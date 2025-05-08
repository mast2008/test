# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from datetime import datetime
from odoo import api, fields, models


class Currency(models.Model):
    _inherit = "res.currency"

    # Note: 'code' column was removed as of v6.0, the 'name' should now hold the ISO code.
    name = fields.Char(string='Currency', size=3, required=True, help="Currency Code (ISO 4217)", translate=True)
    symbol = fields.Char(help="Currency sign, to be used when printing amounts.", required=True, translate=True)
    currency_unit_label = fields.Char(string="Currency Unit", help="Currency Unit Name", translate=True)
    currency_subunit_label = fields.Char(string="Currency Subunit", help="Currency Subunit Name", translate=True)

class hr_holidays(models.Model):
    _inherit = "hr.leave.allocation"

    def create_annual(self):
        contracts = self.env['hr.contract'].search([('state','in',['open','pending'])])
        for contract in contracts:
            annual = contract.holidays
            monthly = annual/12
            total_days = (datetime.utcnow().date() - contract.date_start).days
            diff = annual/365.25
            totals = diff*total_days
            allocations = self.search([('state','=','validate'),('employee_id','=',contract.employee_id.id), ('holiday_status_id','=',1)])
            allocation_days = 0
            for allocation in allocations:
                allocation_days += allocation.number_of_days
            total = int(totals - allocation_days)
            if total>0:
                self.create({'name':'Auto Create Leaves', 'state':'validate', 'employee_id':contract.employee_id.id, 'holiday_status_id':1, 'number_of_days':total})

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        if self.date_from and self.date_to:
            self.number_of_days = (self.date_to - self.date_from).days + 1
        else:
            self.number_of_days = 0

class hr_contract(models.Model):
    _inherit = 'hr.contract'

    holidays = fields.Float(string='Legal Leaves', help="Number of days of paid leaves the employee gets per year.", tracking=True)
    mobile = fields.Monetary(string="Mobile Allowance", tracking=True, help="The employee mobile subscription will be paid up to this amount.")
    transport = fields.Monetary(string="Transport Allowance", tracking=True, help="The employee transport subscription will be paid up to this amount.")
    house = fields.Monetary(string="House Allowance", tracking=True, help="The employee house subscription will be paid up to this amount.")
    food = fields.Monetary(string="Food Allowance", tracking=True, help="The employee food subscription will be paid up to this amount.")
    other_allowances = fields.Monetary(string="Other Allowances", tracking=True)
    airticket = fields.Monetary(string="Airticket Allowance", tracking=True, help="The employee Air Ticket allowanace will be paid up to this amount.")
    indemnity = fields.Boolean(string="Indemnity", tracking=True, help="The employee End of Service.")
    gosi_employee = fields.Float(string="Gosi Employee", tracking=True, help="The employee insurance subscription will be paid up to this amount.")
    gosi_company = fields.Float(string="Gosi Company", tracking=True, help="The employee insurance subscription will be paid up to this amount.")
    lmra = fields.Monetary(string="LMRA", tracking=True, help="The employee LMRA subscription will be paid up to this amount.")

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    disabled = fields.Boolean(string="Disabled", help="If the employee is declared disabled by law", groups="hr.group_hr_user")
    disabled_spouse_bool = fields.Boolean(string='Disabled Spouse', help='if recipient spouse is declared disabled by law', groups="hr.group_hr_user")
    disabled_children_bool = fields.Boolean(string='Disabled Children', help='if recipient children is/are declared disabled by law', groups="hr.group_hr_user")
    disabled_children_number = fields.Integer('Number of disabled children', groups="hr.group_hr_user")
    dependent_children = fields.Integer(compute='_compute_dependent_children', string='Considered number of dependent children', groups="hr.group_hr_user")
    other_dependent_people = fields.Boolean(string="Other Dependent People", help="If other people are dependent on the employee", groups="hr.group_hr_user")
    other_senior_dependent = fields.Integer('# seniors (>=65)', help="Number of seniors dependent on the employee, including the disabled ones", groups="hr.group_hr_user")
    other_disabled_senior_dependent = fields.Integer('# disabled seniors (>=65)', groups="hr.group_hr_user")
    other_juniors_dependent = fields.Integer('# people (<65)', help="Number of juniors dependent on the employee, including the disabled ones", groups="hr.group_hr_user")
    other_disabled_juniors_dependent = fields.Integer('# disabled people (<65)', groups="hr.group_hr_user")
    dependent_seniors = fields.Integer(compute='_compute_dependent_people', string="Considered number of dependent seniors", groups="hr.group_hr_user")
    dependent_juniors = fields.Integer(compute='_compute_dependent_people', string="Considered number of dependent juniors", groups="hr.group_hr_user")

    @api.onchange('disabled_children_bool')
    def _onchange_disabled_children_bool(self):
        self.disabled_children_number = 0

    @api.onchange('other_dependent_people')
    def _onchange_other_dependent_people(self):
        self.other_senior_dependent = 0.0
        self.other_disabled_senior_dependent = 0.0
        self.other_juniors_dependent = 0.0
        self.other_disabled_juniors_dependent = 0.0

    @api.depends('disabled_children_bool', 'disabled_children_number', 'children')
    def _compute_dependent_children(self):
        for employee in self:
            if employee.disabled_children_bool:
                employee.dependent_children = employee.children + employee.disabled_children_number
            else:
                employee.dependent_children = employee.children

    @api.depends('other_dependent_people', 'other_senior_dependent',
        'other_disabled_senior_dependent', 'other_juniors_dependent', 'other_disabled_juniors_dependent')
    def _compute_dependent_people(self):
        for employee in self:
            employee.dependent_seniors = employee.other_senior_dependent + employee.other_disabled_senior_dependent
            employee.dependent_juniors = employee.other_juniors_dependent + employee.other_disabled_juniors_dependent
