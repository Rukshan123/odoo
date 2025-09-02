{
    'name': ' Price Lock',
    'version': '18.0.1.0',
    'category': 'Purchase',
    'summary': 'Lock unit price in purchase orders after manual entry',
    'description': """
        This module locks the unit price field in purchase order lines after it has been manually set.
        Once a unit price is manually entered and saved, it cannot be changed, edited, or removed under any circumstances.
    """,
    'author': 'hatchyard',
    'website': 'https://www.hatchyard.com',
    'depends': ['purchase', 'sale'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}