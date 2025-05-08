{
    'name': 'Credit Limit Exemption Approval',
    'category': 'Sales',
    'version': '15.0.0.1',
    'author': 'Mast Information Technology - Bahrain',
    'summary': "Credit limit exceed approval.T#2002",
    'depends': ['partner_credit_limit'],
    # 'website': 'http://www.mast-it.com',
    'data': [
            'views/sale_views.xml',
            'views/ptnr_cl_exempt_views.xml',
            'views/res_config_settings_views.xml',
            'views/res_partner_views.xml',
            'security/ir.model.access.csv',
            'security/security.xml',
            'data/mail_data.xml',
             ],
    'installable': True,
    'license': 'LGPL-3'
}
