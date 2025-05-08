{
    'name': 'Stock Check No Negative - POS',
    'version': '15.0.0.1',
    'category': 'Point Of Sale',
    'depends': ['stock_no_negative','point_of_sale'],
    'author': 'Mast Information Technology - Bahrain',
    'data': [
    ],
    'installable': True,
    'assets': {
        'point_of_sale.assets': [
            'stock_no_negative_pos/static/src/js/models.js',
            'stock_no_negative_pos/static/src/js/Screens/ProductScreen/ProductScreen.js',
            'stock_no_negative_pos/static/src/js/Screens/PaymentScreen/PaymentScreen.js',
            'stock_no_negative_pos/static/src/js/db.js'
        ],
    }
}