from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CreateAssetWizard(models.TransientModel):
    _name = 'create.asset.wizard'
    _description = 'Create Assets from Invoice Line'

    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        required=True,
        help="Invoice line from which to create assets"
    )
    quantity = fields.Integer(
        string='Quantity to Create',
        required=True,
        default=1,
        help="Number of assets to create"
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='invoice_line_id.product_id',
        readonly=True
    )
    product_name = fields.Char(
        string='Product Name',
        related='invoice_line_id.product_id.name',
        readonly=True
    )
    unit_price = fields.Float(
        string='Unit Price',
        related='invoice_line_id.price_unit',
        readonly=True,
        digits='Product Price'
    )

    @api.onchange('invoice_line_id')
    def _onchange_invoice_line(self):
        """Update quantity when invoice line changes"""
        if self.invoice_line_id:
            self.quantity = int(self.invoice_line_id.quantity)

    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError("Quantity must be greater than 0.")
            if record.invoice_line_id and record.quantity > record.invoice_line_id.quantity:
                raise ValidationError("Quantity cannot exceed the invoice line quantity.")

    def action_create_assets(self):
        """Create assets from the invoice line"""
        self.ensure_one()

        if not self.invoice_line_id or self.quantity <= 0:
            raise ValidationError("Invalid invoice line or quantity.")

        # Validate that this is a vendor bill line
        if self.invoice_line_id.move_id.move_type != 'in_invoice':
            raise ValidationError("Assets can only be created from vendor bill lines.")

        assets = self.env['account.asset']

        try:
            for i in range(self.quantity):
                asset_vals = {
                    'name': self.invoice_line_id.name or self.product_id.name,
                    'original_value': self.invoice_line_id.price_subtotal / self.invoice_line_id.quantity,
                    'acquisition_date': self.invoice_line_id.move_id.invoice_date or fields.Date.today(),
                    'invoice_line_id': self.invoice_line_id.id,
                    'invoice_id': self.invoice_line_id.move_id.id,
                    'state': 'draft',
                }

                asset = self.env['account.asset'].create(asset_vals)
                assets |= asset

            # Show success message
            asset_numbers = assets.mapped('asset_number')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Assets Created Successfully',
                    'message': f'{self.quantity} asset(s) created with numbers: {", ".join(asset_numbers)}',
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise ValidationError(f"Error creating assets: {str(e)}")