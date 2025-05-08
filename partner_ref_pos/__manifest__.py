# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Customer Reference In POS',
    'version': '1.0',
    'category': 'Point of sale',
    'author':'Mast Information Technology - Bahrain',
    'description': "module for showing customer reference in point of sale",
    'depends': ['point_of_sale','base'],
    'website': 'http://www.mast-it.com',
    'data': ['views/templates.xml'
             ],
    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/*.xml'],
    
}
