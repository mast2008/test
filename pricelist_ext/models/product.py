# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    barcode_line = fields.One2many('product.barcode.line','product_tmpl_id',string="Barcodes",readonly=True)

    @api.constrains('uom_id')
    def check_multi_barcodes(self):
        for rec in self:
            if not rec.uom_id or not rec.barcode_line:
                continue
            rec.barcode_line.check_uom_id()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode_line = fields.One2many('product.barcode.line', 'product_id', string="Barcodes")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        res = super(ProductProduct,self)._name_search(name,args,operator,limit,name_get_uid)
        if not res:
            res = list(self._search([('barcode_line.barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
        return res

    @api.constrains('barcode')
    def check_barcode(self):
        obj_pbcl = self.env['product.barcode.line']
        for rec in self:
            if not rec.barcode:
                continue
            line = obj_pbcl.search([('product_id','!=',rec.id),
                                    ('barcode','=',rec.barcode)],limit=1)
            if line:
                raise UserError("Barcode '%s' already exist in multi barcode list of product '%s'." % (rec.barcode,line.product_id.display_name))

class ProductBarcode(models.Model):
    _name = "product.barcode.line"
    _description = "Product Barcode Line"
    _rec_name = 'barcode'

    company_id = fields.Many2one('res.company', 'Company',required=True,default=lambda self: self.env.user.company_id.id,copy=False)
    user_id = fields.Many2one('res.users','User',default=lambda self: self.env.user.id,copy=False,required=True)
    barcode = fields.Char(required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True, domain=[('sale_ok', '=', True)], ondelete='cascade')
    uom_id = fields.Many2one('uom.uom',"Unit of Measure", required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', ondelete='cascade')
    price = fields.Float('Price', required=True, digits='Product Price', default=0.0)
    #uom_categ_id = fields.Many2one('uom.category',related='product_tmpl_id.uom_id.category_id')

    _sql_constraints = [
        ('barcode_unique', 'unique(barcode)', "A barcode can only be assigned to one product !")]

    @api.constrains('barcode', 'product_id')
    def check_barcode(self):
        obj_product = self.env['product.product']
        obj_pbl = self.env['product.barcode.line']
        for rec in self:
            if not rec.barcode or not rec.product_id:
                continue
            product = obj_product.search([('id', '!=', rec.product_id.id),
                                        ('barcode', '=', rec.barcode)], limit=1)
            if product:
                raise UserError("Barcode '%s' already assigned to product '%s'." % (rec.barcode, product.display_name))
            #no benefit  - first execute sql always.
            other_pbl = obj_pbl.search([('product_id', '!=', rec.product_id.id),
                                        ('barcode', '=', rec.barcode)], limit=1)
            if other_pbl:
                raise UserError("Barcode '%s' already exist in multi barcode list of product '%s'." % (rec.barcode, other_pbl.product_id.display_name))

    @api.onchange('barcode')
    def onchange_barcode(self):
        if not self.uom_id:
            product = self.get_onchange_product()
            if product:
                self.uom_id = product.uom_id.id
                return {'domain':{'uom_id':[('category_id','=',product.uom_id.category_id.id)]}}

    def get_onchange_product(self):
        product = False
        if self._context.get('default_product_tmpl_id', False):
            product = self.env['product.template'].browse(self._context['default_product_tmpl_id'])
        elif self._context.get('bc_product_id', False):
            product = self.env['product.product'].browse(self._context['bc_product_id'])
        elif self._context.get('bc_product_tmpl_id', False):
            product = self.env['product.template'].browse(self._context['bc_product_tmpl_id'])
        return product

    @api.onchange('barcode')
    def onchange_product_uom_id(self):
        product = self.get_onchange_product()
        if product:
            return {'domain': {'uom_id': [('category_id', '=', product.uom_id.category_id.id)]}}
    
    @api.constrains('uom_id')
    def check_uom_id(self):
        for rec in self:
            if rec.uom_id and rec.product_tmpl_id and \
            rec.uom_id.category_id.id != rec.product_tmpl_id.uom_id.category_id.id:
                raise UserError(_(f"Product Multi Barcode Error !!\n\nYou can't choose different UOM category measures\n\nProduct UOM Category: {rec.product_tmpl_id.uom_id.category_id.name} \n" \
                              f"Barcode UOM Category: {rec.uom_id.category_id.name}\nBarcode: {rec.barcode}"))

    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('product_tmpl_id',False) and \
            not vals.get('product_id',False):
                vals['product_id'] = self.env['product.template'].browse(vals['product_tmpl_id']).product_variant_ids[0].id
            if not vals.get('product_tmpl_id', False) and \
            vals.get('product_id', False):
                vals['product_tmpl_id'] = self.env['product.product'].browse(vals['product_id']).product_tmpl_id.id
            if not vals.get('uom_id',False):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['uom_id'] = product.uom_id.id
        return super(ProductBarcode, self).create(vals_list)

    def get_pos_open(self):
        return self.env['pos.session'].sudo().search_count([('state', '!=', 'closed')])

    def write(self, values):
        if self and \
        values.get('uom_id', False) and \
        self.get_pos_open() and \
        self.filtered(lambda l: l.uom_id.id != values['uom_id']):
            raise UserError(_('You cannot modify a product barcode line unit of measure in point of sale while a session is still opened.'))
        return super(ProductBarcode, self).write(values)

    def unlink(self):
        if self.get_pos_open():
            raise UserError(_('You cannot delete a product barcode line in point of sale while a session is still opened.'))
        return super(ProductBarcode, self).unlink()