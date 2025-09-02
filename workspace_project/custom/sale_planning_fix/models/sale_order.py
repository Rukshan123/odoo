from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    planning_first_sale_line_id = fields.Many2one(
        'sale.order.line', 
        string='First Planning Sale Line',
        help="First sale order line related to planning",
        copy=False
    )

