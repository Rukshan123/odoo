from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Add a field  if the price was manually set
    price_manually_set = fields.Boolean(
        string='Price Manually Set',
        default=False,
        help='Indicates if the unit price was manually set by the user'
    )

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        """Override to prevent automatic price computation when price is manually set"""
        for line in self:
            # If price was manually set, skip automatic computation completely
            if line.price_manually_set and line.price_unit > 0:
                # Only compute date_planned and name, skip price_unit
                if not line.product_id or line.invoice_lines or not line.company_id:
                    continue

                params = line._get_select_sellers_params()
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(
                        line),
                    uom_id=line.product_uom,
                    params=params)

                if seller or not line.date_planned:
                    line.date_planned = line._get_date_planned(seller).strftime('%Y-%m-%d %H:%M:%S')

                # Only update name if needed
                if not line.name:
                    product_ctx = {'seller_id': seller.id if seller else None, 'lang': self.env.lang}
                    line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

                continue

            # Call the original method for normal computation
            super(PurchaseOrderLine, line)._compute_price_unit_and_date_planned_and_name()

    def write(self, values):
        """Override write to track manual price changes and prevent modifications"""
        for line in self:
            # Check if trying to modify a manually set price
            if 'price_unit' in values and line.price_manually_set:
                raise UserError(_(
                    "Cannot modify unit price. The price has been manually set and is locked. "
                    "Current price: %s" % line.price_unit
                ))

            # Mark price as manually set if it's being changed and not computed
            if 'price_unit' in values and not self.env.context.get('skip_price_lock'):
                values['price_manually_set'] = True

        return super(PurchaseOrderLine, self).write(values)

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

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """Prevent automatic price recomputation when quantity changes if price was manually set"""
        if self.price_manually_set and self.price_unit > 0:
            return

    @api.onchange('product_uom')
    def _onchange_product_uom(self):
        """Prevent automatic price recomputation when UoM changes if price was manually set"""
        if self.price_manually_set and self.price_unit > 0:
            return

    def create(self, vals_list):
        """Override create to mark price as manually set if provided"""
        for vals in vals_list:
            if vals.get('price_unit', 0) > 0:
                vals['price_manually_set'] = True
        return super(PurchaseOrderLine, self).create(vals_list)