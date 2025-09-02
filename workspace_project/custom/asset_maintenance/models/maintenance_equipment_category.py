from odoo import models, fields, api, _


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    # Link to asset model
    asset_model_id = fields.Many2one(
        'account.asset',
        string='Asset Model',
        domain=[('state', '=', 'model')],
        help="Linked asset model for this equipment category"
    )

    # Computed fields
    asset_model_name = fields.Char(
        string='Asset Model Name',
        related='asset_model_id.name',
        readonly=True
    )

    linked_assets_count = fields.Integer(
        string='Linked Assets Count',
        compute='_compute_linked_assets_count'
    )

    @api.depends('asset_model_id')
    def _compute_linked_assets_count(self):
        for category in self:
            if category.asset_model_id:
                category.linked_assets_count = self.env['account.asset'].search_count([
                    ('model_id', '=', category.asset_model_id.id),
                    ('state', '=', 'open')
                ])
            else:
                category.linked_assets_count = 0

    @api.onchange('asset_model_id')
    def _onchange_asset_model_id(self):
        """Update category name when asset model changes"""
        if self.asset_model_id:
            self.name = self.asset_model_id.name

    def action_view_linked_assets(self):
        """Action to view assets linked to this category's model"""
        self.ensure_one()

        if not self.asset_model_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked Assets'),
            'res_model': 'account.asset',
            'view_mode': 'tree,form',
            'domain': [
                ('model_id', '=', self.asset_model_id.id),
                ('state', '=', 'open')
            ],
            'context': {},
        }