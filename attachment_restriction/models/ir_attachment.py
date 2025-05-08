from odoo import models
from odoo.exceptions import AccessError

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def unlink(self):
        if self and \
        not self.env.user.has_group('attachment_restriction.group_unlink_attachment'):
            raise AccessError("You are not allowed to delete attachments.\nContact your administrator to request access if necessary.")
        return super(IrAttachment, self).unlink()