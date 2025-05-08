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

class StockMOveXlsx(models.AbstractModel):

    _name = 'report.mast_stock_move_reports'
    _inherit = 'report.report_xlsx.abstract'

    def get_product_list(self, categ=False):
        pdt_obj = self.env['product.product'].search([('categ_id', '=', categ),('active', '=', True)])
        #products = sorted(list(set(pdt_obj.mapped('id'))))
        return pdt_obj


    def get_opening_data_all(self,products,location_objs, date_from=False):
        date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        opening_list = {}
            #pdt = self.env['product.product'].search([('id', '=', pdt_id)])
            #acc_id = pdt.categ_id.property_stock_valuation_account_id.id
            ######Opening Balance######
        query = """
                SELECT product.id as product_id,
                    pt.name as product_name,
                    stloac.id as locationid,
                    stloac.complete_name as location_name,
                    u.name as uom,
                    product.default_code as stock_code,
                    SUM(sm.product_uom_qty) as opening
                  
                FROM stock_move as sm
                LEFT JOIN product_product product ON (sm.product_id = product.id)
                LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
                LEFT JOIN stock_location stloac ON (sm.location_dest_id = stloac.id)
                LEFT JOIN uom_uom u on (u.id=sm.product_uom)
                WHERE sm.date<=%s and sm.product_id in %s  and sm.location_dest_id in %s
                GROUP BY product.id,locationid,product_name,location_name,uom
                """
        self.env.cr.execute(query, [date_from,tuple(products.ids),tuple(location_objs.ids)])
            # """
            # SUM(CASE WHEN acc_move_line.ref  IS NOT NULL THEN acc_move_line.quantity ELSE 0 END) AS opening,
            #
            # """
        sql = self.env.cr.dictfetchall()
        move = sorted(sql, key=lambda k: k['product_id'])
        return move
        #opening_list.update({pdt_id.id: {}})
        #opening = move[0]['opening'] if move and move[0]['opening'] else 0
        #opening_list[pdt_id.id]['opening'] = opening
        #return opening_list

    def get_stock_data_all(self, products,location_objs,date_from=False, date_to=False):
        date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        date_to = datetime.combine(datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT), datetime.max.time())
        production_list = {}
        #if pdt_id:
           # pdt = self.env['product.product'].search([('id', '=', pdt_id)])
            ######Receipt######
        query2 = """
            SELECT product.id as product_id,
            pt.name as product_name,
            ld.id as locationid,
            ld.complete_name as location_name,
            u.name as uom,
            product.default_code as stock_code,
          
            
                SUM(CASE
                    WHEN (ls.usage in ('supplier','customer','production','transit')) AND sm.state = 'done' THEN product_uom_qty
                END) AS receipt,
                SUM(CASE
                    WHEN (ls.usage = 'inventory') AND sm.state = 'done' THEN product_uom_qty
                END) AS inv_receipt

            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where sm.date>=%s and sm.date<=%s and sm.state='done' and ld.usage = 'internal' and sm.product_id in %s  and ld.id in %s
            group by product.id,sm.state,locationid,product_name,uom
            """
        self.env.cr.execute(query2, [date_from, date_to,tuple(products.ids),tuple(location_objs.ids)])
        sql = self.env.cr.dictfetchall()
        receipts = sorted(sql, key=lambda k: k['product_id'])


        query3 = """
            SELECT product.id as product_id,
            ls.id as locationid,
            ls.complete_name as location_name,
            pt.name as product_name,
            u.name as uom,
            product.default_code as stock_code,
          
                SUM(CASE
                    WHEN (ld.usage in ('supplier','customer','transit')) AND sm.state = 'done' THEN product_uom_qty
                END) AS sales,
                SUM(CASE
                    WHEN (ld.usage = 'production') AND sm.state = 'done' THEN product_uom_qty
                END) AS consume,
                SUM(CASE
                    WHEN (ld.usage = 'inventory') AND sm.state = 'done' THEN product_uom_qty
                END) AS inv_adj

            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where sm.date>=%s and sm.date<=%s and sm.product_id in %s and sm.state='done' and ls.usage = 'internal' and ls.id in %s
            group by product.id,sm.state,locationid,product_name,uom
            """
        self.env.cr.execute(query3, [date_from, date_to,tuple(products.ids),tuple(location_objs.ids)])
        sql = self.env.cr.dictfetchall()
        issues = sorted(sql, key=lambda k: k['product_id'])
        return receipts,issues

    def get_data_all(self, products, location_objs, date_from=False, date_to=False):
        date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        date_to = datetime.combine(datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT), datetime.max.time())

        query2 = """
            SELECT product.id as product_id,
            pt.name as product_name,
            ld.id as locationdestid,
            ld.complete_name as location_dest_name,
            ls.id as location_src_id,
            ls.complete_name as location_src_name,
            u.name as uom,
            product.default_code as stock_code,
            SUM(CASE
                    WHEN (ls.usage in ('supplier','customer','production','transit')) AND sml.state = 'done' THEN qty_done
                END) AS receipt,
                SUM(CASE
                    WHEN (ls.usage = 'inventory') AND sml.state = 'done' THEN qty_done
                END) AS inv_receipt,
                
                 SUM(CASE
                    WHEN (ld.usage in ('supplier','customer','transit')) AND sml.state = 'done' THEN qty_done
                END) AS sales,
                SUM(CASE
                    WHEN (ld.usage = 'production') AND sml.state = 'done' THEN qty_done
                END) AS consume,
                SUM(CASE
                    WHEN (ld.usage = 'inventory') AND sml.state = 'done' THEN qty_done
                END) AS inv_adj
                
            
            from stock_move_line as sml
            LEFT JOIN stock_location ls on (ls.id=sml.location_id)
            LEFT JOIN stock_location ld on (ld.id=sml.location_dest_id)
            LEFT JOIN product_product product ON (sml.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sml.product_uom_id)
            where sml.date>=%s and sml.date<=%s and sml.state='done'  and ld.usage = 'internal' and ls.usage='internal' and sml.product_id in %s  and ld.id in %s or ls.id in %s
            group by product.id,sml.state,locationdestid,location_src_id,product_name,uom,qty_done
            """


        self.env.cr.execute(query2, [date_from, date_to, tuple(products.ids), tuple(location_objs.ids),tuple(location_objs.ids)])
        sql = self.env.cr.dictfetchall()
        moves = sorted(sql, key=lambda k: k['product_id'])


        return moves

    def get_opening_data(self, pdt_id, date_from=False,location_id=False):
        date_from = datetime.combine(datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
        opening_list = {}
        if pdt_id:
            pdt = self.env['product.product'].search([('id', '=', pdt_id)])
            #acc_id = pdt.categ_id.property_stock_valuation_account_id.id
            ######Opening Balance######
            query = """
                SELECT product.id as product_id,
                    product.default_code as stock_code,
                    SUM(sm.product_uom_qty) as opening,
                    COUNT(*) as count_val
                FROM stock_move as sm
                LEFT JOIN product_product product ON (sm.product_id = product.id)
                LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
                LEFT JOIN stock_location stloac ON (sm.location_dest_id = stloac.id)
                WHERE sm.date<=%s and sm.product_id = %s and sm.location_dest_id= %s
                GROUP BY product.id
                """
            self.env.cr.execute(query, [date_from, pdt.id,location_id])
            # """
            # SUM(CASE WHEN acc_move_line.ref  IS NOT NULL THEN acc_move_line.quantity ELSE 0 END) AS opening,
            #
            # """
            sql = self.env.cr.dictfetchall()
            move = sorted(sql, key=lambda k: k['product_id'])
            opening_list.update({pdt.id: {}})
            #stock_code = pdt.default_code or ''
            #product_name = pdt.name or ''
            #product_uom = move[0]['product_uom'] if move else ''
            #product_uom = pdt.uom_id.name
            opening = move[0]['opening'] if move and move[0]['opening'] else 0
            #location=move[0]['location'] if move else None
            #opening_cost = move[0]['opening_cost'] if move and move[0]['opening_cost'] else 0
            #opening_list[pdt.id]['stock_code'] = stock_code
            #opening_list[pdt.id]['product_name'] = product_name
            #opening_list[pdt.id]['product_uom'] = product_uom
            opening_list[pdt.id]['opening'] = opening
            #opening_list[pdt.id]['location'] = location
            #opening_list[pdt.id]['opening_cost'] = opening_cost
        return opening_list

    def get_closing_data(self, pdt_id, date_to=False,location_id=False):
        date_to = datetime.combine(datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT), datetime.max.time())
        closing_list = {}
        if pdt_id:
            pdt = self.env['product.product'].search([('id', '=', pdt_id)])
            #acc_id = pdt.categ_id.property_stock_valuation_account_id.id
            ######Closing Balance######
            query4 = """
                SELECT product.id as product_id,
                    product.default_code as stock_code,
                    SUM(sm.product_uom_qty) as closing,
                    COUNT(*) as count_val
                FROM stock_move as sm
                LEFT JOIN product_product product ON (sm.product_id = product.id)
                LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
                WHERE sm.date<=%s and sm.product_id = %s and sm.location_dest_id= %s
                GROUP BY product.id
                """
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
            #product_uom = move[0]['product_uom'] if move else ''
            #product_uom = pdt.uom_id.name
            closing = move[0]['closing'] if move and move[0]['closing'] else 0
            #closing_cost = move[0]['closing_cost'] if move and move[0]['closing_cost'] else 0

            #closing_list[pdt.id]['stock_code'] = stock_code
            #closing_list[pdt.id]['product_name'] = product_name
            #closing_list[pdt.id]['product_uom'] = product_uom
            closing_list[pdt.id]['closing'] = closing
            #closing_list[pdt.id]['closing_cost'] = closing_cost
            #if pdt.product_tmpl_id.id == 1193:
                #print("kkkkkk",move[0]['count_val'],pdt.name)
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
                END) AS inv_receipt
                
            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where sm.date>%s and sm.date<=%s and sm.product_id = %s and sm.state='done' and ld.usage = 'internal' and ld.id= %s
            group by product.id,sm.state
            """
            self.env.cr.execute(query2, [date_from,date_to, pdt.id,location_id])
            sql = self.env.cr.dictfetchall()
            receipts = sorted(sql, key=lambda k: k['product_id'])

            inv_receipt = receipts[0]['inv_receipt'] if receipts and receipts[0]['inv_receipt'] else 0
            receipt_receipt = receipts[0]['receipt'] if receipts and receipts[0]['receipt'] else 0

            #if receipts and not production_list[pdt.id]['product_uom']:
            #    product_uom = receipts[0]['product_uom']
            #product_uom = receipts[0]['product_uom'] if receipts else ''
            #receipts_cost = receipts[0]['receipts_cost'] if receipts and receipts[0]['receipts_cost'] else 0
            production_list.update({pdt.id: {}})
            production_list[pdt.id]['inv_receipt']=inv_receipt
            production_list[pdt.id]['receipt']=receipt_receipt
            #production_list[pdt.id]['product_uom']=product_uom
            #production_list[pdt.id]['receipts_cost'] = receipts_cost
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
                END) AS inv_adj
                
            from stock_move as sm
            LEFT JOIN stock_location ls on (ls.id=sm.location_id)
            LEFT JOIN stock_location ld on (ld.id=sm.location_dest_id)
            LEFT JOIN product_product product ON (sm.product_id = product.id)
            LEFT JOIN product_template pt ON (product.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom u on (u.id=sm.product_uom)
            where sm.date>%s and sm.date<=%s and sm.product_id = %s and sm.state='done' and ls.usage = 'internal' and ls.id= %s
            group by product.id,sm.state
            """
            self.env.cr.execute(query3, [date_from, date_to, pdt.id,location_id])
            sql = self.env.cr.dictfetchall()
            issues = sorted(sql, key=lambda k: k['product_id'])
            sales = issues[0]['sales'] if issues and issues[0]['sales'] else 0
            consume = issues[0]['consume'] if issues and issues[0]['consume'] else 0
            inv_adj = issues[0]['inv_adj'] if issues and issues[0]['inv_adj'] else 0
            #if issues and not production_list[pdt.id]['product_uom']:
            #    product_uom = issues[0]['product_uom']
            #product_uom = issues[0]['product_uom'] if issues else ''
            #issues_cost = issues[0]['issues_cost'] if issues and issues[0]['issues_cost'] else 0
            production_list[pdt.id]['sales'] = sales
            production_list[pdt.id]['consume'] = consume
            production_list[pdt.id]['inv_adj'] = inv_adj
            #production_list[pdt.id]['product_uom'] = product_uom
            #production_list[pdt.id]['issues_cost'] = issues_cost
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
            font_size_8_currency = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8, 'num_format': currency_num_format})
            format41_currency = workbook.add_format({'font_size': 10, 'align': 'left', 'right': True, 'left': True, 'bottom': True, 'top': True,'bold': True, 'num_format': currency_num_format})
            format1 = workbook.add_format({'font_size': 12})
            format10 = workbook.add_format({'font_size': 10, 'align': 'center'})
            format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
            format21 = workbook.add_format({'font_size': 10, 'align': 'center'})
            format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
            format41 = workbook.add_format({'font_size': 8, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
            format42 = workbook.add_format({'font_size': 8, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True})
            format_sign = workbook.add_format({'font_size': 8, 'align': 'left','bold': True,})
            format_sign1 = workbook.add_format({'font_size': 8, 'align': 'left'})


            font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
            red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,'bg_color': 'red'})
            justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
            format3.set_align('center')
            font_size_8.set_align('center')
            justify.set_align('justify')
            format1.set_align('center')
            red_mark.set_align('center')
            sheet.set_column('B:B', 20)
            sheet.set_column('C:C',38)
            sheet.set_column('E:E',35)
            sheet.set_column('F:F', 12)
            sheet.set_column('H:H', 15)
            sheet.set_column('I:I', 15)
            sheet.set_column('O:O', 12)
            sheet.set_column('P:P', 12)

            sheet.merge_range(1,0,1,8, str(self.env.user.company_id.name), format1)
            buf_image = io.BytesIO(base64.b64decode(self.env.user.company_id.logo))
            #sheet.set_column(1, 9, 15)
            sheet.insert_image('B2', "any_name.png", {'image_data': buf_image, 'x_scale': 0.8, 'y_scale': 0.8})
            address_company=[]
            if self.env.user.company_id.street:
                address_company.append('Flat/Shop No. '+self.env.user.company_id.street)
            if self.env.user.company_id.street2:
                address_company.append('Building ' + self.env.user.company_id.street2)
            if self.env.user.company_id.city:
                address_company.append(self.env.user.company_id.city)
            if self.env.user.company_id.zip:
                address_company.append(self.env.user.company_id.zip)
            if self.env.user.company_id.country_id:
                address_company.append(self.env.user.company_id.country_id.name)
            sheet.merge_range(2, 0, 2, 8, str(', '.join(address_company)), format21)
            sheet.merge_range(3,0,3,8, 'Inventory Movement', format10)
            user_date_format = self.env['res.lang']._lang_get(self.env.user.lang).date_format
            startday = datetime.strptime(data['form']['date_from'], DEFAULT_SERVER_DATE_FORMAT).strftime(str(user_date_format))
            endday = datetime.strptime(data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT).strftime(str(user_date_format))
            sheet.merge_range(4, 0, 4, 8,'Period:' + str(startday) + ' to ' + str(endday),format21)
            sheet.write(6, 0, 'SL.No', format41)
            sheet.write(6, 1, 'Product Code', format41)
            sheet.write(6, 2, 'Product Name', format41)
            sheet.write(6, 3, 'UOM', format41)
            sheet.write(6, 4, 'Location', format41)
            sheet.write(6, 5, 'Opening Stock', format41)
            sheet.write(6, 6, 'In', format41)
            sheet.write(6, 7, 'Out', format41)
            sheet.write(6, 8, 'Closing Stock.', format41)
            if not data['form']['date_to']:
                data['form']['date_to'] = ''
            if not data['form']['date_from']:
                data['form']['date_from'] = ''
            row = 7
            if data['form']['location_id']:
                location_objs = self.env['stock.location'].sudo().search([('id','in',(data['form']['location_id']))])
            else:
                location_objs = self.env['stock.location'].sudo().search([('usage','=','internal')])
            if data['form']['categ_ids']:
                categ_objs = self.env['product.category'].sudo().search([('id', 'in', data['form']['categ_ids'])])
            else:
                categ_objs = self.env['product.category'].sudo().search([])
            products = self.env['product.product'].sudo().search([('categ_id', 'in', categ_objs.ids), ('active', '=', True), ('detailed_type', '=', 'product')])
            if products:
                move_opening = self.get_opening_data_all(products,location_objs,data['form']['date_from'])
                stock_data= self.get_stock_data_all(products,location_objs,data['form']['date_from'],data['form']['date_to'])
                move_opening_filtered=[x for x in move_opening if (x['opening']) != None]
                stock_data_in=[x for x in stock_data[0] if (x['receipt'] or x['inv_receipt'] != None)]
                stock_data_out=[x for x in stock_data[1] if (x['sales'] or x['consume'] != None or x['inv_adj']!=None)]
                list_moves=move_opening_filtered+stock_data_in+stock_data_out
                pdt_list=[x['product_id'] for x in list_moves]
                product_final_list = list(dict.fromkeys(pdt_list))
                products_result = self.env['product.product'].sudo().search([('id', 'in', product_final_list)])


                sl_no = 1
                #tmp = defaultdict(list)
                #stock=defaultdict(list)
               # stock_out=defaultdict(list)
                #for item in move_opening+stock_data:
                    #tmp[item['product_id'],item['locationid'], item['product_name'], item['uom'], item['stock_code']].append([item['location_name'], item['opening']])
                #for item in  stock_data:
                    #stock[item['product_id']].append([item['location_name'],item['receipt'] ,item['inv_receipt'],item['sales'],item['consume'],item['inv_adj']])
                #for item in stock_data[1]:
                    #stock_out[item['product_id']].append([item['location_name'],item['sales'],item['consume'],item['inv_adj']])
                #parsed_list = [{'product_id': k, 'data': v} for k, v in tmp.items()]
                #parsed_stock= [{'product_id': k, 'datain_out': v} for k, v in stock.items()]
                #parsed_stock_out= [{'product_id': k, 'dataout': v} for k, v in stock_out.items()]

                #print("parsed_list",parsed_list)
                #print("parsed_stock", parsed_stock)
                #print("parsed_stock_out", parsed_stock_out)
                #print("parsed_stock",parsed_stock_in+parsed_stock_out)
                # date_from = datetime.combine(datetime.strptime(data['form']['date_from'], DEFAULT_SERVER_DATE_FORMAT), datetime.min.time())
                #date_to = datetime.combine(datetime.strptime(data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT), datetime.max.time())
                #datas = self.get_data_all(products,location_objs,data['form']['date_from'],data['form']['date_to'])
                #print("data",data)
                #for data in datas:
                    #print("data",data)


                for product in products_result:
                    for location in location_objs:
                        if list_moves:
                            close_stock = 0
                            opening = 0
                            receipt = 0
                            inv_receipt = 0
                            sales = 0
                            consume = 0
                            inv_adj = 0
                            for item in list_moves:
                                #print("item",item)
                                if item.get('product_id')==product.id and item.get('locationid')==location.id:
                                    sheet.write(row, 0, sl_no, font_size_8)
                                    sheet.write(row, 1, product.default_code, font_size_8)
                                    sheet.write(row, 2, product.name, font_size_8)
                                    sheet.write(row, 3, product.uom_id.name, font_size_8)
                                    sheet.write(row, 4, location.complete_name, font_size_8)
                                    if item.get('opening'):
                                        opening+=item.get('opening') if item.get('opening') else 0
                                        sheet.write(row, 5, opening, font_size_8)
                                        close_stock += (item.get('opening') if item.get('opening') else 0 )
                                    # else:
                                    #     sheet.write(row, 5,0, font_size_8)
                                    if item.get('receipt') or item.get('inv_receipt'):
                                        receipt +=item.get('receipt') if item.get('receipt') else 0
                                        inv_receipt += item.get('inv_receipt') if item.get('inv_receipt') else 0
                                        sheet.write(row, 6, receipt + inv_receipt, font_size_8)
                                        close_stock += (receipt + inv_receipt)
                                    else:
                                        sheet.write(row, 6,0, font_size_8)

                                    if item.get('sales') or item.get('consume') or item.get('inv_adj'):
                                        sales += item.get('sales') if item.get('sales') else 0
                                        consume += item.get('consume') if item.get('consume') else 0
                                        inv_adj += item.get('inv_adj') if item.get('inv_adj') else 0
                                        sheet.write(row, 7, sales + consume + inv_adj, font_size_8)
                                        close_stock -= (sales + consume + inv_adj)
                                    else:
                                        sheet.write(row, 7, 0, font_size_8)
                                    sheet.write(row, 8, close_stock, font_size_8)
                                    #row += 1
                            if close_stock!=0 or opening!=0 or receipt!=0 or inv_receipt!=0 or sales!=0 or consume!=0 or inv_adj!=0:
                                row+=1
                                sl_no += 1
                    #row+=1
                    #sl_no += 1
                        #row += 1
                        #row += 1
                        #sl_no += 1
                        # if  move_opening_filtered:
                        #     for item in move_opening_filtered:
                        #         if item.get('product_id')==product.id and item.get('locationid')==location.id:
                        #             sheet.write(row, 4, location.complete_name, font_size_8)
                        #             sheet.write(row, 5, item.get('opening') if item.get('opening') else 0, font_size_8)
                        #             close_stock += (item.get('opening') if item.get('opening') else 0)
                        # if stock_data_in:
                        #     for item in stock_data_in:
                        #         if item.get('product_id') == product.id and item.get('locationid') == location.id:
                        #             receipt = item.get('receipt') if item.get('receipt') else 0
                        #             inv_receipt = item.get('inv_receipt') if item.get('inv_receipt') else 0
                        #             sheet.write(row, 4, location.complete_name, font_size_8)
                        #             sheet.write(row, 6, receipt + inv_receipt, font_size_8)
                        #             close_stock += (receipt + inv_receipt)
                        # if stock_data_out:
                        #     for item in stock_data_out:
                        #         if item.get('product_id') == product.id and item.get('locationid') == location.id:
                        #             sales = item.get('sales') if item.get('sales') else 0
                        #             consume = item.get('consume') if item.get('consume') else 0
                        #             inv_adj = item.get('inv_adj') if item.get('inv_adj') else 0
                        #             sheet.write(row, 4, location.complete_name, font_size_8)
                        #             sheet.write(row, 7, sales + consume + inv_adj, font_size_8)
                        #             close_stock -= (sales + consume + inv_adj)
                        # sheet.write(row, 8, close_stock, font_size_8)
                        #row+=1




                        # if move_opening_filtered:
                        #     for move_open in move_opening_filtered:
                        #         if move_open.get('product_id')==product.id and move_open.get('locationid')==location.id:
                        #             sheet.write(row, 5, move_open.get('opening'), font_size_8)
                        #             close_stock += (move_open.get('opening') if move_open.get('opening') else 0 )
                        #             #else:
                        #                 #sheet.write(row, 5, 0, font_size_8)
                        #         #else:
                        #             #sheet.write(row, 5, 0, font_size_8)
                        # #else:
                        #     #sheet.write(row, 5, 0, font_size_8)
                        # if stock_data_in:
                        #     for invalue in stock_data_in:
                        #         if invalue.get('product_id')==product.id and invalue.get('locationid')==location.id:
                        #             receipt=invalue.get('receipt') if invalue.get('receipt')  else 0
                        #             inv_receipt=invalue.get('inv_receipt') if invalue.get('inv_receipt') else 0
                        #             sheet.write(row, 6,receipt+inv_receipt ,font_size_8)
                        #             close_stock +=(receipt + inv_receipt)
                        #
                        #         #else:
                        #             #sheet.write(row, 6, 0, font_size_8)
                        # #else:
                        #     #sheet.write(row, 6, 0, font_size_8)
                        # if stock_data_out:
                        #     for out_value in stock_data_out:
                        #         if out_value.get('product_id')==product.id and out_value.get('locationid')==location.id:
                        #             sales = out_value.get('sales') if out_value.get('sales') else 0
                        #             consume=out_value.get('consume') if out_value.get('consume') else 0
                        #             inv_adj=out_value.get('inv_adj') if out_value.get('inv_adj') else 0
                        #             sheet.write(row, 7,sales+consume+inv_adj, font_size_8)
                        #             close_stock -= (sales + consume + inv_adj)
                        #         #else:
                        #             #sheet.write(row, 7, 0, font_size_8)
                        #else:
                            #sheet.write(row, 7, 0, font_size_8)
                        # sheet.write(row, 8, close_stock, font_size_8)
                        # row += 1
                    #sl_no += 1

            # sl_no = 1
            # for product in products:
            #     sheet.write(row, 0, sl_no, font_size_8)
            #     sheet.write(row, 1, product.default_code, font_size_8)
            #     sheet.write(row, 2, product.name, font_size_8)
            #     sheet.write(row, 3, product.uom_id.name,font_size_8)
            #     for location in location_objs:
            #         moves = self.get_opening_data(product.id, data['form']['date_from'],location.id)
            #         #close_moves = self.get_closing_data(product.id, data['form']['date_to'],location.id)
            #         sheet.write(row, 4, location.complete_name, font_size_8)
            #         sheet.write(row, 5, moves[product.id]['opening'], font_size_8)
            #         close_stock_open=moves[product.id]['opening']
            #         moves = self.get_stock_data(product.id,data['form']['date_from'],data['form']['date_to'],location.id)
            #         sheet.write(row, 6, moves[product.id]['inv_receipt'] + moves[product.id]['receipt'], font_size_8)
            #         sheet.write(row, 7, moves[product.id]['sales'] + moves[product.id]['consume'] + moves[product.id]['inv_adj'], font_size_8)
            #         close_stock=close_stock_open+moves[product.id]['inv_receipt'] + moves[product.id]['receipt']-moves[product.id]['sales'] + moves[product.id]['consume'] + moves[product.id]['inv_adj']
            #         sheet.write(row, 8,  close_stock, font_size_8)
            #         #total_close_stock += close_moves[product.id]['closing']
            #         row+=1
            #     sl_no+=1
            # else:
            #     for categ in self.env['product.category'].sudo().search([]):
            #         products = self.get_product_list(categ.id)
            #         for product in products:
            #             sheet.write(row, 0, sl_no, font_size_8)
            #             sheet.write(row, 1, product.default_code, font_size_8)
            #             sheet.write(row, 2, product.name, font_size_8)
            #             sheet.write(row, 3, product.uom_id.name, font_size_8)
            #             for location in location_objs:
            #                 moves = self.get_opening_data(product.id, data['form']['date_from'],location.id)
            #                 close_moves = self.get_closing_data(product.id, data['form']['date_to'],location.id)
            #                 sheet.write(row, 4, location.complete_name, font_size_8)
            #                 sheet.write(row, 5, moves[product.id]['opening'], font_size_8)
            #                 close_stock_open=moves[product.id]['opening']
            #                 moves = self.get_stock_data(product.id,data['form']['date_from'],data['form']['date_to'],location.id)
            #                 sheet.write(row, 6, moves[product.id]['inv_receipt'] + moves[product.id]['receipt'], font_size_8)
            #                 sheet.write(row, 7, moves[product.id]['sales'] + moves[product.id]['consume'] + moves[product.id]['inv_adj'], font_size_8)
            #                 close_stock=close_stock_open+moves[product.id]['inv_receipt'] + moves[product.id]['receipt']-moves[product.id]['sales'] + moves[product.id]['consume'] + moves[product.id]['inv_adj']
            #                 sheet.write(row, 8,  close_stock, font_size_8)
            #                 #total_close_stock += close_moves[product.id]['closing']
            #                 row+=1
            #             sl_no += 1
            sheet.write(row + 3, 1, "Reviewed By", format_sign)
            sheet.write(row + 4, 1, "Store Supervisor", format_sign1)
            sheet.write(row + 3, 8, "Approved By", format_sign)
            sheet.write(row + 4, 8, "Store Manager", format_sign1)
        except Exception as e:
            raise UserError("Error:-"+str(e))


class StockMoveReport(models.TransientModel):
    _name = "stock_move.reports"
    _description = "Production Report"

    date_to = fields.Date(string='Date To', required=True)
    date_from = fields.Date(string='Date From', required=True)
    categ_ids = fields.Many2many('product.category', 'production_pdt_category_rel', 'production_id', 'category_id', string='Product Categories')
    #company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,default=lambda self: self.env.company)
    #currency_id = fields.Many2one('res.currency', related="company_id.currency_id", required=True, readonly=False,string='Currency', help="Main currency of the company.")
    location_id=fields.Many2many('stock.location',string="Location",domain=[('usage','=','internal')])

    def excel_report(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'stock.move'
        datas['form'] = self.read()[0]
        report_xml_id = self.env.ref('aljaser_stock_movement_report_ext.report_xlsx_production_report')
        report_xml_id.report_file = 'Production Report'
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('aljaser_stock_movement_report_ext.report_xlsx_production_report').with_context(discard_logo_check=True).report_action(self, data=datas)
