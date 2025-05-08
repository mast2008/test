from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cl_approval = fields.Boolean("Credit Limit Exemption Approval", help="Allow to confirm sales until certain hours by getting approval from manager even if credit limit exceeded", readonly=False,
                                 related='company_id.cl_approval')
    cl_approval_user_ids = fields.Many2many('res.users', related='company_id.cl_approval_user_ids', readonly=False, string="Users to approve credit limit exemption")
    cl_approval_validity_hour = fields.Integer("Approval Validity (Hour)",help="Can confirm sales until this hour from approval date", related='company_id.cl_approval_validity_hour', readonly=False)