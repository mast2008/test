# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    over_credit = fields.Boolean('Allow Over Credit?')
    #credit_perday = fields.Float('Credit per day')
    credit_days = fields.Integer('Credit Days')
