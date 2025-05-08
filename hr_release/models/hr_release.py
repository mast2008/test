# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import time
from datetime import datetime
from datetime import time as datetime_time
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class hr_release_compute(models.Model):
    _name = 'hr.release.compute'
    _description = 'Release Computation'
    
    reason_id = fields.Many2one('hr.release.reason', string='Reason')
    name = fields.Char(string='Description', required=True)
    minimum_years = fields.Integer(string='Minimum Years')
    percentage_salary = fields.Float(string='Percentage')
    release_by = fields.Selection([('employee', 'Employee'), ('company', 'Company')], string='Release By', default='employee', required=True)
    

class hr_release_reason(models.Model):
    _name = 'hr.release.reason'
    _description = 'Employees Release Reasons'

    name = fields.Char(string='Name', required=True)
    calculate_ids = fields.One2many('hr.release.compute', 'reason_id', string='Calculation')

class hr_employee(models.Model):
    _inherit = 'hr.employee'
    
    indemnity_amount = fields.Float(string='Indemnity', groups="hr.group_hr_user")

class hr_release(models.Model):
    _name = 'hr.release'
    _description = 'Employees Release'
    _inherit = 'mail.thread'

    name = fields.Char(string='Description', readonly=True, track_visibility='onchange', states={'new': [('readonly', False)]}, required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, track_visibility='onchange', states={'new': [('readonly', False)]}, required=True)
    reason = fields.Many2one('hr.release.reason', string='Reason', readonly=True, track_visibility='onchange', states={'new': [('readonly', False)]}, required=True)
    note = fields.Text(string='Note', readonly=True, states={'new': [('readonly', False)]})
    date = fields.Date(string='Date', default=str(datetime.today()), readonly=True, track_visibility='onchange', copy=False, states={'new': [('readonly', False)]}, required=True)
    effective_date = fields.Date(string='Effective Date', default=str(datetime.today()), readonly=True, track_visibility='onchange', copy=False, states={'new': [('readonly', False)]}, required=True)
    state = fields.Selection([('new', 'New'), ('approve', 'Approved'), ('reject', 'Rejected'), ('cancel','Cancelled')], string='State', default='new', readonly=True, track_visibility='onchange', copy=False)
    company_id = fields.Many2one('res.company', related='employee_id.company_id', string='Company', readonly=True)
    release_by = fields.Selection([('employee', 'Employee'), ('company', 'Company')], string='Release By', default='employee', required=True, readonly=True, track_visibility='onchange', copy=False, states={'new': [('readonly', False)]})
    calculate_id = fields.Many2one('hr.release.compute', string='Calculation')

    def action_reject(self):
        for rec in self:
            if rec.state != 'new':
                raise UserError(_("Only an new release can be reject."))
            rec.write({'state': 'reject'})
        return True

    def action_draft(self):
        for rec in self:
            if rec.state not in ('reject', 'cancel'):
                raise UserError(_("Only a cancel or reject release can be set to new."))
            rec.write({'state': 'new'})
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state != 'new':
                raise UserError(_("Only an new release can be cancel."))
            rec.write({'state': 'cancel'})
        return True

    def action_confirm(self):
        for rec in self:
            if rec.state != 'new':
                raise UserError(_("Only an new release can be confirm."))
            rec.write({'state': 'approve'})
            contracts = self.env['hr.contract'].search([('employee_id','=',rec.employee_id.id),('state','=','open')])
            for contract in contracts:

                if contract.date_end == False or contract.date_end>rec.effective_date:
                    contract.write({'date_end':rec.effective_date})
            if not contract:
                return True
            print('contracts', contracts)
            print('contracts[0]', contracts[0])
            years = (rec.effective_date - contracts[0].date_start).days/365
            print('years', years)
            calculate_id = False
            y = 0
            for record in rec.reason.calculate_ids:
                if record.minimum_years<=years and record.minimum_years>=y and rec.release_by == record.release_by:
                    y = record.minimum_years
                    calculate_id = record
            rec.calculate_id = calculate_id
            rec.employee_id.indemnity_amount = contracts[0].wage*years*rec.calculate_id.percentage_salary/100
        return True

    def unlink(self):
        if any(rec.state in ('approve') for rec in self):
            raise UserError(_('It is not allowed to delete a release that already approved.'))
        return super(hr_release, self).unlink()