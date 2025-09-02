# Asset Number Auto Generator for Odoo 18

## Overview

This module automatically generates asset numbers for fixed assets in Odoo 18. It creates asset numbers based on the asset name, following a pattern like "MV/001" for "Monitor Vehicle" assets.

## Features

- **Automatic Asset Number Generation**: Creates asset numbers based on asset names
- **Smart Prefix Generation**: Uses first letters of words in asset names (e.g., "Monitor Vehicle" → "MV")
- **Sequential Numbering**: Maintains sequential numbers for each prefix (MV/001, MV/002, etc.)
- **Invoice Integration**: Create assets directly from vendor bill lines
- **Asset Tracking**: Links assets to their source invoice and invoice line
- **User-Friendly Interface**: Clean UI with proper validation and notifications

## Installation

1. Copy the `asset_number` folder to your Odoo custom addons directory
2. Update the addons list in Odoo
3. Install the "Asset Number Auto Generator" module
4. Restart Odoo server

## Usage

### Automatic Asset Creation

When you create a new asset manually or through the system:

1. The asset number is automatically generated based on the asset name
2. For "Monitor Vehicle", it generates "MV/001"
3. For "Desktop Computer", it generates "DC/001"
4. Subsequent assets with the same prefix get incremented numbers

### Creating Assets from Vendor Bills

1. Go to a vendor bill (purchase invoice)
2. In the invoice line form view, you'll see a "Create Assets" button
3. Click the button to open the asset creation wizard
4. Specify the quantity of assets to create
5. Click "Create Assets" to generate the assets

### Asset Number Format

- **Format**: `PREFIX/NUMBER`
- **Prefix**: First letters of asset name words (max 2 letters)
- **Number**: Sequential 3-digit number (001, 002, etc.)

Examples:
- "Monitor Vehicle" → "MV/001"
- "Desktop Computer" → "DC/001"
- "Laptop" → "LA/001"
- "Office Chair" → "OC/001"

## Technical Details

### Models

#### AccountAsset (account.asset)
- `asset_number`: Auto-generated asset number
- `invoice_line_id`: Related invoice line
- `invoice_id`: Related vendor bill

#### AccountMoveLine (account.move.line)
- `action_create_assets_from_line()`: Method to create assets from invoice line

#### CreateAssetWizard (create.asset.wizard)
- Transient model for asset creation wizard
- Handles validation and asset creation process

### Key Methods

#### Asset Number Generation
```python
def _generate_asset_number(self, asset_name):
    # Generates asset number based on asset name
    # Returns format: PREFIX/NUMBER
```

#### Asset Creation from Invoice Line
```python
def action_create_assets_from_line(self):
    # Opens wizard to create assets from invoice line
```

## Configuration

### Dependencies
- `base`: Odoo base module
- `account_asset`: Asset management module

### Security
- Access rights are granted to `account.group_account_user`
- Users with accounting access can create and manage assets

## Troubleshooting

### Common Issues

1. **Asset numbers not generating**: Ensure the asset has a name
2. **Button not visible**: Check that you're on a vendor bill line with a product
3. **Permission errors**: Verify user has accounting access rights

### Logs
Check Odoo logs for detailed error messages:
```bash
tail -f /var/log/odoo/odoo.log
```

## Development

### File Structure
```
asset_number/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── account_asset.py
│   └── account_move_line.py
├── wizard/
│   ├── __init__.py
│   ├── create_asset_wizard.py
│   └── create_asset_wizard_view.xml
├── views/
│   ├── account_asset_view.xml
│   └── account_move_line_view.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

### Customization

To modify the asset number format:
1. Edit the `_generate_asset_number()` method in `account_asset.py`
2. Adjust the prefix generation logic as needed
3. Update the number formatting if required

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Odoo logs for error details
- Ensure all dependencies are properly installed

## License

This module is licensed under AGPL-3.

## Version History

- **18.0.1.0**: Initial release for Odoo 18
  - Automatic asset number generation
  - Invoice line integration
  - Asset creation wizard
  - Proper Odoo 18 compatibility 