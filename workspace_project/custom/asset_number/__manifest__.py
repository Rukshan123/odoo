# -*- coding: utf-8 -*-
{
    'name': 'Asset Number Auto Generator',
    'version': '18.0.1.0',
    'category': 'Accounting',
    'summary': 'Auto-generate asset numbers and display with asset name',
    'description': 'Auto-generate asset numbers like MV001 for Monitor vehicles and display next to asset name',
    'author': 'Hatchyard',
    'company': 'Hatchyard',
    'maintainer': 'Hatchyard',
    'website': 'https://www.hatchyard.io',
    'depends': [
        'base',
        'account_asset',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_asset_view.xml',
        'views/account_move_line_view.xml',
         #'views/account_shortcode.xml',
        'views/asset_report.xml',
        'wizard/create_asset_wizard_view.xml',
        #'wizard/short_code_wizard.xml',

    ],
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'auto_install': False,
}