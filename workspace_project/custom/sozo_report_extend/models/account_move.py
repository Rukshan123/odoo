from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_name_invoice_report(self):
        name = super()._get_name_invoice_report()
        # Use our customized invoice report by default
        return 'sozo_report_extend.report_invoice_document'


