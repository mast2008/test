# -*- coding: utf-8 -*-

from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    loan_ids = fields.One2many('hr.loan', 'employee_id', string='Loans')
    loans_count = fields.Integer(compute='_compute_loans_count', string='Loan')

    def _compute_loans_count(self):
        loan_data = self.env['hr.loan'].sudo().read_group([('employee_id', 'in', self.ids)], ['employee_id'], ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in loan_data)
        for employee in self:
            employee.loans_count = result.get(employee.id, 0)

class hr_employee_public(models.Model):
    _inherit = 'hr.employee.public'

    loan_ids = fields.One2many('hr.loan', 'employee_id', string='Lines')
    loans_count = fields.Integer(compute='_compute_loans_count', string='Loans')

    def _compute_loans_count(self):
        loan_data = self.env['hr.loan'].sudo().read_group([('employee_id', 'in', self.ids)], ['employee_id'], ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in loan_data)
        for employee in self:
            employee.loans_count = result.get(employee.id, 0)

class hr_loan(models.Model):
    _name = 'hr.loan'
    _description = 'Employees Loan'
    _inherit = 'mail.thread'

    @api.depends('loan_ids.amount', 'amount')
    def _balance(self):
        for line in self:
            if line.state == 'new':
                continue
            amount = 0
            for lines in line.loan_ids:
                amount =  lines.amount + amount
            line.paid = amount or 0.0
            line.balance = line.amount - line.paid or 0.0
            if line.balance<=0 and line.state=='open':
                line.state = 'paid'
    name = fields.Char(string='Description', readonly=True, tracking=True, states={'new': [('readonly', False)]}, required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, tracking=True, states={'new': [('readonly', False)]}, required=True)
    date = fields.Date(string='Date', default=str(datetime.today()), readonly=True, tracking=True, copy=False, states={'new': [('readonly', False)]}, required=True)
    amount = fields.Float(string='Amount', digits='Payroll', readonly=True, tracking=True, copy=False, states={'new': [('readonly', False)]}, required=True)
    paid = fields.Float(compute='_balance', string='Paid', digits='Payroll', readonly=True, copy=False, store=True)
    balance = fields.Float(compute='_balance', string='Amount Due', digits='Payroll', readonly=True, copy=False, store=True)
    state = fields.Selection([('new', 'New'), ('open', 'Running'), ('paid', 'Paid'), ('reject', 'Rejected'), ('cancel','Cancelled')], string='State', default='new', readonly=True, tracking=True, copy=False)
    installment = fields.Float(string='Installment', digits='Payroll', readonly=True, tracking=True, copy=False, states={'new': [('readonly', False)]}, required=True)
    company_id = fields.Many2one('res.company', related='employee_id.company_id', string='Company', readonly=True)
    loan_ids = fields.One2many('hr.loan.lines', 'loan_id', 'Lines', readonly=True, copy=False)

    def action_reject(self):
        for rec in self:

            if rec.state != 'new':
                raise UserError(_("Only an new loan can be reject."))
            rec.write({'state': 'reject'})
        return True

    def action_draft(self):
        for rec in self:
            if rec.state not in ('reject', 'cancel'):
                raise UserError(_("Only a cancel or reject loan can be set to new."))
            rec.write({'state': 'new'})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state != 'new':
                raise UserError(_("Only an new loan can be cancel."))
            rec.write({'state': 'cancel'})
        return True

    def action_confirm(self):
        for rec in self:
            if rec.state != 'new':
                raise UserError(_("Only an new loan can be confirm."))

            rec.write({'state': 'open'})
        return True

    def unlink(self):
        if any(bool(rec.move_id) for rec in self):
            raise UserError(_("You can not delete a loan that is already running"))
        if any(rec.state in ('open','paid') for rec in self):
            raise UserError(_('It is not allowed to delete a loan that already confirmed.'))
        return super(hr_loan, self).unlink()

class hr_loan_lines(models.Model):
    _name = 'hr.loan.lines'
    _description = 'Employees Loan Lines'

    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    date = fields.Date(string='Date')
    amount = fields.Float(string='Amount', digits='Payroll')
    loan_id = fields.Many2one('hr.loan', 'Loan')

class hr_payslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        for payslip in self:
            amount = 0
            for line in payslip.line_ids:
                if line.code == 'LO':
                    amount += line.amount
            #print("line", line)
        loans = self.env['hr.loan'].search([('employee_id','=',self.employee_id.id), ('installment','>',0), ('balance','>',0), ('state','=','open')])
        #print('loans', loans)
        for loan in loans:
            #print('loan', loan)
            if loan.installment>=(amount*-1):
                if loan.balance>=loan.installment:
                    loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount':amount*-1})]
                    amount = 0
                elif loan.balance<loan.installment and loan.balance>=(amount*-1):
                    loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount':amount*-1})]
                    amount = 0
                else:
                    amount += loan.balance
                    loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount':loan.balance})]
            elif loan.installment<(amount*-1):
                if loan.balance<=loan.installment:
                    loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount':loan.balance})]
                    amount += loan.balance
                elif loan.balance>loan.installment:
                    loan.loan_ids = [(0, 0, {'payslip_id': self.id, 'date': self.date_to, 'amount':loan.installment})]
                    amount += loan.installment
        return super(hr_payslip, self).action_payslip_done()

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        res = super(hr_payslip, self).get_inputs(contracts, date_from, date_to)
        loans = self.env['hr.loan'].search([('employee_id','=',self.employee_id.id), ('installment','>',0), ('balance','>',0), ('state','=','open')])
        #print("loans", loans)
        loan = 0
        for l in loans:
            loan += l.installment
        res += [{'name': 'Loan', 'code': 'Loan', 'contract_id': contracts.id, 'amount':loan*-1}]
        return res

class hr_payslip_input(models.Model):
    _inherit = 'hr.payslip.input'

    amount = fields.Float(help="It is used in computation. For e.g. A rule for sales having "
                               "1% commission of basic salary for per product can defined in expression "
                               "like result = inputs.SALEURO.amount * contract.wage*0.01.", digits='Payroll')

