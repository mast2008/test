# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class AccountPayment(models.Model):
    _inherit = "account.payment"

    paid_name = fields.Char(string="Paid to")

    def do_print_checks(self):
        self.write({'is_move_sent': True})
        return self.env.ref('bahrain_check.action_report_check').report_action(self)

    @api.onchange('partner_id')
    def paid_partner(self):
        self.paid_name = self.partner_id.name