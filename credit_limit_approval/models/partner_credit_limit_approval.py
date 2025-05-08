from odoo import models, fields
from odoo.exceptions import UserError

class PartnerCreditLimitExemption(models.Model):
    _name = 'ptnr.cl.exempt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'partner_id'
    _description = 'Credit Limit Exemption'

    partner_id = fields.Many2one('res.partner', required=True, tracking=True)
    date_requested = fields.Datetime(required=True, default=fields.Datetime.now(), copy=False, readonly=True)
    date_decision = fields.Datetime(readonly=True, copy=False, tracking=True, string="Approved / Rejected Date")
    state = fields.Selection([('to_approve', 'To Approve'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected')], store=True, copy=False, default='to_approve',
                             tracking=True, required=True, string="Status")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company, required=True, copy=False)
    sale_order_id = fields.Many2one('sale.order', string="Sales Order", copy=False)

    def check_operation_permission(self):
        for rec in self:
            company = rec.company_id
            if not company.cl_approval:
                raise UserError("Please enable settings first.\n\nSales -> Configuration -> Settings -> Credit Limit Exemption Approval")
            approval_users = company.cl_approval_user_ids
            if not approval_users:
                raise UserError("Please set approval users.\n\nSales -> Configuration -> Settings -> Credit Limit Exemption Approval")
            if self.env.user.id not in approval_users.ids:
                appvl_users = ", ".join(approval_users.mapped('name'))
                raise UserError(f"Only following users can do this operation.\n\n{appvl_users}")

    def action_approve(self):
        self.check_operation_permission()
        to_do = self.filtered(lambda r: r.state == 'to_approve')
        for rec in to_do:
            partner = rec.partner_id.with_company(rec.company_id)
            rec.date_decision = fields.Datetime.now()
            rec.activity_feedback(['credit_limit_approval.mail_act_ptnr_cl_exempt_approval'], user_id=self.env.user.id)
            if not partner.date_cl_exempt_apvl or \
            rec.date_decision > partner.date_cl_exempt_apvl:
                partner.date_cl_exempt_apvl = rec.date_decision
            rec.state = 'approved'
            if rec.sale_order_id:
                rec.sale_order_id.message_post(body="Credit Limit Exemption Approved")
                if rec.sale_order_id.user_id:
                    rec.sale_order_id.activity_schedule('mail.mail_activity_data_todo',
                                                            note=f'',
                                                            user_id=rec.sale_order_id.user_id.id,
                                                            date_deadline=fields.Datetime.now().date())

    def action_reject(self):
        self.check_operation_permission()
        to_do = self.filtered(lambda r: r.state != 'rejected')
        for rec in self:
            partner = rec.partner_id.with_company(rec.company_id)
            if rec.date_decision and \
            rec.state == 'approved' and \
            partner.date_cl_exempt_apvl == rec.date_decision:
                partner.date_cl_exempt_apvl = False
            rec.activity_unlink(['credit_limit_approval.mail_act_ptnr_cl_exempt_approval'])
            if rec.sale_order_id:
                rec.sale_order_id.message_post(body="Credit Limit Exemption Rejected")
                if rec.sale_order_id.user_id:
                    rec.sale_order_id.activity_schedule('mail.mail_activity_data_todo',
                                                            note=f'',
                                                            user_id=rec.sale_order_id.user_id.id,
                                                            date_deadline=fields.Datetime.now().date())
        to_do.write({'state': 'rejected', 'date_decision': fields.Datetime.now()})

    def action_set_to_to_approve(self):
        self.check_operation_permission()
        to_do = self.filtered(lambda r: r.state == 'rejected')
        to_do.write({'state': 'to_approve', 'date_decision': False})

    def unlink(self, force=False):
        if not force:
            self.check_operation_permission()
            for rec in self:
                if rec.state != 'to_approve':
                    raise UserError("Only allowed to delete records in 'To Approve' state.")
        return super().unlink()