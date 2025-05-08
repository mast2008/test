# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
#import pytz
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from . import user_tz_dtm
import base64
import io
from collections import defaultdict

class InventoryValuationXlsx(models.AbstractModel):

    _name = 'report.mast_inventory_valuation_reports'
    _inherit = 'report.report_xlsx.abstract'

    def get_product_list(self, categ=False):
        pdt_obj = self.env['product.product'].search([('categ_id', '=', categ), ('active', '=', True),('detailed_type','!=','service')])
        products = sorted(list(set(pdt_obj.mapped('id'))))
        return products

    def get_opening_data_all(self,products,location_objs ,date_from=False):
        date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        query = """
                SELECT  product.id as product_id,
                    pt.name as product_name,
                    stloac.id locationid,
                    stloac.complete_name as location_name,
                    product.default_code as stock_code,
                    u.name as uom,
                    
                    SUM(st_move.product_uom_qty	) as opening,
                     SUM(st_move.price_unit*st_move.product_uom_qty) as opening_cost,
                    COUNT(*) as count_val
                FROM stock_move as st_move
                LEFT JOIN product_product product ON (st_move.product_id = product.id)
                LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
                LEFT JOIN stock_location stloac ON (st_move.location_dest_id = stloac.id)
                LEFT JOIN uom_uom u on (u.id=st_move.product_uom)
                WHERE st_move.date<=%s and st_move.product_id in %s and st_move.location_dest_id in %s
                GROUP BY product.id,pt.name,locationid,uom
                """
        self.env.cr.execute(query, [date_from, tuple(products.ids),tuple(location_objs.ids)])
        sql = self.env.cr.dictfetchall()
        move = sorted(sql, key=lambda k: k['product_id'])
        #opening = move[0]['opening'] if move and move[0]['opening'] else 0
        #opening_cost = move[0]['opening_cost'] if move and move[0]['opening_cost'] else 0
        return move

    def get_stock_data_all(self, products,location_objs, date_to=False):
        #date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        date_to = datetime.combine(datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT), datetime.max.time())
        production_list = {}

        ######Receipt######
        query2 = """
            SELECT product.id as product_id,
            ld.id as locationid,
            ld.complete_name as location_name,
                SUM(CASE
                    WHEN (ls.usage in ('supplier','customer','production','transit')) AND sm.state = 'done' THEN product_uom_qty
                END) AS receipt,
                SUM(CASE
                    WHEN (ls.usage = 'inventory') AND sm.state = 'done' THEN product_uom_qty
                END) AS inv_receipt,
                SUM (sm.price_unit*sm.product_uom_qty) as receipts_cost

            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where  sm.date<=%s and sm.product_id in %s and sm.state='done' and ld.usage = 'internal' and ld.id in %s
            group by product.id,sm.state,sm.price_unit,locationid
            """
        self.env.cr.execute(query2, [date_to,tuple(products.ids),tuple(location_objs.ids)])
        sql = self.env.cr.dictfetchall()
        receipts = sorted(sql, key=lambda k: k['product_id'])

        #inv_receipt = receipts[0]['inv_receipt'] if receipts and receipts[0]['inv_receipt'] else 0
        #receipt_receipt = receipts[0]['receipt'] if receipts and receipts[0]['receipt'] else 0
        #receipts_cost = receipts[0]['receipts_cost'] if receipts and receipts[0]['receipts_cost'] else 0

        query3 = """
            SELECT product.id as product_id,
            ld.id as locationid,
            ld.complete_name as location_name,
                SUM(CASE
                    WHEN (ld.usage in ('supplier','customer','transit')) AND sm.state = 'done' THEN product_uom_qty
                END) AS sales,
                SUM(CASE
                    WHEN (ld.usage = 'production') AND sm.state = 'done' THEN product_uom_qty
                END) AS consume,
                SUM(CASE
                    WHEN (ld.usage = 'inventory') AND sm.state = 'done' THEN product_uom_qty
                END) AS inv_adj,
                SUM (sm.price_unit*sm.product_uom_qty) as issues_cost
            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where  sm.date<=%s and sm.product_id in %s and sm.state='done' and ls.usage = 'internal' and ld.id in %s
            group by product.id,sm.state,sm.price_unit,locationid
            """
        self.env.cr.execute(query3, [date_to,tuple(products.ids),tuple(location_objs.ids)])
        sql = self.env.cr.dictfetchall()
        issues = sorted(sql, key=lambda k: k['product_id'])
        #sales = issues[0]['sales'] if issues and issues[0]['sales'] else 0
        #consume = issues[0]['consume'] if issues and issues[0]['consume'] else 0
        #inv_adj = issues[0]['inv_adj'] if issues and issues[0]['inv_adj'] else 0
        #issues_cost = issues[0]['issues_cost'] if issues and issues[0]['issues_cost'] else 0
        return receipts,issues


    def get_opening_data(self, pdt_id, date_from=False,location_id=False):
        date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        opening_list = {}
        if pdt_id:
            pdt = self.env['product.product'].search([('id', '=', pdt_id)])
            #acc_id = pdt.categ_id.property_stock_valuation_account_id.id
            ######Opening Balance######
            # query = """
            #     SELECT product.id as product_id,
            #         pt.name as product_name,
            #         product.default_code as stock_code,
            #         SUM(acc_move_line.quantity) as opening,
            #         COALESCE (sum(acc_move_line.debit - acc_move_line.credit),0) as opening_cost,
            #         COUNT(*) as count_val
            #     FROM account_move_line as acc_move_line
            #     LEFT JOIN product_product product ON (acc_move_line.product_id = product.id)
            #     LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            #     WHERE acc_move_line.date<=%s and acc_move_line.product_id = %s and acc_move_line.account_id = %s and acc_move_line.parent_state = 'posted'
            #     GROUP BY product.id,pt.name
            #     """
            query = """
                SELECT product.id as product_id,
                    pt.name as product_name,
                    product.default_code as stock_code,
                    SUM(st_move.product_uom_qty	) as opening,
                     SUM(st_move.price_unit) as opening_cost,
                    COUNT(*) as count_val
                FROM stock_move as st_move
                LEFT JOIN product_product product ON (st_move.product_id = product.id)
                LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
                LEFT JOIN stock_location stloac ON (st_move.location_dest_id = stloac.id)
                WHERE st_move.date<=%s and st_move.product_id = %s and st_move.location_dest_id= %s
                GROUP BY product.id,pt.name,st_move.price_unit
                """



            #self.env.cr.execute(query, [date_from, pdt.id, acc_id])
            self.env.cr.execute(query, [date_from, pdt.id,location_id])

            # """
            # SUM(CASE WHEN acc_move_line.ref  IS NOT NULL THEN acc_move_line.quantity ELSE 0 END) AS opening,
            #
            # """
            sql = self.env.cr.dictfetchall()
            # if pdt.id == 821:
            #    print("sqllllllll",sql)
            move = sorted(sql, key=lambda k: k['product_id'])
            opening_list.update({pdt.id: {}})
            #stock_code = pdt.default_code or ''
            #product_name = pdt.name or ''
            # product_uom = move[0]['product_uom'] if move else ''
            #product_uom = pdt.uom_id.name
            opening = move[0]['opening'] if move and move[0]['opening'] else 0
            opening_cost = move[0]['opening_cost'] if move and move[0]['opening_cost'] else 0
            #print("opening_cost",opening_cost)
            #opening_list[pdt.id]['stock_code'] = stock_code
            #opening_list[pdt.id]['product_name'] = product_name
            #opening_list[pdt.id]['product_uom'] = product_uom
            opening_list[pdt.id]['opening'] = opening
            opening_list[pdt.id]['opening_cost'] = opening_cost
        return opening_list

    def get_closing_data(self, pdt_id, date_to=False,location_id=False):
        date_to = datetime.combine(datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT), datetime.max.time())
        closing_list = {}
        if pdt_id:
            pdt = self.env['product.product'].search([('id', '=', pdt_id)])
            acc_id = pdt.categ_id.property_stock_valuation_account_id.id
            ######Closing Balance######
            # query4 = """
            #     SELECT product.id as product_id,
            #         pt.name as product_name,
            #         product.default_code as stock_code,
            #         SUM(acc_move_line.quantity) as closing,
            #         COALESCE (sum(acc_move_line.debit - acc_move_line.credit),0) as closing_cost,
            #         COUNT(*) as count_val
            #     FROM account_move_line as acc_move_line
            #     LEFT JOIN product_product product ON (acc_move_line.product_id = product.id)
            #     LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            #     WHERE acc_move_line.date<=%s and acc_move_line.product_id = %s and acc_move_line.account_id = %s and acc_move_line.parent_state = 'posted'
            #     GROUP BY product.id,pt.name
            #     """
            # self.env.cr.execute(query4, [date_to, pdt.id, acc_id])

            query4 = """
                            SELECT product.id as product_id,
                                pt.name as product_name,
                                product.default_code as stock_code,
                                SUM(sm.product_uom_qty	) as closing,
                                SUM (sm.price_unit) as closing_cost,
                                COUNT(*) as count_val
                            FROM stock_move as sm
                            LEFT JOIN product_product product ON (sm.product_id = product.id)
                            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
                            WHERE sm.date<=%s and sm.product_id = %s and sm.location_dest_id=%s
                            GROUP BY product.id,pt.name,sm.price_unit
                            """
            #self.env.cr.execute(query4, [date_to, pdt.id,acc_id])
            self.env.cr.execute(query4, [date_to, pdt.id,location_id])

            sql = self.env.cr.dictfetchall()
            move = sorted(sql, key=lambda k: k['product_id'])
            # """
            # SUM(CASE WHEN acc_move_line.ref  IS NOT NULL THEN acc_move_line.quantity ELSE 0 END) AS closing,
            #
            # """
            closing_list.update({pdt.id: {}})
            #stock_code = pdt.default_code or ''
            #product_name = pdt.name or ''
            # product_uom = move[0]['product_uom'] if move else ''
            #product_uom = pdt.uom_id.name
            closing = move[0]['closing'] if move and move[0]['closing'] else 0
            closing_cost = move[0]['closing_cost'] if move and move[0]['closing_cost'] else 0
            #closing_list[pdt.id]['stock_code'] = stock_code
            #closing_list[pdt.id]['product_name'] = product_name
            #closing_list[pdt.id]['product_uom'] = product_uom
            closing_list[pdt.id]['closing'] = closing
            closing_list[pdt.id]['closing_cost'] = closing_cost
            #if pdt.product_tmpl_id.id == 1193:
                #print("kkkkkk", move[0]['count_val'], pdt.name)
        return closing_list

    def get_stock_data(self, pdt_id, date_from=False, date_to=False,location_id=False):
        date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        date_to = datetime.combine(datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT), datetime.max.time())
        production_list = {}
        if pdt_id:
            pdt = self.env['product.product'].search([('id', '=', pdt_id)])
            ######Receipt######
            query2 = """
            SELECT product.id as product_id,
                SUM(CASE
                    WHEN (ls.usage in ('supplier','customer','production','transit')) AND sm.state = 'done' THEN product_uom_qty
                END) AS receipt,
                SUM(CASE
                    WHEN (ls.usage = 'inventory') AND sm.state = 'done' THEN product_uom_qty
                END) AS inv_receipt,
                SUM (sm.price_unit) as receipts_cost

            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where sm.date>%s and sm.date<=%s and sm.product_id = %s and sm.state='done' and ld.usage = 'internal' and ld.id= %s
            group by product.id,sm.state,sm.price_unit
            """
            self.env.cr.execute(query2, [date_from, date_to, pdt.id,location_id])
            sql = self.env.cr.dictfetchall()
            receipts = sorted(sql, key=lambda k: k['product_id'])

            inv_receipt = receipts[0]['inv_receipt'] if receipts and receipts[0]['inv_receipt'] else 0
            receipt_receipt = receipts[0]['receipt'] if receipts and receipts[0]['receipt'] else 0

            # if receipts and not production_list[pdt.id]['product_uom']:
            #    product_uom = receipts[0]['product_uom']
            #product_uom = receipts[0]['product_uom'] if receipts else ''
            #location=receipts[0]['location'] if receipts else None
            #print("location",location)

            receipts_cost = receipts[0]['receipts_cost'] if receipts and receipts[0]['receipts_cost'] else 0
            #print("receipts_cost",receipts_cost)
            production_list.update({pdt.id: {}})
            production_list[pdt.id]['inv_receipt'] = inv_receipt
            production_list[pdt.id]['receipt'] = receipt_receipt
            #production_list[pdt.id]['product_uom'] = product_uom
            #production_list[pdt.id]['location'] = location
            production_list[pdt.id]['receipts_cost'] = receipts_cost
            ######Issues######
            query3 = """
            SELECT product.id as product_id,
                SUM(CASE
                    WHEN (ld.usage in ('supplier','customer','transit')) AND sm.state = 'done' THEN product_uom_qty
                END) AS sales,
                SUM(CASE
                    WHEN (ld.usage = 'production') AND sm.state = 'done' THEN product_uom_qty
                END) AS consume,
                SUM(CASE
                    WHEN (ld.usage = 'inventory') AND sm.state = 'done' THEN product_uom_qty
                END) AS inv_adj,
                SUM (sm.price_unit) as issues_cost

            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where sm.date>%s and sm.date<=%s and sm.product_id = %s and sm.state='done' and ls.usage = 'internal' and ld.id= %s
            group by product.id,sm.state,sm.price_unit
            """
            self.env.cr.execute(query3, [date_from, date_to, pdt.id,location_id])
            sql = self.env.cr.dictfetchall()
            issues = sorted(sql, key=lambda k: k['product_id'])
            sales = issues[0]['sales'] if issues and issues[0]['sales'] else 0
            consume = issues[0]['consume'] if issues and issues[0]['consume'] else 0
            inv_adj = issues[0]['inv_adj'] if issues and issues[0]['inv_adj'] else 0
            # if issues and not production_list[pdt.id]['product_uom']:
            #    product_uom = issues[0]['product_uom']
            #product_uom = issues[0]['product_uom'] if issues else ''
            #location = issues[0]['location'] if issues else None
            issues_cost = issues[0]['issues_cost'] if issues and issues[0]['issues_cost'] else 0
            production_list[pdt.id]['sales'] = sales
            production_list[pdt.id]['consume'] = consume
            production_list[pdt.id]['inv_adj'] = inv_adj
            #production_list[pdt.id]['product_uom'] = product_uom
            #production_list[pdt.id]['location'] = location
            production_list[pdt.id]['issues_cost'] = issues_cost
            #print("sales",sales,consume,inv_adj)
        return production_list

    def generate_xlsx_report(self, workbook, data, lines):
        try:
            DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
            date = data['form']['create_date']
            sheet = workbook.add_worksheet()

            product_uom_dp = self.env.ref('product.decimal_product_uom')
            rec = lines
            currency_id=self.env.user.company_id.currency_id
            user_lang = user_tz_dtm.get_language(self)
            currency_num_format = f"#{user_lang.thousands_sep}##0{user_lang.decimal_point}{currency_id.decimal_places * '0'}"
            uom_num_format = f"###0.{product_uom_dp.digits * '0'}"
            col_center = workbook.add_format({'bold': True, 'font_size': 10, 'align': 'center'})
            font_size_8_currency = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,'num_format': currency_num_format})
            format41_currency = workbook.add_format({'font_size': 8, 'align': 'right', 'right': True, 'left': True, 'bottom': True, 'top': True,'bold': True, 'num_format': currency_num_format})
            format_sign = workbook.add_format({'font_size': 8, 'align': 'left','bold': True,})
            format_sign1 = workbook.add_format({'font_size': 8, 'align': 'left'})
            format1 = workbook.add_format({'font_size': 12})
            format10 = workbook.add_format({'font_size': 10, 'align': 'center'})
            format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,'bold': True})
            format21 = workbook.add_format({'font_size': 10, 'align': 'center'})
            format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
            format41 = workbook.add_format({'font_size': 8, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,'bold': True})
            format42 = workbook.add_format({'font_size': 8, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True})
            font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
            red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,'bg_color': 'red'})
            justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
            format3.set_align('center')
            font_size_8.set_align('center')
            justify.set_align('justify')
            format1.set_align('center')
            red_mark.set_align('center')
            sheet.set_column('B:B', 20)
            sheet.set_column('C:C', 38)
            sheet.set_column('E:E', 35)
            sheet.set_column('F:F', 12)
            sheet.set_column('G:G', 18)
            sheet.set_column('F:F', 18)
            sheet.set_column('H:H', 15)
            sheet.set_column('I:I', 18)
            sheet.set_column('J:J', 18)
            sheet.set_column('O:O', 12)
            sheet.set_column('P:P', 12)
            sheet.merge_range(1, 0, 1, 9, str(self.env.user.company_id.name), format1)
            buf_image = io.BytesIO(base64.b64decode(self.env.user.company_id.logo))
            # sheet.set_column(1, 9, 15)
            sheet.insert_image('B2', "any_name.png", {'image_data': buf_image, 'x_scale': 0.8, 'y_scale': 0.8})
            address_company = []
            if self.env.user.company_id.street:
                address_company.append('Flat/Shop No. ' + self.env.user.company_id.street)
            if self.env.user.company_id.street2:
                address_company.append('Building ' + self.env.user.company_id.street2)
            if self.env.user.company_id.city:
                address_company.append(self.env.user.company_id.city)
            if self.env.user.company_id.zip:
                address_company.append(self.env.user.company_id.zip)
            if self.env.user.company_id.country_id:
                address_company.append(self.env.user.company_id.country_id.name)
            sheet.merge_range(2, 0, 2, 9, str(', '.join(address_company)), format21)
            sheet.merge_range(3, 0, 3,9, 'Inventory Valuation', format10)
            user_date_format = self.env['res.lang']._lang_get(self.env.user.lang).date_format
            #startday = datetime.strptime(data['form']['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime(str(user_date_format))
            endday = datetime.strptime(data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime(str(user_date_format))
            sheet.merge_range(4, 0, 4, 9, 'As on Date of ' +str(endday) + ')', format21)
            # sheet.merge_range('A4:I4', 'Employee', format11)
            sheet.write(6, 0, 'SL.No', format41)
            sheet.write(6, 1, 'Product Code', format41)
            sheet.write(6, 2, 'Product Description', format41)
            sheet.write(6, 3, 'UOM', format41)
            sheet.write(6, 4, 'Location', format41)
            sheet.write(6, 5, 'Total Qty', format41)
            sheet.write(6, 6, 'Cost Per Unit', format41)
            sheet.write(6, 7, 'Total Cost', format41)
            sheet.write(6, 8, 'Selling Price Per Unit', format41)
            sheet.write(6, 9, 'Total Selling Price', format41)
            if not data['form']['date_to']:
                data['form']['date_to'] = ''
            #if not data['form']['date_from']:
                #data['form']['date_from'] = ''
            row = 7

            sl_no = 1
            if data['form']['location_id']:
                location_objs = self.env['stock.location'].sudo().search([('id', 'in', (data['form']['location_id']))])
            else:
                location_objs = self.env['stock.location'].sudo().search([('usage', '=', 'internal')])
            if data['form']['categ_ids']:
                categ_objs = self.env['product.category'].sudo().search([('id', 'in', data['form']['categ_ids'])])
            else:
                categ_objs = self.env['product.category'].sudo().search([])
                #products = self.get_product_list(categ)
            products=self.env['product.product'].sudo().search([('categ_id', 'in', categ_objs.ids), ('active', '=', True), ('detailed_type', '=', 'product')])
            print("len(products)",len(products))
            if products:
                #opening_data = self.get_opening_data_all(products, location_objs, data['form']['date_from'])
                #print("opening_data",len(opening_data),opening_data)
                #stock_data = self.get_stock_data_all(products, location_objs, data['form']['date_from'],data['form']['date_to'])
                stock_data = self.get_stock_data_all(products, location_objs,data['form']['date_to'])

                #print("stock_data[0]",(stock_data[0]))
                #print("(stock_data[1])",(stock_data[1]))

                # tmp = defaultdict(list)
                # for item in opening_data:
                #     tmp[item['product_id'],item['product_name'],item['uom'],item['stock_code']].append([item['location_name'], item['opening'],item['opening_cost']])
                # if stock_data[0]:
                #     for stock_data_item in stock_data[0]:
                #         print("stock_data_item",stock_data_item)
                #
                #
                # parsed_list = [{'product_id': k, 'data': v} for k, v in tmp.items()]
                # #print(parsed_list)
                # if parsed_list:
                #     for item in parsed_list:
                #         #print("item.get('product_id')",item.get('product_id'))
                #         #print("item.get('data')",item.get('data'))
                #         sheet.write(row, 0, sl_no, font_size_8)
                #         sheet.write(row, 1, item.get('product_id')[3], font_size_8)
                #         sheet.write(row, 2, item.get('product_id')[1], font_size_8)
                #         sheet.write(row, 3, item.get('product_id')[2], font_size_8)
                #         for item_data in item.get('data'):
                #             sheet.write(row, 4, item_data[0], font_size_8)
                #             sheet.write(row, 5, (item_data[1] if item_data[1] else 0), font_size_8)
                #             sheet.write(row, 7, item_data[2] if item_data[2] else 0 , font_size_8_currency)
                #             if (len(item.get('data'))>1):
                #                 row+=1
                #         row+=1
                #         sl_no+=1



                # if opening_data:
                #     for move_open in opening_data:
                #         tot_qty_final=0
                #         pdt_obj=self.env['product.product'].sudo().browse(int(move_open.get('product_id')))
                #         sheet.write(row, 0, sl_no, font_size_8)
                #         sheet.write(row, 1, move_open.get('stock_code'), font_size_8)
                #         sheet.write(row, 2, move_open.get('product_name'), font_size_8)
                #         sheet.write(row, 3, move_open.get('uom'), font_size_8)
                #         sheet.write(row, 4, move_open.get('location_name'), font_size_8)
                #
                #         #sheet.write(row, 5, (tot_qty_final), font_size_8)
                #         #sheet.write(row, 6, unit_cost, font_size_8_currency)
                #         #sheet.write(row, 7, tot_cost_final, font_size_8_currency)
                #         sheet.write(row, 8, pdt_obj.list_price, font_size_8_currency)
                #         sheet.write(row, 9, (pdt_obj.list_price)*tot_qty_final, font_size_8_currency)
                #         row += 1
                #         sl_no += 1





                for product in products:
                    sheet.write(row, 0, sl_no, font_size_8)
                    sheet.write(row, 1, product.default_code, font_size_8)
                    sheet.write(row, 2, product.name, font_size_8)
                    sheet.write(row, 3, product.uom_id.name, font_size_8)
                    pdt_sell_price = product.list_price
                    for location in location_objs:
                        #tot_qty=0
                        #tot_cost=0
                        tot_qty_final=0
                        tot_cost_final = 0

                        #if opening_data:
                            #tot_qty_final+=(sum(move_open.get('opening')  if move_open.get('opening') else 0 for move_open in opening_data if move_open.get('product_id')==product.id and move_open.get('locationid')==location.id))
                            #tot_cost_final+=(sum(move_open.get('opening_cost') if move_open.get('opening_cost') else 0 for move_open in opening_data if move_open.get('product_id')==product.id and move_open.get('locationid')==location.id))

                            # for move_open in opening_data:
                            #     if move_open.get('product_id'):
                            #         if move_open.get('product_id')==product.id and move_open.get('locationid')==location.id:
                            #             #sheet.write(row, 5, move_open.get('opening'), font_size_8)
                            #             tot_qty+=move_open.get('opening') if move_open.get('opening') else 0
                            #             opening_cost=move_open.get('opening_cost') if move_open.get('opening_cost') else 0
                            #             tot_cost+=opening_cost
                        if stock_data[0]:
                            receipt=(sum(invalue.get('receipt')  if invalue.get('receipt') else 0 for invalue in stock_data[0] if invalue.get('product_id')==product.id and invalue.get('locationid')==location.id))
                            inv_receipt=(sum(invalue.get('inv_receipt')  if invalue.get('inv_receipt') else 0 for invalue in stock_data[0] if invalue.get('product_id')==product.id and invalue.get('locationid')==location.id))
                            tot_qty_final+=receipt+inv_receipt
                            receipt_cost=(sum(invalue.get('receipts_cost')  if invalue.get('receipts_cost') else 0 for invalue in stock_data[0] if invalue.get('product_id')==product.id and invalue.get('locationid')==location.id))
                            tot_cost_final+=receipt_cost

                            # for invalue in stock_data[0]:
                            #     if invalue.get('product_id'):
                            #         if invalue.get('product_id')==product.id and invalue.get('locationid')==location.id:
                            #             receipt=invalue.get('receipt') if invalue.get('receipt')  else 0
                            #             inv_receipt=invalue.get('inv_receipt') if invalue.get('inv_receipt') else 0
                            #             tot_qty+=receipt+inv_receipt
                            #             receipt_cost=invalue.get('receipts_cost') if  invalue.get('receipts_cost') else 0
                            #             tot_cost += receipt_cost
                        if stock_data[1]:
                            sales=(sum(out_value.get('sales')  if out_value.get('sales') else 0 for out_value in stock_data[1] if out_value.get('product_id')==product.id and out_value.get('locationid')==location.id))
                            consume=(sum(out_value.get('consume')  if out_value.get('consume') else 0 for out_value in stock_data[1] if out_value.get('product_id')==product.id and out_value.get('locationid')==location.id))
                            inv_adj=(sum(out_value.get('inv_adj')  if out_value.get('inv_adj') else 0 for out_value in stock_data[1] if out_value.get('product_id')==product.id and out_value.get('locationid')==location.id))
                            tot_qty_final-=sales+consume+inv_adj
                            issues_cost=(sum(out_value.get('issues_cost')  if out_value.get('issues_cost') else 0 for out_value in stock_data[1] if out_value.get('product_id')==product.id and out_value.get('locationid')==location.id))
                            tot_cost_final += (issues_cost)

                            # for out_value in stock_data[1]:
                            #     if out_value.get('product_id'):
                            #         if out_value.get('product_id')==product.id and out_value.get('locationid')==location.id:
                            #             sales = out_value.get('sales') if out_value.get('sales') else 0
                            #             consume=out_value.get('consume') if out_value.get('consume')  else 0
                            #             inv_adj=out_value.get('inv_adj') if out_value.get('inv_adj')  else 0
                            #             tot_qty-=sales+consume+inv_adj
                            #             issues_cost=out_value.get('issues_cost') if out_value.get('issues_cost')  else 0
                            #             tot_cost+=(issues_cost)

                        if tot_qty_final>0:
                            sheet.write(row, 4, location.complete_name, font_size_8)
                            sheet.write(row, 5, (tot_qty_final), font_size_8)
                        #print("tot_qty_final", tot_qty_final)
                        #print("tot_qty", tot_qty)

                            if tot_qty_final > 0:
                                unit_cost=tot_cost_final/tot_qty_final
                            else:
                                unit_cost=0
                            sheet.write(row, 6, unit_cost, font_size_8_currency)
                            sheet.write(row, 7, tot_cost_final, font_size_8_currency)
                        #print("tot_cost_final", tot_cost_final)
                        #print("tot_cost", tot_cost)
                            sheet.write(row, 8, pdt_sell_price, font_size_8_currency)
                            sheet.write(row, 9, pdt_sell_price*tot_qty_final, font_size_8_currency)
                            row += 1
                        sl_no += 1




            # for product in products:
            #     sheet.write(row, 0, sl_no, font_size_8)
            #     sheet.write(row, 1, product.default_code, font_size_8)
            #     sheet.write(row, 2, product.name, font_size_8)
            #     sheet.write(row, 3, product.uom_id.name, font_size_8)
            #     pdt_sell_price = product.list_price
            #     for location in location_objs:
            #         moves = self.get_opening_data(product.id, data['form']['date_from'],location.id)
            #         #close_moves = self.get_closing_data(product.id, data['form']['date_to'],location.id)
            #         get_stock_moves= self.get_stock_data(product.id, data['form']['date_from'], data['form']['date_to'],location.id)
            #         sheet.write(row, 4, location.complete_name, font_size_8)
            #         tot_qty= moves[product.id]['opening']+get_stock_moves[product.id]['inv_receipt']+ get_stock_moves[product.id]['receipt']+get_stock_moves[product.id]['sales'] + get_stock_moves[product.id]['consume'] + get_stock_moves[product.id]['inv_adj']
            #         sheet.write(row, 5,tot_qty , font_size_8)
            #         total_cost=moves[product.id]['opening_cost']+get_stock_moves[product.id]['issues_cost']+get_stock_moves[product.id]['receipts_cost']
            #         if tot_qty>0:
            #             unit_cost=total_cost/tot_qty
            #         else:
            #             unit_cost=0.0
            #         sheet.write(row, 6, unit_cost, font_size_8_currency)
            #         sheet.write(row, 7, total_cost, font_size_8_currency)
            #         sheet.write(row, 8, pdt_sell_price, font_size_8_currency)
            #         sheet.write(row, 9, pdt_sell_price*tot_qty, font_size_8_currency)
            #         row = row + 1
            #     sl_no+=1

            # else:
            #     for categ in self.env['product.category'].sudo().search([]):
            #         products = self.get_product_list(categ.id)
            #         for product in products:
            #             sheet.write(row, 0, sl_no, font_size_8)
            #             sheet.write(row, 1, product.default_code, font_size_8)
            #             sheet.write(row, 2, product.name, font_size_8)
            #             sheet.write(row, 3, product.uom_id.name, font_size_8)
            #             pdt_sell_price = product.list_price
            #
            #             moves = self.get_opening_data(product, data['form']['date_from'], data['form']['location_id'])
            #             close_moves = self.get_closing_data(product, data['form']['date_to'],data['form']['location_id'])
            #             #moves = self.get_opening_data(product, data['form']['date_from'])
            #             #close_moves = self.get_closing_data(product, data['form']['date_to'])
            #             get_stock_moves= self.get_stock_data(product, data['form']['date_from'], data['form']['date_to'],data['form']['location_id'])
            #             #print("moves0000", moves)
            #             sheet.write(row, 0, sl_no, font_size_8)
            #             sheet.write(row, 1, moves[product]['stock_code'], font_size_8)
            #             sheet.write(row, 2, moves[product]['product_name'], font_size_8)
            #             sheet.write(row, 3, moves[product]['product_uom'] or close_moves[product]['product_uom'],font_size_8)
            #             sheet.write(row, 4, location_obj.complete_name, font_size_8)
            #
            #             ###opening Balance###
            #             if moves[product]['opening']:
            #                 op_balance = moves[product]['opening_cost'] / moves[product]['opening']
            #             else:
            #                 op_balance = moves[product]['opening_cost']
            #             tot_qty= moves[product]['opening']+get_stock_moves[product]['inv_receipt']+ get_stock_moves[product]['receipt']+get_stock_moves[product]['sales'] + get_stock_moves[product]['consume'] + get_stock_moves[product]['inv_adj']
            #             sheet.write(row, 5,tot_qty , font_size_8)
            #             #total_cost=moves[product]['opening_cost']+close_moves[product]['closing_cost']
            #             total_cost = moves[product]['opening_cost'] + get_stock_moves[product]['issues_cost'] + get_stock_moves[product]['receipts_cost']
            #             if tot_qty>0:
            #                 unit_cost=total_cost/tot_qty
            #             else:
            #                 unit_cost=0.0
            #
            #             sheet.write(row, 6, unit_cost, font_size_8_currency)
            #             sheet.write(row, 7, total_cost, font_size_8_currency)
            #             #moves = self.get_stock_data(product, data['form']['date_from'], data['form']['date_to'])
            #             print("get_stock_moves", get_stock_moves)
            #             ###Receipt###
            #             sheet.write(row, 8, pdt_sell_price, font_size_8)
            #             sheet.write(row, 9, pdt_sell_price*tot_qty, font_size_8)
            #             #sheet.write(row, 8, moves[product]['inv_receipt'] + moves[product]['receipt'], font_size_8)
            #             ###Issues###
            #             #sheet.write(row, 9, moves[product]['sales'], font_size_8)
            #             #sheet.write(row, 10, moves[product]['consume'], font_size_8)
            #             #sheet.write(row, 11, moves[product]['inv_adj'], font_size_8)
            #             #sheet.write(row, 12,moves[product]['sales'] + moves[product]['consume'] + moves[product]['inv_adj'],font_size_8)
            #
            #             ###Closing Balance###
            #
            #             # print("moves2222", close_moves)
            #             if close_moves[product]['closing']:
            #                 cl_balance = close_moves[product]['closing_cost'] / close_moves[product]['closing']
            #             else:
            #                 cl_balance = close_moves[product]['closing_cost']
            #             #sheet.write(row, 13, close_moves[product]['closing'], font_size_8)
            #             #sheet.write(row, 14, cl_balance, font_size_8_currency)
            #             #sheet.write(row, 15, close_moves[product]['closing_cost'], font_size_8_currency)
            #             # total_close_value += close_moves[product]['closing_cost']
            #             # total_close_cost += cl_balance
            #             # total_close_stock += close_moves[product]['closing']
            #             # categ_total_close_value += close_moves[product]['closing_cost']
            #             # categ_total_close_cost += cl_balance
            #             # categ_total_close_stock += close_moves[product]['closing']
            #             """for k in moves:
            #                 #for k in sorted_d:
            #                 close_bal = moves[k]['opening'] + moves[k]['inv_receipt'] + moves[k]['receipt'] - moves[k]['sales'] - moves[k]['consume'] - moves[k]['inv_adj']
            #                 if close_bal:
            #                     row = row + 1
            #                     serial = serial + 1
            #                     sheet.write(row, 0, moves[k]['stock_code'], font_size_8)
            #                     sheet.write(row, 1, moves[k]['product_name'], font_size_8)
            #                     sheet.write(row, 2, moves[k]['product_uom'], font_size_8)
            #                     ###opening Balance###
            #                     if moves[k]['opening']:
            #                         op_balance = moves[k]['opening_cost']/moves[k]['opening']
            #                     else:
            #                         op_balance = moves[k]['opening_cost']
            #                     sheet.write(row, 3, moves[k]['opening'], font_size_8)
            #                     sheet.write(row, 4, moves[k]['opening_cost'], font_size_8_currency)
            #                     sheet.write(row, 5, op_balance, font_size_8_currency)
            #                     ###Receipt###
            #                     sheet.write(row, 6, moves[k]['inv_receipt'], font_size_8)
            #                     sheet.write(row, 7, moves[k]['receipt'], font_size_8)
            #                     sheet.write(row, 8, moves[k]['inv_receipt'] + moves[k]['receipt'], font_size_8)
            #                     ###Issues###
            #                     sheet.write(row, 9, moves[k]['sales'], font_size_8)
            #                     sheet.write(row, 10, moves[k]['consume'], font_size_8)
            #                     sheet.write(row, 11, moves[k]['inv_adj'], font_size_8)
            #                     sheet.write(row, 12, moves[k]['sales'] + moves[k]['consume'] + moves[k]['inv_adj'], font_size_8)
            #                     ###Closing Balance###
            #                     close_cost = moves[k]['opening_cost'] + moves[k]['receipts_cost'] + moves[k]['issues_cost']
            #                     close_value = close_cost/close_bal
            #                     sheet.write(row, 13, close_bal, font_size_8)
            #                     sheet.write(row, 14, close_cost, font_size_8_currency)
            #                     sheet.write(row, 15, close_value, font_size_8_currency)
            #                     total_close_value += close_value"""
            #         # sheet.write(row, 12, 'Sub Total', format41)
            #         # sheet.write(row, 13, categ_total_close_stock, format41)
            #         # sheet.write(row, 14, categ_total_close_cost, format41_currency)
            #         # sheet.write(row, 15, categ_total_close_value, format41_currency)
            #             row = row + 1
            #             sl_no+=1

            sheet.write(row+3, 1, "Reviewed By", format_sign)
            sheet.write(row + 4, 1, "Store Supervisor", format_sign1)

            sheet.write(row + 3, 9, "Approved By", format_sign)
            sheet.write(row + 4, 9, "Store Manager", format_sign1)

        except Exception as e:
            raise UserError("Error:-" + str(e))


class InventoryValuationReport(models.TransientModel):
    _name = "inventory_valuation_reports"
    _description = "Inventory Valuation Report"

    date_to = fields.Date(string='As on Date', required=True)
    #date_from = fields.Date(string='Date From', required=True)
    categ_ids = fields.Many2many('product.category', 'inv_valuation_pdt_category_rel', 'production_id', 'category_id', string='Product Categories')
    #categ_id = fields.Many2one('product.category', 'Product category', required=True)
    location_id=fields.Many2many('stock.location',string="Location",domain=[('usage','=','internal')])

    def excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'stock.move'
        datas['form'] = self.read()[0]
        report_xml_id = self.env.ref('aljaser_stock_valuation_report_ext.report_xlsx_valuation_report')
        report_xml_id.report_file = 'Stock Valuation Report'
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('aljaser_stock_valuation_report_ext.report_xlsx_valuation_report').with_context(
            discard_logo_check=True).report_action(self, data=datas)
