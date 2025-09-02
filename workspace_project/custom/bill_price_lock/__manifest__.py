# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Bill Price Lock',
    'version': '18.0.1.0',
    'category': 'Accounting',
    'summary': 'Lock price field when purchase order is selected in bills ',
    'description': """
        This module makes the price field read-only in bill lines when a purchase order 
        is selected in the Auto-Complete field.
    """,
    'author': 'hatchyard',
    'website': 'https://www.hatchyard.com',
    'depends': ['account', 'purchase'],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
} 