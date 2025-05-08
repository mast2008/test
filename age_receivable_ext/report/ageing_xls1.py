# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import pytz
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import calendar
import logging
import xlsxwriter

_logger = logging.getLogger(__name__)


class AgeingReportXls(models.AbstractModel):
    _name = 'report.age_receivable_ext.xlsx_age_receivable'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        count = 10
        sheet = workbook.add_worksheet()
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
        sheet.write(0, 0, 'Customer Name', format21)
        sheet.write(0, 1, 'Sale man', format21)
        sheet.write(0, 2, 'Credit Days', format21)
        sheet.write(0, 3, 'Credit Limit', format21)
        sheet.write(0, 4, 'Opening Balance', format21)
        sheet.write(0, 5, 'Date', format21)
        sheet.write(0, 6, 'Amount', format21)
        sheet.write(0, 7, 'Due amount as per limit', format21)
        sheet.write(0, 8, 'Collection amount', format21)
        sheet.write(0, 9, '0-' + str(data['form']['days']) + ' Days', format21)
        sheet.write(0, 10, str(int(data['form']['days']) + 1) + '-' + str(int(data['form']['days'])*2) , format21)
        sheet.write(0, 11, str(int(data['form']['days'])*2 + 1) + '-' + str(int(data['form']['days'])*3) , format21)
        sheet.write(0, 12, str(int(data['form']['days'])*3 + 1) + '-' + str(int(data['form']['days'])*4) , format21)
        sheet.write(0, 13, str(int(data['form']['days'])*4 + 1) + '-' + str(int(data['form']['days'])*5) , format21)
        sheet.write(0, 14, str(int(data['form']['days']) * 5 + 1) + '-' + str(int(data['form']['days']) * 6) ,format21)
        sheet.write(0, 15, str(int(data['form']['days'])*6) + '+', format21)
        sheet.write(0, 16, 'Closing balance', format21)
        row = 1
        days = int(data['form']['days'])
        outstandings = 0
        openbalances = 0
        not_dues = 0
        days30s = 0
        days60s = 0
        days90s = 0
        days180s = 0
        days360s = 0
        days720s = 0
        days721s = 0
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
            			where "account_move_line".date<=%s and move.state='posted' and account.user_type_id = 1 and "account_move_line".partner_id is not NULL
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
        self.env.cr.execute(query, [endday, endday, startday, endday])
        sql = self.env.cr.dictfetchall()
        self.env.cr.execute(query1, [endday, endday, startday])
        sql1 = self.env.cr.dictfetchall()
        print("sql===", sql)
        print("sql1===", sql1)
        moves = sorted(sql, key=lambda k: k['partner_id'])
        moves1 = sorted(sql1, key=lambda k: k['partner_id'])
        print("moves===", moves)
        if not moves:
            return []
        if not moves1:
            return []
        partner = 0
        count =0
        for move in moves:
            count+=1
            print("len of moves", len(moves), moves[1])
            if partner!=move['partner_id']:
                if partner!=0 and (round(not_duess,3)!=0 or round(days30ss,3)!=0 or round(days60ss,3)!=0 or round(days90ss,3)!=0 or round(days180ss,3)!=0 or round(days360ss,3)!=0 or round(days720ss,3)!=0 or round(days721ss,3)!=0):
                    print("checcck", count)
                    #sheet.merge_range(row, 0, row, 1, "Total1"+ moves[count-1]['partner_name'], font_size_8)
                    # sheet.write(row, 2, str(round(outstandingss,3)), format21)
                    #sheet.write(row, 3, str(round(not_duess,3)), format21
                    print("vv=",moves[count - 2]['partner_id'])
                    customer = self.env['res.partner'].search([('id', '=', moves[count - 2]['partner_id'])])
                    sheet.write(row, 0, moves[count-2]['partner_name'], font_size_8)
                    sheet.write(row, 1, customer.user_id.name, font_size_8)
                    sheet.write(row, 2, customer.user_id.credit_days, font_size_8)
                    sheet.write(row, 3, str(customer.user_id.credit_limit)+" days", font_size_8)
                    sheet.write(row, 9, str(round(days30ss,3)), font_size_8)
                    sheet.write(row, 10, str(round(days60ss,3)), font_size_8)
                    sheet.write(row, 11, str(round(days90ss,3)), font_size_8)
                    sheet.write(row, 12, str(round(days180ss,3)), font_size_8)
                    sheet.write(row, 13, str(round(days360ss,3)), font_size_8)
                    sheet.write(row, 14, str(round(days720ss, 3)), font_size_8)
                    sheet.write(row, 15, str(round(days721ss,3)), font_size_8)
                    sheet.write(row, 16, str(round(outstandingss, 3)), font_size_8)
                    row = row + 1
                partner = move['partner_id']
                # firstrow = True
                outstandingss = 0
                not_duess = 0
                days30ss = 0
                days60ss = 0
                days90ss = 0
                days180ss = 0
                days360ss = 0
                days720ss = 0
                days721ss = 0
            outstanding = 0
            not_due = 0
            days30 = 0
            days60 = 0
            days90 = 0
            days180 = 0
            days360 = 0
            days720 = 0
            days721 = 0
            credits = move['credits'] or 0
            debits = move['debits'] or 0
            debit = move['debit'] or 0
            credit = move['credit'] or 0
            total = debit + debits - credit - credits
            if move['date']>=endday:
                not_due += total
            elif move['date']>=(endday - timedelta(days=days)):
                days30 += total
            elif move['date']>=(endday - timedelta(days=days*2)):
                days60 += total
            elif move['date']>=(endday - timedelta(days=days*3)):
                days90 += total
            elif move['date']>=(endday - timedelta(days=days*4)):
                days180 += total
            elif move['date']>=(endday - timedelta(days=days*5)):
                days360 += total
            elif move['date'] >= (endday - timedelta(days=days * 6)):
                days720 += total
            else:
                days721 += total
            outstanding += not_due + days30 + days60 + days90 + days180 + days360 + days720 + days721
            if round(not_due,3)==0 and round(days30,3)==0 and round(days60,3)==0 and round(days90,3)==0 and round(days180,3)==0 and round(days360,3)==0 and round(days720,3)==0 and round(days721,3)==0:
                continue
            #if firstrow == True:
                #sheet.write(row, 0, move['partner_name'], font_size_8)
                #firstrow = False
            if move['invoice_name']:
                name = move['invoice_name']
            elif move['payment_name']:
                name = move['payment_name']
            else:
                name = move['journal_name']
            '''
            sheet.write(row, 0, move['partner_name']+"first line", font_size_8)
            sheet.write(row, 1, name, font_size_8)
            #sheet.write(row, 2, str(round(outstanding,3)), font_size_8)
            #sheet.write(row, 3, str(round(not_due,3)), font_size_8)
            sheet.write(row, 9, str(round(days30,3)), font_size_8)
            sheet.write(row, 10, str(round(days60,3)), font_size_8)
            sheet.write(row, 11, str(round(days90,3)), font_size_8)
            sheet.write(row, 12, str(round(days180,3)), font_size_8)
            sheet.write(row, 13, str(round(days360,3)), font_size_8)
            sheet.write(row, 14, str(round(days720, 3)), font_size_8)
            sheet.write(row, 15, str(round(days721,3)), font_size_8)
            sheet.write(row, 16, str(round(outstanding, 3)), font_size_8)
            '''
            outstandings += outstanding
            not_dues += not_due
            days30s += days30
            days60s += days60
            days90s += days90
            days180s += days180
            days360s += days360
            days720s += days720
            days721s += days721

            outstandingss += outstanding
            not_duess += not_due
            days30ss += days30
            days60ss += days60
            days90ss += days90
            days180ss += days180
            days360ss += days360
            days720ss += days720
            days721ss += days721
            #row = row + 1

        #sheet.merge_range(row, 0, row, 1, "Total last customer", font_size_8)
        # sheet.write(row, 2, str(round(outstandingss,3)), format21)
        #sheet.write(row, 9, str(round(not_duess,3)), format21)
        print("ccccc", count)
        customer = self.env['res.partner'].search([('id', '=', move['partner_id'])])

        sheet.write(row, 0, move['partner_name'], font_size_8)
        sheet.write(row, 1, customer.user_id.name, font_size_8)
        sheet.write(row, 2, customer.user_id.credit_days, font_size_8)
        sheet.write(row, 3, str(customer.user_id.credit_limit) + " days", font_size_8)
        sheet.write(row, 9, str(round(days30ss,3)), font_size_8)
        sheet.write(row, 10, str(round(days60ss,3)), font_size_8)
        sheet.write(row, 11, str(round(days90ss,3)), font_size_8)
        sheet.write(row, 12, str(round(days180ss,3)), font_size_8)
        sheet.write(row, 13, str(round(days360ss,3)), font_size_8)
        sheet.write(row, 14, str(round(days720ss, 3)), font_size_8)
        sheet.write(row, 15, str(round(days721ss,3)), font_size_8)
        sheet.write(row, 16, str(round(outstandingss, 3)), font_size_8)
        row = row + 1
        ####
        #print open balance
        if moves1:
            row = 1
            partner1 = 0
            for move in moves1:
                if partner1 != move['partner_id']:
                    if partner1 != 0 and (
                            round(not_duess, 3) != 0 or round(days30ss, 3) != 0 or round(days60ss, 3) != 0 or round(
                            days90ss, 3) != 0 or round(days180ss, 3) != 0 or round(days360ss, 3) != 0 or round(
                            days720ss, 3) != 0 or round(days721ss, 3) != 0):

                        sheet.write(row, 4, str(round(openbalancess, 3)), font_size_8)
                        row = row + 1
                    partner1 = move['partner_id']

                    openbalancess = 0

                openbalance = 0

                credits = move['credits'] or 0
                debits = move['debits'] or 0
                debit = move['debit'] or 0
                credit = move['credit'] or 0
                total = debit + debits - credit - credits

                openbalance += total
                print("openbalance==", openbalance)
                if round(not_due, 3) == 0 and round(days30, 3) == 0 and round(days60, 3) == 0 and round(days90,
                                                                                                        3) == 0 and round(
                        days180, 3) == 0 and round(days360, 3) == 0 and round(days720, 3) == 0 and round(days721,
                                                                                                         3) == 0:
                    continue

                openbalances += openbalance

                openbalancess += openbalance



            sheet.write(row, 4, str(round(openbalancess, 3)), font_size_8)
            row = row + 1
        ###

        if(data['form']['receivable']==True and data['form']['payable']==True):
            query = """
            SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
            LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
            LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
            LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
            LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
			where "account_move_line".date<=%s and move.state='posted' and account.user_type_id in (1,2) and "account_move_line".partner_id is NULL
			ORDER BY "account_move_line".date DESC"""
        elif(data['form']['receivable']==True):
            query = """
            SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
            LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
            LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
            LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
            LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
			where "account_move_line".date>=%s and "account_move_line".date<=%s and move.state='posted' and account.user_type_id = 1 and "account_move_line".partner_id is NULL
			ORDER BY "account_move_line".date DESC"""
        elif(data['form']['payable']==True):
            query = """
            SELECT invoice.name as invoice_name, payment.id as payment_name, move.name as journal_name, "account_move_line".date, "account_move_line".debit, "account_move_line".credit, (select sum(amount) from account_partial_reconcile where "account_move_line".id=debit_move_id and max_date<=%s) as credits, (select sum(amount) from account_partial_reconcile where "account_move_line".id=credit_move_id and max_date<=%s) as debits, "account_move_line".credit FROM "account_move_line"
            LEFT JOIN account_move invoice ON ("account_move_line".move_id = invoice.id)
            LEFT JOIN account_payment payment ON ("account_move_line".payment_id = payment.id)
            LEFT JOIN account_move move ON ("account_move_line".move_id = move.id)
            LEFT JOIN account_account account ON ("account_move_line".account_id = account.id)
			where "account_move_line".date<=%s and move.state='posted' and account.user_type_id = 2 and "account_move_line".partner_id is NULL
			ORDER BY "account_move_line".date DESC"""
        self.env.cr.execute(query, [endday, endday, startday, endday])
        sql = self.env.cr.dictfetchall()
        moves = sql
        #firstrow == True
        outstandingss = 0
        not_duess = 0
        days30ss = 0
        days60ss = 0
        days90ss = 0
        days180ss = 0
        days360ss = 0
        days720ss = 0
        days721ss = 0
        for move in moves:
            outstanding = 0
            not_due = 0
            days30 = 0
            days60 = 0
            days90 = 0
            days180 = 0
            days360 = 0
            days720 = 0
            days721 = 0
            credits = move['credits'] or 0
            debits = move['debits'] or 0
            debit = move['debit'] or 0
            credit = move['credit'] or 0
            total = debit + debits - credit - credits
            if move['date']>=endday:
                not_due += total
            elif move['date']>=(endday - timedelta(days=days)):
                days30 += total
            elif move['date']>=(endday - timedelta(days=days*2)):
                days60 += total
            elif move['date']>=(endday - timedelta(days=days*3)):
                days90 += total
            elif move['date']>=(endday - timedelta(days=days*4)):
                days180 += total
            elif move['date']>=(endday - timedelta(days=days*5)):
                days360 += total
            elif move['date']>=(endday - timedelta(days=days*6)):
                days720 += total
            else:
                days721 += total
            outstanding += not_due + days30 + days60 + days90 + days180 + days360 + days720 + days721
            if round(not_due,3)==0 and round(days30,3)==0 and round(days60,3)==0 and round(days90,3)==0 and round(days180,3)==0 and round(days360,3)==0 and round(days720,3)==0  and round(days721,3)==0:
                continue
            #if firstrow == True:
                #sheet.write(row, 0, 'UNKNOWN', font_size_8)
                #firstrow = False
            if move['invoice_name']:
                name = move['invoice_name']
            elif move['payment_name']:
                name = move['payment_name']
            else:
                name = move['journal_name']
            '''
            sheet.write(row, 0, 'UNKNOWN t', font_size_8)
            sheet.write(row, 1, name, font_size_8)
            #sheet.write(row, 2, str(round(outstanding,3)), font_size_8)
            #sheet.write(row, 3, str(round(not_due,3)), font_size_8)
            sheet.write(row, 9, str(round(days30,3)), font_size_8)
            sheet.write(row, 10, str(round(days60,3)), font_size_8)
            sheet.write(row, 11, str(round(days90,3)), font_size_8)
            sheet.write(row, 12, str(round(days180,3)), font_size_8)
            sheet.write(row, 13, str(round(days360,3)), font_size_8)
            sheet.write(row, 14, str(round(days720, 3)), font_size_8)
            sheet.write(row, 15, str(round(days721,3)), font_size_8)
            sheet.write(row, 16, str(round(outstanding, 3)), font_size_8)
            '''
            outstandings += outstanding
            not_dues += not_due
            days30s += days30
            days60s += days60
            days90s += days90
            days180s += days180
            days360s += days360
            days720s += days720
            days721s += days721

            outstandingss += outstanding
            not_duess += not_due
            days30ss += days30
            days60ss += days60
            days90ss += days90
            days180ss += days180
            days360ss += days360
            days720ss += days720
            days721ss += days721
            #row = row + 1
        '''
        if (round(not_duess,3)!=0 or round(days30ss,3)!=0 or round(days60ss,3)!=0 or round(days90ss,3)!=0 or round(days180ss,3)!=0 or round(days360ss,3)!=0 or round(days720ss,3)!=0 or round(days721ss,3)!=0):
            sheet.merge_range(row, 0, row, 1, "Total", format21)
            #sheet.write(row, 2, str(round(outstandingss,3)), format21)
            sheet.write(row, 3, str(round(not_duess,3))+"tttt", format21)
            sheet.write(row, 9, str(round(days30ss,3)), format21)
            sheet.write(row, 10, str(round(days60ss,3)), format21)
            sheet.write(row, 11, str(round(days90ss,3)), format21)
            sheet.write(row, 12, str(round(days180ss,3)), format21)
            sheet.write(row, 13, str(round(days360ss,3)), format21)
            sheet.write(row, 14, str(round(days720ss, 3)), format21)
            sheet.write(row, 15, str(round(days721ss,3)), format21)
            row = row + 2
        '''
        sheet.merge_range(row, 0, row, 1, "Total", format21)
        #sheet.write(row, 2, str(round(outstandings,3)), format21)
        sheet.write(row, 3, str(round(not_dues,3))+"ttt11", format21)
        sheet.write(row, 9, str(round(days30s,3)), format21)
        sheet.write(row, 10, str(round(days60s,3)), format21)
        sheet.write(row, 11, str(round(days90s,3)), format21)
        sheet.write(row, 12, str(round(days180s,3)), format21)
        sheet.write(row, 13, str(round(days360s,3)), format21)
        sheet.write(row, 14, str(round(days720s, 3)), format21)
        sheet.write(row, 15, str(round(days721s,3)), format21)
        sheet.write(row, 16, str(round(outstandings, 3)), format21)
