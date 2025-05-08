# See LICENSE file for full copyright and licensing details.

{
    'name': 'POS Default Customer',
    'category': 'POS',
    'version': '15.0.1.0.1',
    'images': ['static/description/icon.png'],
    'description': '',
    'author': 'Mast',
    'depends': ['point_of_sale'],
    'data': [
        #'views/assets.xml',
        'views/pos_config_view.xml',

    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_default_customer/static/src/js/get_customer.js',
            'pos_default_customer/static/src/js/PaymentScreen.js',
            'pos_default_customer/static/src/js/models.js',

        ],

    },
    'demo': [

    ],
    'images': [],
    'application': True,
    'installable': True,

}
