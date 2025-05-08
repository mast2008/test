# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
import pytz
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import calendar
import logging
from odoo.tools.misc import formatLang, format_date, parse_date
import xlsxwriter

_logger = logging.getLogger(__name__)


class AgeingReportXls(models.AbstractModel):
    _name = 'report.age_receivable_ext.xlsx_age_receivable'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        count = 10
        sheet = workbook.add_worksheet('Aged Receivable')
        merge_format = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter'})
        merge_format1 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter'})
        content_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'num_format': '0.000',
            'valign': 'vcenter'})
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')

        sheet.merge_range('A1:Q1', self.env.user.company_id.name, merge_format)
        sheet.merge_range('A2:Q2', 'Building'+ str(self.env.user.company_id.street_number)+',Road/Street '+str(self.env.user.company_id.street_name)+
        ', Block ' + str(self.env.user.company_id.street2), merge_format1)
        sheet.merge_range('A3:Q3','P.O. Box '+ str(self.env.user.company_id.zip)+',CR '+str(self.env.user.company_id.vat)+
                          ', '+ str(self.env.user.company_id.city)+ ', '+ str(self.env.user.company_id.country_id.name), merge_format1)
        sheet.merge_range('A5:Q5', 'Summary of Account Receivable as on' + ' ' + str(date.today()), merge_format)



        sheet.merge_range(5, 0, 6, 0, 'Customer Name', merge_format)
        sheet.merge_range(5, 1, 6, 1, 'Sale man', merge_format)
        sheet.merge_range(5, 2, 6, 2, 'Credit Days', merge_format)
        sheet.merge_range(5, 3, 6, 3, 'Credit Limit', merge_format)
        sheet.merge_range(5, 4, 6, 4, 'Opening Balance', merge_format)
        sheet.merge_range(5, 5, 6, 6, 'Last Payment', merge_format)
        sheet.merge_range(5, 7, 6, 7, 'Due amount as per limit', merge_format)
        sheet.merge_range(5, 8, 6, 8, 'Collection amount', merge_format)
        sheet.merge_range(5, 9, 6, 9, '0-' + str(data['form']['days']), merge_format)
        sheet.merge_range(5, 10, 6, 10, str(int(data['form']['days']) + 1) + '-' + str(int(data['form']['days'])*2), merge_format)
        sheet.merge_range(5, 11, 6, 11, str(int(data['form']['days'])*2 + 1) + '-' + str(int(data['form']['days'])*3), merge_format)
        sheet.merge_range(5, 12, 6, 12, str(int(data['form']['days'])*3 + 1) + '-' + str(int(data['form']['days'])*4), merge_format)
        sheet.merge_range(5, 13, 6, 13, str(int(data['form']['days'])*4 + 1) + '-' + str(int(data['form']['days'])*5), merge_format)
        sheet.merge_range(5, 14, 6, 14, str(int(data['form']['days']) * 5 + 1) + '-' + str(int(data['form']['days']) * 6), merge_format)
        sheet.merge_range(5, 15, 6, 15, str(int(data['form']['days'])*6) + '+', merge_format)
        sheet.merge_range(5, 16, 6, 16, 'Closing balance', merge_format)
        sheet.write(6, 5, 'Date', merge_format)
        sheet.write(6, 6, 'Amount', merge_format)
        row = 7
        days = int(data['form']['days'])
        startday = datetime.strptime(data['form']['date_from'], DEFAULT_SERVER_DATE_FORMAT).date()
        endday = datetime.strptime(data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT).date()
        print("Ddd",startday,endday)
        if(data['form']['receivable']==True and data['form']['payable']==True):
            query = """
            SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, partner.name as partner_name, partner.id as partner_id, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
            LEFT JOIN res_partner partner ON ("account_move_line".partner_id = partner.id)
            LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
            LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
            LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
            LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
			where %s<="account_move_line".date<=%s and move.state='posted' and account.user_type_id in (1,2) and "account_move_line".partner_id is not NULL
			ORDER BY partner_name ASC, "account_move_line".date DESC"""
        elif(data['form']['receivable']==True):
            query0 = """
                        SELECT DISTINCT "account_move_line".partner_id,partner.name as partner_name FROM "account_move_line"
                        LEFT JOIN res_partner partner ON ("account_move_line".partner_id = partner.id)
                        LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
                        LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
                        LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
                        LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
            			where "account_move_line".date>=%s and "account_move_line".date<=%s and move.state='posted' and account.user_type_id = 1 and "account_move_line".partner_id is not NULL
            			ORDER BY partner_name"""

            query = """
            SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, partner.name as partner_name, partner.id as partner_id, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
            LEFT JOIN res_partner partner ON ("account_move_line".partner_id = partner.id)
            LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
            LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
            LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
            LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
			where "account_move_line".date>=%s and "account_move_line".date<=%s and move.state='posted' and account.user_type_id = 1 and "account_move_line".partner_id is not NULL
			ORDER BY partner_name ASC, "account_move_line".date DESC"""

            query1 = """
                        SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, partner.name as partner_name, partner.id as partner_id, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
                        LEFT JOIN res_partner partner ON ("account_move_line".partner_id = partner.id)
                        LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
                        LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
                        LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
                        LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
            			where "account_move_line".date<%s and move.state='posted' and account.user_type_id = 1 and "account_move_line".partner_id is not NULL
            			ORDER BY partner_name ASC, "account_move_line".date DESC"""
            query2 = """
                                    SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, partner.name as partner_name, partner.id as partner_id, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
                                    LEFT JOIN res_partner partner ON ("account_move_line".partner_id = partner.id)
                                    LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
                                    LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
                                    LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
                                    LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
                        			where "account_move_line".date_maturity>%s and move.state='posted' and account.user_type_id = 1 and "account_move_line".partner_id is not NULL
                        			ORDER BY partner_name ASC, "account_move_line".date DESC"""
        elif(data['form']['payable']==True):
            query = """
            SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, partner.name as partner_name, partner.id as partner_id, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
            LEFT JOIN res_partner partner ON ("account_move_line".partner_id = partner.id)
            LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
            LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
            LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
            LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
			where %s<="account_move_line".date<=%s and move.state='posted' and account.user_type_id = 2 and "account_move_line".partner_id is not NULL
			ORDER BY partner_name ASC, "account_move_line".date DESC"""
        self.env.cr.execute(query0, [startday, endday])
        partners = self.env.cr.dictfetchall()
        print("partners", partners)
        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        print("partner_ids==", partner_ids)
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        print("lines==", lines)
        if not partner_ids:
            partner_ids = [0, -1]


        self.env.cr.execute(query, [endday, endday, startday, endday])
        sql = self.env.cr.dictfetchall()
        print("sql===", sql)

        moves = sorted(sql, key=lambda k: k['partner_id'])
        print("moves===", moves)


        if not moves:
            return []
        #opening balance
        self.env.cr.execute(query1, [endday, endday, startday])
        sql1 = self.env.cr.dictfetchall()
        print("sql1===", sql1)
        moves11 = sorted(sql1, key=lambda k: k['partner_id'])
        print("moves11===", moves11)
        #due amount
        self.env.cr.execute(query2, [endday, endday, endday])
        sql2 = self.env.cr.dictfetchall()
        print("sql2===", sql2)
        moves22 = sorted(sql2, key=lambda k: k['partner_id'])
        print("moves22===", moves22)


        result = {}
        t_closing_balance = 0
        t_opening_balance = 0
        t_last_payment = 0
        t_collection_amount = 0
        t_not_due = 0
        t_days30 = 0
        t_days60 = 0
        t_days90 = 0
        t_days180 = 0
        t_days360 = 0
        t_days720 = 0
        t_days721 = 0
        for partner in partner_ids:
            closing_balance = 0
            opening_balance = 0
            collection_amount = 0
            not_due = 0
            days30 = 0
            days60 = 0
            days90 = 0
            days180 = 0
            days360 = 0
            days720 = 0
            days721 = 0

            if partner not in result:
                customer = self.env['res.partner'].search([('id', '=', partner)])
                payment = self.env['account.payment'].search([('partner_id', '=', partner),('payment_type', '=', 'inbound'),
                                                              ('state', '=', 'posted'),
                                                              ('date','>=',startday), ('date','<=',endday)],
                                                            order='date desc', limit=1)
                payments = self.env['account.payment'].search(
                    [('partner_id', '=', partner), ('payment_type', '=', 'inbound'),
                     ('state', '=', 'posted'),
                     ('date', '>=', startday), ('date', '<=', endday)])
                if payments:
                    for pay in payments:
                        collection_amount += pay.amount
                result[partner] = {
                    'customer_name': customer.name,
                    'sale_man': customer.user_id.name,
                    'credit_days': customer.credit_days,
                    'credit_limit': customer.credit_limit,
                    'opening_balance': opening_balance,
                    'last_payment': payment.amount,
                    'last_payment_date': payment.date,
                    'collection_amount': collection_amount,
                    'not_due': not_due,
                    'days30': days30,
                    'days60': days60,
                    'days90': days90,
                    'days180': days180,
                    'days360': days360,
                    'days720': days720,
                    'days721': days721,
                    'closing_balance': closing_balance,
                }
                print("day30", (endday - timedelta(days=days)))

            for move in moves:
                result[partner]['closing_balance'] = 0
                if move['partner_id'] == partner:

                    credits = move['credits'] or 0
                    debits = move['debits'] or 0
                    debit = move['debit'] or 0
                    credit = move['credit'] or 0
                    total = debit + debits - credit - credits
                    '''
                    if move['date'] >= endday:
                        result[partner]['not_due'] += total
                    '''
                    if move['date'] >= (endday - timedelta(days=days)):
                        result[partner]['days30'] += total
                    elif move['date'] >= (endday - timedelta(days=days * 2)):
                        result[partner]['days60'] += total
                    elif move['date'] >= (endday - timedelta(days=days * 3)):
                        result[partner]['days90'] += total
                    elif move['date'] >= (endday - timedelta(days=days * 4)):
                        result[partner]['days180'] += total
                    elif move['date'] >= (endday - timedelta(days=days * 5)):
                        result[partner]['days360'] += total
                    elif move['date'] >= (endday - timedelta(days=days * 6)):
                        result[partner]['days720'] += total
                    else:
                        result[partner]['days721'] += total
                result[partner]['closing_balance'] += result[partner]['days30'] + result[partner]['days60'] + \
                                                      result[partner]['days90'] + result[partner]['days180'] + result[partner]['days360'] +\
                                                      result[partner]['days720'] + result[partner]['days721']

             #open balance
            for move1 in moves11:

                if move1['partner_id'] == partner:

                    credits = move1['credits'] or 0
                    debits = move1['debits'] or 0
                    debit = move1['debit'] or 0
                    credit = move1['credit'] or 0
                    total1 = debit + debits - credit - credits
                    result[partner]['opening_balance'] += total1

            # Due Amount
            for move2 in moves22:

                if move2['partner_id'] == partner:
                    credits = move2['credits'] or 0
                    debits = move2['debits'] or 0
                    debit = move2['debit'] or 0
                    credit = move2['credit'] or 0
                    total2 = debit  - credit
                    result[partner]['not_due'] += total2

        print("result", result)

        for val in result:
            
            sheet.write(row, 0, result[val]['customer_name'], content_format)
            if result[val]['sale_man'] != False:
                sheet.write(row, 1, result[val]['sale_man'], content_format)
            else:
                sheet.write(row, 1, '', content_format)
            if result[val]['last_payment_date']!= False:
                sheet.write(row, 5, str(result[val]['last_payment_date']), content_format)
            else:
                sheet.write(row, 5, '', content_format)
            sheet.write(row, 2, result[val]['credit_days'], content_format)
            sheet.write(row, 3, result[val]['credit_limit'], content_format)
            sheet.write(row, 4, result[val]['opening_balance'], content_format)
            # sheet.write(row, 5, str(result[val]['last_payment_date']), content_format)
            sheet.write(row, 6, result[val]['last_payment'], content_format)
            sheet.write(row, 7, result[val]['not_due'], content_format)
            sheet.write(row, 8, result[val]['collection_amount'], content_format)
            sheet.write(row, 9, result[val]['days30'], content_format)
            sheet.write(row, 10, result[val]['days60'], content_format)
            sheet.write(row, 11, result[val]['days90'], content_format)
            sheet.write(row, 12, result[val]['days180'], content_format)
            sheet.write(row, 13, result[val]['days360'], content_format)
            sheet.write(row, 14, result[val]['days720'], content_format)
            sheet.write(row, 15, result[val]['days721'], content_format)
            sheet.write(row, 16, result[val]['closing_balance'], content_format)

            row = row + 1
            t_opening_balance += result[val]['opening_balance']
            t_last_payment += result[val]['last_payment']
            t_not_due += result[val]['not_due']
            t_collection_amount += result[val]['collection_amount']
            t_days30 += result[val]['days30']
            t_days60 +=result[val]['days60']
            t_days90 += result[val]['days90']
            t_days180 += result[val]['days180']
            t_days360 += result[val]['days360']
            t_days720 += result[val]['days720']
            t_days721 += result[val]['days721']
            t_closing_balance += result[val]['closing_balance']

        sheet.write(row, 0, 'Total', content_format)
        sheet.write(row, 1, '', content_format)
        sheet.write(row, 2, ' ', content_format)
        sheet.write(row, 3, ' ', content_format)
        sheet.write(row, 4, t_opening_balance, content_format)
        sheet.write(row, 5, ' ', content_format)
        sheet.write(row, 6, t_last_payment, content_format)
        sheet.write(row, 7, t_not_due, content_format)
        sheet.write(row, 8, t_collection_amount, content_format)
        sheet.write(row, 9, t_days30, content_format)
        sheet.write(row, 10, t_days60, content_format)
        sheet.write(row, 11, t_days90, content_format)
        sheet.write(row, 12, t_days180, content_format)
        sheet.write(row, 13, t_days360, content_format)
        sheet.write(row, 14, t_days720, content_format)
        sheet.write(row, 15, t_days721, content_format)
        sheet.write(row, 16, t_closing_balance, content_format)




