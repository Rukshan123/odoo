from odoo import models, fields, api, _


class AssetMaintenanceLinkWizard(models.TransientModel):
    _name = 'asset.maintenance.link.wizard'
    _description = 'Link Asset with Maintenance Equipment'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        required=True,
        readonly=True
    )

    asset_id = fields.Many2one(
        'account.asset',
        string='Asset',
        domain=[('state', '=', 'open'), ('maintenance_equipment_id', '=', False)],
        required=True
    )

    serial_number = fields.Char(
        string='Serial Number',
        related='asset_id.serial_number',
        readonly=True
    )

    asset_name = fields.Char(
        string='Asset Name',
        related='asset_id.name',
        readonly=True
    )

    asset_value = fields.Monetary(
        string='Asset Value',
        related='asset_id.original_value',
        readonly=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='asset_id.currency_id',
        readonly=True
    )

    def action_link(self):
        """Link the equipment with the selected asset"""
        self.ensure_one()

        if not self.equipment_id or not self.asset_id:
            return False

        # Link the asset to the equipment
        self.asset_id.maintenance_equipment_id = self.equipment_id.id
        self.equipment_id.asset_id = self.asset_id.id

        # Update equipment fields from asset
        self.equipment_id._update_from_asset(self.asset_id)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Equipment successfully linked with asset.'),
                'type': 'success',
            }
        }