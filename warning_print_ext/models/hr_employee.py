# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class HRWarning(models.Model):
    _inherit = 'hr.warning'

    w_type = fields.Selection([
        ('verbal', 'Verbal Counseling Session'),
        ('fir_w', '1st Written Warning'),
        ('sec_w', '2nd Written Warning'),
        ('final', 'Final'),
        ('dismissal', 'Dismissal'),
        ('suspension', 'Suspension Pending Investigation'),
    ], string='Warning')

    date = fields.Datetime(string='Date', default=datetime.now(), readonly=True, track_visibility='onchange',
                       copy=False, required=True)

    desc = fields.Text(string='Description of Incident', readonly=True)
    steps = fields.Text(string='Steps for Improvement', readonly=True)
    step_not_imp = fields.Text(string='Steps to be taken if Action/Behavior Does Not Improve', readonly=True)
    explanation = fields.Text(string='Explanation of Incident', readonly=True)
    f_date = fields.Date(string='Follow-Up Date')
    refused = fields.Boolean(string='Emp Refused Sign',help="Employee Refused to Sign .")
    refused_date = fields.Date(string='Refused Date')
    hr_date = fields.Date(string='HR/Witness Date')

