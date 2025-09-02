{
    'name': 'Quotation PDF Downloader',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Download quotations as PDF with custom template',
    'description': """
        This module adds a new action button to download quotations as PDF.
        When users go to the sales module and click on a quotation, they will see
        a new "Download Quotation" option in the print menu that generates a
        professional quotation PDF based on the provided template.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['sale', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'report/simple_quotation_template.xml',
        'report/quotation_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
