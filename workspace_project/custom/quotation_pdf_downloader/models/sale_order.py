from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_download_quotation_pdf(self):
        """
        Action to download quotation as PDF using custom template
        """
        self.ensure_one()
        
        # Generate the PDF report
        report_action = self.env.ref('quotation_pdf_downloader.action_report_custom_quotation')
        if not report_action:
            raise UserError("Custom quotation report not found. Please check module installation.")
        
        # Return the report action
        return report_action.report_action(self)


