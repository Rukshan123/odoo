# -*- coding: utf-8 -*-
"""
Pre-migration script for hy_cheque_book_management module upgrade to Odoo 18.0.1.0
"""

def migrate(cr, version):
    """
    Pre-migration script for hy_cheque_book_management module
    """
    # Ensure sh_pdc module is upgraded first since this depends on it
    # Add any cheque book specific pre-migration logic here
    
    print("Pre-migration completed for hy_cheque_book_management module") 