# -*- coding: utf-8 -*-
{
    'name': "vcls-legal",

    'summary': """
        VCLS customs for legal / contract.""",

    'description': """
    """,

    'author': "VCLS",
    'website': "http://www.voisinconsulting.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.3.3',

    # any module necessary for this one to work correctly
    'depends': [
        'agreement_legal',
        'agreement_sale',
        'agreement_legal_sale',
        'vcls-crm',
        'vcls-invoicing',
        'vcls-contact',
        'vcls_security',
    ],

    # always loaded
    'data': [
        ### VIEWS ###
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/lead_views.xml',
        'views/contact_views.xml',
        'views/agreement.xml',
        'views/sale_views.xml',
    ],
}
