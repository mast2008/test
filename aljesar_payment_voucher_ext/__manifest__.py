# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
    
{
    'name': 'Payment Voucher customization',
    'version': '15.0.1.0.1',
    'category': 'Accounting/Accounting',
    'summary': 'Cheque and Payment Voucher customization',
    'author': 'Mast-IT Bahrain',
    'description': """
Ticket: Cheque and Payment Voucher customization (#2246)
    """,
    'depends': ['account'],
    'data': [
        'report/report_payment_receipt_templates.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}

