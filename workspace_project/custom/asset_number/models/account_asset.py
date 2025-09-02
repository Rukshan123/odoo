from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    asset_number = fields.Char(
        string='Asset Number',
        readonly=True,
        copy=False,
        index=True,
        help="Auto-generated asset number based on asset category"
    )
    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        readonly=True,
        help="Related invoice line from which this asset was created"
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        readonly=True,
        help="Related vendor bill from which this asset was created"
    )
    short_code = fields.Char(
        string='Short Code',
        size=10,
        help="Short code for quick identification of asset model",
        tracking=True,
        index=True,
    )

    @api.model
    def create(self, vals):
        """Override create to auto-generate both asset number and short code"""
        # First handle short code generation
        if not vals.get('short_code') and vals.get('name'):
            vals['short_code'] = self._generate_short_code(vals['name'])

        # Then handle asset number generation
        if not vals.get('asset_number'):
            model_id = vals.get('model_id')
            model_name = None
            if model_id:
                model = self.env['account.asset'].browse(model_id) if not isinstance(model_id, models.BaseModel) else model_id
                model_name = model.name
            vals['asset_number'] = self._generate_asset_number(model_name)

        return super(AccountAsset, self).create(vals)

    def _generate_short_code(self, asset_name):
        """Generate short code from asset name with specific mappings"""
        if not asset_name:
            return ''

        # Specific asset code mappings as requested
        asset_code_mappings = {
            'building': 'BG',
            'furniture & fittings': 'FF',
            'motor vehicle': 'MV',
            'office equipment': 'OE',
            'plant & machinery': 'PM',
        }

        # Check for exact matches first
        asset_lower = asset_name.lower().strip()
        if asset_lower in asset_code_mappings:
            return asset_code_mappings[asset_lower]

        # Check for partial matches
        for key, code in asset_code_mappings.items():
            if key in asset_lower:
                return code

        # For other asset names, generate from first letters of words
        words = re.findall(r'\b\w+', asset_lower)
        if not words:
            return ''

        # Take first letter of each word, up to 2 words for consistency
        short_code = ''.join(word[0].upper() for word in words[:2])

        # Ensure it's not longer than 10 characters
        return short_code[:10]

    def write(self, vals):
        """Override write to auto-generate short code if name changes and short code is empty"""
        if 'name' in vals and not vals.get('short_code'):
            for record in self:
                if not record.short_code:
                    vals['short_code'] = self._generate_short_code(vals['name'])
                    break
        return super(AccountAsset, self).write(vals)

    @api.onchange('name')
    def _onchange_name(self):
        """Auto-generate short code when name changes"""
        if self.name and not self.short_code:
            self.short_code = self._generate_short_code(self.name)

    def _generate_asset_number(self, model_name):
        """Generate asset number based on asset model name"""
        if not model_name:
            return self._get_next_default_number()

        # Special mapping for known asset models
        special_prefixes = {
            'building': 'BG',
            'furniture & fittings': 'FF',
            'motor vehicle': 'MV',
            'office equipment': 'OE',
            'plant & machinery': 'PM',
        }
        key = model_name.strip().lower()
        if key in special_prefixes:
            prefix = special_prefixes[key]
        else:
            # Remove special characters and split into words
            words = re.findall(r'\b\w+', model_name)
            prefix = ''.join(word[0].upper() for word in words[:2])
        return self._get_next_number_for_prefix(prefix)

    def _get_next_number_for_prefix(self, prefix):
        """Get next available number for given prefix"""
        last_asset = self.search([
            ('asset_number', 'like', f'{prefix}/%')
        ], order='asset_number desc', limit=1)

        if last_asset and last_asset.asset_number:
            asset_num = last_asset.asset_number
            if asset_num.startswith(f'{prefix}/'):
                number_part = asset_num[len(prefix) + 1:]  # +1 for '/'
                if number_part.isdigit():
                    next_number = int(number_part) + 1
                else:
                    next_number = 1
            else:
                next_number = 1
        else:
            next_number = 1

        return f"{prefix}/{next_number:03d}"

    def _get_next_default_number(self):
        """Get next default asset number"""
        last_asset = self.search([
            ('asset_number', 'like', 'AS/%')
        ], order='asset_number desc', limit=1)

        if last_asset and last_asset.asset_number:
            asset_num = last_asset.asset_number
            if asset_num.startswith('AS/'):
                number_part = asset_num[3:]  # Skip 'AS/'
                if number_part.isdigit():
                    next_number = int(number_part) + 1
                else:
                    next_number = 1
            else:
                next_number = 1
        else:
            next_number = 1

        return f"AS/{next_number:03d}"

    def name_get(self):
        """Override to show asset number with name"""
        result = []
        for asset in self:
            if asset.asset_number:
                display_name = f"{asset.name} ({asset.asset_number})"
                if asset.short_code:
                    display_name = f"{asset.short_code} - {display_name}"
                result.append((asset.id, display_name))
            else:
                result.append((asset.id, asset.name))
        return result

    @api.model
    def create_assets_from_invoice_line(self, invoice_line):
        """Create multiple assets from invoice line based on quantity"""
        assets = self.env['account.asset']

        if not invoice_line.product_id or invoice_line.quantity <= 0:
            return assets

        for i in range(int(invoice_line.quantity)):
            asset_vals = {
                'name': invoice_line.product_id.name,
                'original_value': invoice_line.price_unit,
                'invoice_line_id': invoice_line.id,
                'invoice_id': invoice_line.move_id.id,
                'acquisition_date': invoice_line.move_id.invoice_date or fields.Date.today(),
                'state': 'draft',
                'model_id': invoice_line.asset_model_id.id if hasattr(invoice_line, 'asset_model_id') and invoice_line.asset_model_id else None,
            }

            asset = self.create(asset_vals)
            assets |= asset

        return assets