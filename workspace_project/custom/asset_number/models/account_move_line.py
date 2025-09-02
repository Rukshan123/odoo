from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def action_create_assets_from_line(self):
        """Action to create assets from invoice line"""
        self.ensure_one()

        # Check if this is a vendor bill line with product and quantity
        if (self.move_id.move_type != 'in_invoice' or
                not self.product_id or
                self.quantity <= 0):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cannot Create Assets',
                    'message': 'Assets can only be created from vendor bill lines with products and quantity > 0.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Create assets using the wizard
        return {
            'name': 'Create Assets',
            'type': 'ir.actions.act_window',
            'res_model': 'create.asset.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_line_id': self.id,
                'default_quantity': int(self.quantity),
            }
        }

    def _create_assets_from_invoice_line(self):
        """Create assets from invoice line based on quantity"""
        for line in self:
            # Only process vendor bills (purchase invoices)
            if line.move_id.move_type != 'in_invoice':
                continue

            # Check if the line has a product and quantity
            if not line.product_id or line.quantity <= 0:
                continue

            # Create assets based on quantity
            for i in range(int(line.quantity)):
                asset_vals = {
                    'name': line.name or line.product_id.name,
                    'original_value': line.price_subtotal / line.quantity,
                    # Divide by quantity for individual asset value
                    'acquisition_date': line.move_id.invoice_date or fields.Date.today(),
                    'invoice_line_id': line.id,
                    'invoice_id': line.move_id.id,
                    'state': 'draft',
                }

                # Create the asset (asset_number will be auto-generated)
                self.env['account.asset'].create(asset_vals)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        """Override to create assets when vendor bill is posted"""
        result = super()._post(soft=soft)

        # Create assets from invoice lines for vendor bills
        # Fix: Iterate through each move to avoid singleton error
        for move in self:
            if move.move_type == 'in_invoice':
                for line in move.invoice_line_ids:
                    line._create_assets_from_invoice_line()

        return result