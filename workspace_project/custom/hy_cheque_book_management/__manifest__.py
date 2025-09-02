# -*- coding: utf-8 -*-
{
    "name": "PDC Cheque Number Management",
    "author": "Hatchyard(pvt)LTD",
    "sequence": 3,
    "website": "https://hatchyard.io/",
    "support": "https://hatchyard.io/",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": "Cheque Number Management for PDC Payments, Manage Multiple Cheque Books per Bank Account, Automatic Cheque Reference Generation, Track Used Cheque Numbers",
    "description": """
PDC Cheque Number Management Module

This module extends the PDC (Post Dated Cheque) functionality with comprehensive cheque number management:

Features:
- Create and manage multiple cheque books for different bank accounts
- Each bank account can have multiple cheque books with user-defined ordering
- Define first and last cheque numbers for each cheque book
- Automatic cheque number assignment when creating PDC payments
- Automatic cheque reference generation (CHQ-{ChequeBook}-{ChequeNumber})
- Track used and available cheque numbers
- Prevent duplicate cheque number usage
- Validation to ensure cheque numbers are within defined range
- User-friendly reordering of cheque books via drag-and-drop
- Detailed reporting of cheque usage
- Integration with existing PDC payment workflow

Benefits:
- Supports multiple cheque books per bank account
- User can control which cheque book to use first
- Prevents duplicate cheque numbers
- Automatic cheque reference generation
- Reduces manual work with automatic assignment
- Complete audit trail of cheque usage
- Better organization and tracking
- Enhanced reporting capabilities
- Flexible cheque book management
    """,
    "version": "18.0.1.0",
    "depends": [
        "account",
        "sh_pdc",
    ],
    "data": [
        "data/ir_sequence.xml",
        "security/ir.model.access.csv",
        "security/ir.rule.csv",
        "views/cheque_book_views.xml",
        "views/sh_pdc.xml",
        "wizard/cheque_book_wizard_views.xml",
        "report/cheque_report_template.xml",
    ],
    "images": [],
    "application": False,
    "auto_install": False,
    "installable": True,
    "price": 0,
} 