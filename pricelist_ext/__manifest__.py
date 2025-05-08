# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Pricelist Extension',
    'version': '15.0.0.1',
    'category': 'Sales',
    'author':'Mast Information Technology - Bahrain',
    'summary': "Product multi barcodes - POS",
    'depends': ['product','sale','point_of_sale'],
    #'website': 'http://www.mast-it.com',
    'data': [
            'security/ir.model.access.csv',
            'views/product_pricelist_views.xml',
            'views/product_views.xml',
            'views/pos_order_views.xml',
            'data/data.xml',
             ],
    'assets': {
        'point_of_sale.assets': [
            'pricelist_ext/static/src/js/db.js',
            'pricelist_ext/static/src/js/models.js',
            'pricelist_ext/static/src/js/ProductScreen.js',
            'pricelist_ext/static/src/js/TicketScreen.js',
        ],
        'web.assets_qweb': [
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
    #'qweb': ['static/src/xml/*.xml'],
}
