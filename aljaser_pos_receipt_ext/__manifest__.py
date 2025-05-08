# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Aljaser POS Custom Receipt',
    'version': '15.0.1',
    'category': 'Point Of Sale',
    'author':'Mast Information Technology - Bahrain',
    'description': """
	By using this module can make a custom receipt.
	""",
    'license': 'Other proprietary',
    'depends': ['base','point_of_sale'],
    'data': [
    ],
    'assets': {
        'point_of_sale.assets': [
            #'aljaser_pos_receipt_ext/static/src/js/invoice_number.js',
            #'aljaser_pos_receipt_ext/static/src/js/payment.js',

            'aljaser_pos_receipt_ext/static/src/js/models.js',

        ],
        'web.assets_qweb': [
            #'aljaser_pos_receipt_ext/static/src/xml/**/*',
            'aljaser_pos_receipt_ext/static/src/xml/pos.xml',
        ],
    },
    'installable': True,
    'application': False,
}
