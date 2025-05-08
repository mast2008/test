# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models
from itertools import groupby

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    #pos stock_picking
    def _prepare_stock_move_vals(self, first_line, order_lines):
        res = super(StockPicking,self)._prepare_stock_move_vals(first_line, order_lines)
        res['product_uom'] = first_line.product_uom_id.id or first_line.product_id.uom_id.id
        return res

    def _create_move_from_pos_order_lines(self, lines):
        #full replaced
        #extra key - l.product_uom_id.id in lines_by_product
        self.ensure_one()
        lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: (l.product_id.id,l.product_uom_id.id))
        move_vals = []
        for dummy, olines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*olines)
            move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))
        moves = self.env['stock.move'].create(move_vals)
        confirmed_moves = moves._action_confirm()
        confirmed_moves._add_mls_related_to_order(lines, are_qties_done=True)