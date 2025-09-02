{
    'name': 'Sale Planning Fix',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Fix for missing planning_first_sale_line_id field',
    'description': """
        This addon adds the missing planning_first_sale_line_id field to the sale.order model
        to fix the Owl lifecycle error.
    """,
    'depends': ['sale'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}

