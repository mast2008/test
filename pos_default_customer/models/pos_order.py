# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class PosOrder(models.Model):
    _inherit = "pos.order"


    """def _generate_pos_order_invoice(self):
        if self.session_id.config_id.restrict_inv_creation:
            return False
        else:
            return super(PosOrder, self)._generate_pos_order_invoice()"""


    