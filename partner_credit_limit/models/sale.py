# See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
#from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DFT
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def check_limit(self):
        print("check_limit000")
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        moveline_obj = self.env['account.move.line']
        movelines = moveline_obj.sudo().search(
            [('partner_id', '=', partner.id),
             ('account_id.user_type_id.name', 'in', ['Receivable', 'Payable']),
             ('full_reconcile_id', '=', False), ('move_id.state', '=', 'posted')]
        )
        debit, credit = 0.0, 0.0
        today_dt = datetime.strftime(datetime.now().date(), DF)
        flag = False
        credit_days = partner.credit_days
        invoices = []
        for line in movelines:
            date_maturity = line.date_maturity if line.date_maturity else line.date
            if datetime.strftime(date_maturity, DF) <= today_dt:
                credit += line.debit
                debit += line.credit
            invoice = self.env['account.move'].search([('move_type', 'in', ['out_invoice', 'out_refund']),('id', '=', line.move_id.id)], limit=1)
            if invoice and partner.credit_days and invoice.move_type == 'out_invoice' and line.parent_state == 'posted':
                last_dt = datetime.strftime(datetime.now().date() - relativedelta(days=credit_days), DF)
                if invoice.payment_state != 'paid' and datetime.strftime(invoice.invoice_date, DF) <= last_dt:
                    flag = True
                    invoices.append(invoice.name)

        #print("bbbbbbbbb",credit,debit,self.amount_total,partner.credit_limit)
        if (credit - debit + self.amount_total) > partner.credit_limit:
            if not partner.over_credit:
                msg = 'Can not confirm Sale Order,Total mature due Amount ' \
                      '%s as on %s !\nCheck Partner Accounts or Credit ' \
                      'Limits !' % (credit - debit, today_dt)
                raise UserError(_('Credit Over Limits !\n' + msg))
        if flag == True:
            if not partner.over_credit:
                msg = 'Sales order cannot be confirmed, partner has invoices not paid ' \
                      'before %s days  !\nCheck Unpaid Invoices' % (credit_days)

                raise UserError(_('Credit Over Limits !\n' + msg + '\n' + ','.join(invoices)))
        return True

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.check_limit()
        return res


