# See LICENSE file for full copyright and licensing details.

{
    'name': 'Partner Credit Limit',
    'version': '15.0.1.0.0',
    'category': 'Partner',
    'license': 'AGPL-3',
    'author': 'Mast-IT Bahrain',
    'website': 'http://www.mast-it.com',
    'summary': 'Set credit limit warning',
    'depends': [
        'sale_management',
    ],
    'data': [
        'security/security.xml',
        'views/partner_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
