from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Add a field to  price was manually set
    price_manually_set = fields.Boolean(
        string='Price Manually Set',
        default=False,
        help='Indicates if the unit price was manually set by the user'
    )

    @api.depends('product_id', 'product_uom_id')
    def _compute_price_unit(self):
        """Override to prevent automatic price computation when price is manually set"""
        for line in self:
            # If price was manually set, skip automatic computation
            if line.price_manually_set and line.price_unit > 0:
                continue


            super(AccountMoveLine, line)._compute_price_unit()

    def write(self, values):
        """Override write to track manual price changes and prevent modifications"""
        for line in self:
            # Check if trying to modify a manually set price
            if 'price_unit' in values and line.price_manually_set:
                raise UserError(_(
                    "Cannot modify unit price. The price has been manually set and is locked. "
                    "Current price: %s" % line.price_unit
                ))


            if 'price_unit' in values and not self.env.context.get('skip_price_lock'):
                values['price_manually_set'] = True

        return super(AccountMoveLine, self).write(values)

    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        """Mark price as manually set when user changes it"""
        if self.price_unit > 0:
            self.price_manually_set = True

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Reset price_manually_set when product changes"""
        if self.product_id:
            self.price_manually_set = False

    def create(self, vals_list):
        """Override create to mark price as manually set if provided"""
        for vals in vals_list:
            if vals.get('price_unit', 0) > 0:
                vals['price_manually_set'] = True
        return super(AccountMoveLine, self).create(vals_list)