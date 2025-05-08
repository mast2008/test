# -*- coding: utf-8 -*-
{
    "name": "Cloud Storage Solutions",
    "version": "17.0.1.3.32",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/17.0/cloud-storage-solutions-16-0-cloud-base-739",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "mail"
    ],
    "data": [
        "security/security.xml",
        "data/data.xml",
        "data/cron.xml",
        "data/mass_actions.xml",
        "security/ir.model.access.csv",
        "views/clouds_log.xml",
        "views/sync_model.xml",
        "views/clouds_client.xml",
        "views/ir_attachment.xml",
        "views/clouds_folder.xml",
        "views/clouds_queue.xml",
        "views/clouds_tag.xml",
        "views/res_config_settings.xml",
        "wizard/mass_attachment_update.xml",
        "wizard/mass_update_tag.xml",
        "views/menu.xml",
        "views/templates.xml"
    ],
    "assets": {
        "web.assets_backend": [
                "cloud_base/static/src/views/kanban/*.scss",
                "cloud_base/static/src/views/kanban/*.xml",
                "cloud_base/static/src/views/kanban/*.js",
                "cloud_base/static/src/views/search/*.js",
                "cloud_base/static/src/views/list/*.js",
                "cloud_base/static/src/views/fields/jstree_widget/*.xml",
                "cloud_base/static/src/views/fields/jstree_widget/*.js",
                "cloud_base/static/src/views/fields/rule_parent/*.xml",
                "cloud_base/static/src/views/fields/rule_parent/*.js",
                "cloud_base/static/src/models/attachment/*.js",
                "cloud_base/static/src/models/attachment_list/*.js",
                "cloud_base/static/src/models/attachment_card/*.js",
                "cloud_base/static/src/models/thread/*.js",
                "cloud_base/static/src/models/file_uploader/*.js",
                "cloud_base/static/src/models/activity/*.js",
                "cloud_base/static/src/components/cloud_manager/*.xml",
                "cloud_base/static/src/components/cloud_manager/*.js",
                "cloud_base/static/src/components/cloud_jstree_container/*.xml",
                "cloud_base/static/src/components/cloud_jstree_container/*.js",
                "cloud_base/static/src/components/node_jstree_container/*.xml",
                "cloud_base/static/src/components/node_jstree_container/*.js",
                "cloud_base/static/src/components/cloud_navigation/*.xml",
                "cloud_base/static/src/components/cloud_navigation/*.js",
                "cloud_base/static/src/components/cloud_logs/*.xml",
                "cloud_base/static/src/components/cloud_logs/*.js",
                "cloud_base/static/src/components/cloud_logs/*.scss",
                "cloud_base/static/src/components/message_list/*.js",
                "cloud_base/static/src/components/attachment_box/*.xml",
                "cloud_base/static/src/components/attachment_box/*.js",
                "cloud_base/static/src/components/attachment_card/*.xml",
                "cloud_base/static/src/components/chatter_topbar/*.xml"
        ]
},
    "demo": [
        
    ],
    "external_dependencies": {
        "python": [
                "sortedcontainers"
        ]
},
    "summary": "The tool to flexibly structure Odoo attachments in folders and synchronize directories with cloud clients: Google Drive, OneDrive/SharePoint, Nextcloud/ownCloud, and Dropbox. DMS. File Manager. Document management system. Attachments cloud base. Attachments manager. Attachment manager. Two way integration. Bilateral synchronization. Cloud services.",
    "description": """
For the full details look at static/description/index.html
* Features *- Odoo File Manager Interface- Enhanced attachment box - Cloud storage synchronization- &lt;span id=&#34;cloud_base_folder_rules&#34;&gt;Automatic folder structure&lt;/span&gt;- File manager and sync access rights- Use notes
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "379.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=11&ticket_version=17.0&url_type_id=3",
}