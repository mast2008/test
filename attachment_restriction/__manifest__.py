{
    'name': 'Attachment Restriction',
    'category': 'Base',
    'version': '15.0.0.1',
    'author': 'Mast Information Technology - Bahrain',
    # 'description': "Specific user group can only delete attachment. T#2090",
    'summary': "Specific user group can only delete attachments. User group 'Allow to Delete Attachments'. T#2090",
    'depends': ['base'],
    # 'website': 'http://www.mast-it.com',
    'data': [
            'security/security.xml',
             ],
    'installable': True,
}
