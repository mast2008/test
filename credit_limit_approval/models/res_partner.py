from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_cl_exempt_apvl = fields.Datetime(company_dependent=True, string="Last Date Credit Limit Exemption Approval")




