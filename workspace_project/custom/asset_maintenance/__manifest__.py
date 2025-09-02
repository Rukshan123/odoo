{
    'name': 'Asset Equipment Link',
    'version': '18.0.1.0',
    'category': 'Accounting/Asset Management',
    'summary': 'Link assets with maintenance equipment',
    'description': """
        This module links accounting assets with maintenance equipment.
        Features:
        - Auto-create maintenance equipment when assets are created from vendor bills
        - Auto-select asset model in equipment category
        - Auto-select vendor from bills in equipment product information
        - Sync cost between asset and equipment
        - Add serial number and warranty expiration date to assets and asset models
        - Auto-populate equipment fields from asset data
        - Default serial number and warranty date from asset models
        - Auto-fill asset serial number and warranty date from maintenance equipment product information
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'account_asset',
        'maintenance',
        'purchase',
    ],
    'data': [
        #'security/ir.model.access.csv',
        #'data/ir_sequence_data.xml',
        'views/account_asset_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/maintenance_equipment_category_views.xml',
        'wizard/asset_maintenance_link_wizard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}