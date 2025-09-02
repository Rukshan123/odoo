from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    serial_number = fields.Char(
        string='Serial Number',
        copy=False,
        tracking=True,
        help="Serial number of the asset"
    )

    warranty_expiration_date = fields.Date(
        string='Warranty Expiration Date',
        tracking=True,
        help="Warranty expiration date of the asset"
    )

    # Link to maintenance equipment
    maintenance_equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Maintenance Equipment',
        copy=False,
        help="Linked maintenance equipment"
    )

    # Computed fields
    has_maintenance_equipment = fields.Boolean(
        string='Has Maintenance Equipment',
        compute='_compute_has_maintenance_equipment',
        store=True
    )

    @api.depends('maintenance_equipment_id')
    def _compute_has_maintenance_equipment(self):
        for asset in self:
            asset.has_maintenance_equipment = bool(asset.maintenance_equipment_id)

    def _auto_fill_from_maintenance_equipment(self):
        """Auto-fill serial number and warranty date from linked maintenance equipment"""
        self.ensure_one()

        if not self.maintenance_equipment_id:
            return

        equipment = self.maintenance_equipment_id

        # Auto-fill serial number if not already set
        if not self.serial_number and equipment.serial_no:
            self.serial_number = equipment.serial_no

        # Auto-fill warranty date if not already set
        if not self.warranty_expiration_date and equipment.warranty_date:
            self.warranty_expiration_date = equipment.warranty_date

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-create maintenance equipment"""
        assets = super().create(vals_list)

        for asset in assets:
            if asset.state == 'open' and not asset.maintenance_equipment_id:
                asset._create_maintenance_equipment()

        return assets

    def write(self, vals):
        """Override write to update maintenance equipment"""
        result = super().write(vals)

        for asset in self:
            if asset.state == 'open' and not asset.maintenance_equipment_id:
                asset._create_maintenance_equipment()
            elif asset.maintenance_equipment_id:
                asset._update_maintenance_equipment()

        return result

    def _create_maintenance_equipment(self):
        """Create maintenance equipment from asset"""
        self.ensure_one()

        if not self.name or self.state != 'open':
            return False

        # Get vendor and vendor reference from original move lines
        vendor, vendor_ref = self._get_vendor_and_reference_from_move_lines()

        # Get asset model for equipment category
        equipment_category = self._get_equipment_category_from_model()

        equipment_vals = {
            'name': self.name,
            'category_id': equipment_category.id if equipment_category else False,
            'partner_id': vendor.id if vendor else False,
            'partner_ref': vendor_ref,  # Auto-populate vendor reference
            'model': self.model_id.name if self.model_id else '',
            'serial_no': self.serial_number,  # Auto-populate serial number
            'cost': self.original_value,
            'warranty_date': self.warranty_expiration_date,
            'assign_date': self.acquisition_date,
        }

        equipment = self.env['maintenance.equipment'].create(equipment_vals)

        # Link the equipment to the asset
        self.maintenance_equipment_id = equipment.id

        return equipment

    def _update_maintenance_equipment(self):
        """Update maintenance equipment from asset"""
        self.ensure_one()

        if not self.maintenance_equipment_id:
            return

        equipment = self.maintenance_equipment_id

        # Get vendor and vendor reference from original move lines
        vendor, vendor_ref = self._get_vendor_and_reference_from_move_lines()

        # Get asset model for equipment category
        equipment_category = self._get_equipment_category_from_model()

        update_vals = {
            'name': self.name,
            'category_id': equipment_category.id if equipment_category else False,
            'partner_id': vendor.id if vendor else False,
            'partner_ref': vendor_ref,  # Auto-update vendor reference
            'model': self.model_id.name if self.model_id else '',
            'serial_no': self.serial_number,  # Auto-update serial number
            'cost': self.original_value,
            'warranty_date': self.warranty_expiration_date,
            'assign_date': self.acquisition_date,
        }

        equipment.write(update_vals)

    def _get_vendor_and_reference_from_move_lines(self):
        """Get vendor and vendor reference from original move lines"""
        self.ensure_one()

        vendor = False
        vendor_ref = False

        for move_line in self.original_move_line_ids:
            if move_line.move_id.partner_id:
                vendor = move_line.move_id.partner_id
                # Get vendor reference from the move (bill reference)
                vendor_ref = move_line.move_id.ref or move_line.move_id.name
                break

        return vendor, vendor_ref

    def _get_vendor_from_move_lines(self):
        """Get vendor from original move lines (for backward compatibility)"""
        vendor, _ = self._get_vendor_and_reference_from_move_lines()
        return vendor

    def _get_equipment_category_from_model(self):
        """Get equipment category from asset model"""
        self.ensure_one()

        if not self.model_id:
            return False

        #  find existing category with same name as asset model
        category = self.env['maintenance.equipment.category'].search([
            ('name', '=', self.model_id.name)
        ], limit=1)

        if not category:
            # Create new category if it doesn't exist
            category = self.env['maintenance.equipment.category'].create({
                'name': self.model_id.name,
                'technician_user_id': self.env.user.id,
            })

        return category

    def action_view_maintenance_equipment(self):
        """Action to view linked maintenance equipment"""
        self.ensure_one()

        if not self.maintenance_equipment_id:
            return False

        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Equipment'),
            'res_model': 'maintenance.equipment',
            'res_id': self.maintenance_equipment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_maintenance_equipment(self):
        """Manual action to create maintenance equipment"""
        self.ensure_one()

        if self.maintenance_equipment_id:
            raise ValidationError(_('Maintenance equipment already exists for this asset.'))

        equipment = self._create_maintenance_equipment()

        if equipment:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Maintenance equipment created successfully.'),
                    'type': 'success',
                }
            }

        return False