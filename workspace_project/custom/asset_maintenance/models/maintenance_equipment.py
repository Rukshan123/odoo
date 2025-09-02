from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    # Link to asset
    asset_id = fields.Many2one(
        'account.asset',
        string='Linked Asset',
        copy=False,
        help="Linked accounting asset"
    )

    # Computed fields
    has_linked_asset = fields.Boolean(
        string='Has Linked Asset',
        compute='_compute_has_linked_asset',
        store=True
    )

    asset_name = fields.Char(
        string='Asset Name',
        related='asset_id.name',
        readonly=True
    )

    asset_code = fields.Char(
        string='Asset ID',
        compute='_compute_asset_code',
        readonly=True
    )

    def _compute_asset_code(self):
        for equipment in self:
            code_value = False
            asset = equipment.asset_id
            if asset:
                # Prefer custom asset_number if available (e.g., FF/003)
                if 'asset_number' in asset._fields:
                    code_value = asset.asset_number
                # Fallbacks for other implementations
                elif 'code' in asset._fields:
                    code_value = asset.code
                elif 'reference' in asset._fields:
                    code_value = asset.reference
            equipment.asset_code = code_value

    @api.depends('asset_id')
    def _compute_has_linked_asset(self):
        for equipment in self:
            equipment.has_linked_asset = bool(equipment.asset_id)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-link with asset if possible"""
        equipments = super().create(vals_list)

        for equipment in equipments:
            equipment._try_link_with_asset()

        return equipments

    def write(self, vals):
        """Override write to update asset if linked"""
        result = super().write(vals)

        for equipment in self:
            if equipment.asset_id:
                equipment._update_linked_asset()

        return result

    def _try_link_with_asset(self):
        """Try to link equipment with existing asset based on serial number"""
        self.ensure_one()

        if self.asset_id or not self.serial_no:
            return

        # Try to find asset with same serial number
        asset = self.env['account.asset'].search([
            ('serial_number', '=', self.serial_no),
            ('state', '=', 'open'),
            ('maintenance_equipment_id', '=', False)
        ], limit=1)

        if asset:
            # Link the asset to this equipment
            asset.maintenance_equipment_id = self.id
            self.asset_id = asset.id

            # Update equipment fields from asset
            self._update_from_asset(asset)

    def _update_from_asset(self, asset):
        """Update equipment fields from asset"""
        self.ensure_one()

        if not asset:
            return

        update_vals = {}

        if not self.name and asset.name:
            update_vals['name'] = asset.name

        if not self.category_id and asset.model_id:
            equipment_category = self._get_equipment_category_from_asset_model(asset.model_id)
            if equipment_category:
                update_vals['category_id'] = equipment_category.id

        if not self.partner_id:
            vendor = self._get_vendor_from_asset(asset)
            if vendor:
                update_vals['partner_id'] = vendor.id

        if not self.partner_ref:
            vendor_ref = self._get_vendor_reference_from_asset(asset)
            if vendor_ref:
                update_vals['partner_ref'] = vendor_ref

        if not self.cost and asset.original_value:
            update_vals['cost'] = asset.original_value

        if not self.warranty_date and asset.warranty_expiration_date:
            update_vals['warranty_date'] = asset.warranty_expiration_date

        if not self.assign_date and asset.acquisition_date:
            update_vals['assign_date'] = asset.acquisition_date

        # Auto-populate serial number from asset if not set
        if not self.serial_no and asset.serial_number:
            update_vals['serial_no'] = asset.serial_number

        if update_vals:
            self.write(update_vals)

    def _update_linked_asset(self):
        """Update linked asset from equipment changes"""
        self.ensure_one()

        if not self.asset_id:
            return

        asset = self.asset_id
        update_vals = {}

        # Update asset fields that might have changed
        if self.serial_no != asset.serial_number:
            update_vals['serial_number'] = self.serial_no

        # Fix: Use warranty_date instead of warranty_expiration_date
        if self.warranty_date != asset.warranty_expiration_date:
            update_vals['warranty_expiration_date'] = self.warranty_date

        if update_vals:
            asset.write(update_vals)

    def _get_equipment_category_from_asset_model(self, asset_model):
        """Get or create equipment category from asset model"""
        if not asset_model:
            return False

        # Try to find existing category
        category = self.env['maintenance.equipment.category'].search([
            ('name', '=', asset_model.name)
        ], limit=1)

        if not category:
            # Create new category
            category = self.env['maintenance.equipment.category'].create({
                'name': asset_model.name,
                'technician_user_id': self.env.user.id,
            })

        return category

    def _get_vendor_from_asset(self, asset):
        """Get vendor from asset's original move lines"""
        if not asset:
            return False

        for move_line in asset.original_move_line_ids:
            if move_line.move_id.partner_id:
                return move_line.move_id.partner_id

        return False

    def _get_vendor_reference_from_asset(self, asset):
        """Get vendor reference from asset's original move lines"""
        if not asset:
            return False

        for move_line in asset.original_move_line_ids:
            if move_line.move_id.ref or move_line.move_id.name:
                return move_line.move_id.ref or move_line.move_id.name

        return False

    def action_view_linked_asset(self):
        """Action to view linked asset"""
        self.ensure_one()

        if not self.asset_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Linked Asset'),
            'res_model': 'account.asset',
            'res_id': self.asset_id.id,
            'view_mode': 'form',
            'target': 'current',
        }