# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import time
from datetime import datetime
from datetime import time as datetime_time
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError


class hr_loan(models.Model):
    _inherit = 'hr.loan'

    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    journal_id = fields.Many2one('account.journal', 'Loan Journal', readonly=True, required=True,
                                 states={'new': [('readonly', False)]},
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1))
    payment_id = fields.Many2one('account.journal', string='Payment From', required=True,
                                 domain=[('type', 'in', ('bank', 'cash'))], readonly=True,
                                 states={'new': [('readonly', False)]})
    account_id = fields.Many2one('account.account', string='Account', required=True, readonly=True,
                                 states={'new': [('readonly', False)]})

    def action_confirm(self):
        for rec in self:

            if rec.state != 'new':
                raise UserError(_("Only an new loan can be confirm."))

            move = rec._create_payment_entry(rec.amount)

            rec.write({'state': 'open', 'move_id': move.id})
        return True

    def _create_payment_entry(self, amount):
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)

        # debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.date)._compute_amount_fields(amount, self.company_id.currency_id, self.company_id.currency_id)
        amount_currency = amount
        balance = self.company_id.currency_id._convert(amount, self.company_id.currency_id, self.company_id.id,
                                                       self.move_id.date or fields.Date.context_today(
                                                           self.company_id.currency_id))

        # debit = balance if balance > 0.0 else 0.0
        # credit = -balance if balance < 0.0 else 0.0


        move = self.env['account.move'].create(self._get_move_vals())

        # Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(balance, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(False))
        counterpart_aml_dict.update({'currency_id': self.company_id.currency_id.id})
        print('counterpart_aml_dict=', counterpart_aml_dict)
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        # Write counterpart lines
        if not self.company_id.currency_id.is_zero(self.amount):
            # debit = balance < 0.0 and -balance or 0.0
            # credit = balance > 0.0 and balance or 0.0
            amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals1(balance, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            print('liquidity_aml_dict=', liquidity_aml_dict)
            aml_obj.create(liquidity_aml_dict)

        # validate the payment
        move.post()

        return move

    def _get_shared_move_line_vals(self, balance, amount_currency, move_id, invoice_id=False):
        return {
            'partner_id': self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
            'move_id': move_id,
            'debit': balance > 0.0 and balance or 0.0,
            'credit': balance < 0.0 and -balance or 0.0,
            'amount_currency': False,
            'payment_id': False,
        }

    def _get_shared_move_line_vals1(self, balance, amount_currency, move_id, invoice_id=False):
        return {
            'partner_id': self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
            'move_id': move_id,
            'debit': balance < 0.0 and -balance or 0.0,
            'credit': balance > 0.0 and balance or 0.0,
            'amount_currency': False,
            'payment_id': False,
        }



    def _get_move_vals(self, journal=None):
        journal = journal or self.journal_id
        """
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
        """
        name = self.move_id.name
        return {
            'name': name,
            'date': self.date,
            'ref': self.name or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
        }

    def _get_liquidity_move_line_vals(self, amount):
        name = self.name
        vals = {
            'name': name,
            'account_id': self.journal_id.outbound_payment_method_line_ids[0].payment_account_id.id ,
            'partner_id': self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
            'journal_id': self.journal_id.id,
            'currency_id': False,
        }

        return vals

    def _get_counterpart_move_line_vals(self, invoice=False):
        name = self.name
        return {
            'name': name,
            'account_id': self.account_id.id,
            'journal_id': self.journal_id.id,
            'partner_id': self.employee_id.address_home_id and self.employee_id.address_home_id.id or False,
            'currency_id': False,
        }

    def unlink(self):
        if any(bool(rec.move_id) for rec in self):
            raise UserError(_("You can not delete a loan that is already running"))
        if any(rec.state in ('open', 'paid') for rec in self):
            raise UserError(_('It is not allowed to delete a loan that already confirmed.'))
        return super(hr_loan, self).unlink()
