# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfigInherit(models.Model):
    _inherit = 'pos.config'

    default_partner_id = fields.Many2one('res.partner', string="Select Customer")
    restrict_inv_download = fields.Boolean(string="Restrict Invoice Download",
                                           help="This allows auto download invoice as optional from pos setting")
    restrict_auto_inv_creation = fields.Boolean(string="Restrict auto Invoice",
                                           help="It optionally controls automatic invoice generation from the POS setting.")
