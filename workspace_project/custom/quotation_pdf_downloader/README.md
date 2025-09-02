# Quotation PDF Downloader Module

This Odoo module adds a custom "Download Quotation" button to sales orders that generates a professional quotation PDF based on the provided template.

## Features

-   Adds a "Download Quotation" button to sale order forms
-   Generates a professional PDF quotation with custom formatting
-   Matches the design of the provided quotation template
-   Includes company header, line items, totals, and terms & conditions
-   Available for quotations in 'draft' and 'sent' states

## Installation

### Localhost/Development

1. Copy the `quotation_pdf_downloader` folder to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the module from the Apps menu
4. Restart your Odoo server

### Production Deployment

```bash
# Quick deployment
./deploy_to_production.sh [production-server] [odoo-user] [database-name]

# Example:
./deploy_to_production.sh myserver.com odoo production_db
```

**For detailed production guidelines, see `PRODUCTION_DEPLOYMENT.md`**

## Usage

1. Go to Sales → Quotations
2. Open any quotation in draft or sent state
3. Click the "Download Quotation" button in the form header
4. The PDF will be generated and downloaded automatically

## Customization

### Company Information

To customize the company information in the quotation header, edit the template in:
`report/quotation_report_templates.xml`

### Styling

The template uses Bootstrap classes and inline CSS for styling. You can modify the appearance by editing the template file.

### Terms and Conditions

Update the terms and conditions section in the template to match your business requirements.

## Technical Details

-   **Model**: Extends `sale.order`
-   **Report Type**: QWeb PDF
-   **Template**: Custom HTML template with Bootstrap styling
-   **Dependencies**: sale, base

## 🌐 Production Ready

This module is designed to work in both **localhost** and **production** environments.

### Production Features

-   ✅ **Security**: Proper file permissions and access controls
-   ✅ **Performance**: Optimized for production workloads
-   ✅ **Monitoring**: Logging and error handling
-   ✅ **Scalability**: Handles multiple users and large datasets
-   ✅ **Backup**: Safe deployment with rollback procedures

### Production Deployment

-   **Automated Script**: `deploy_to_production.sh` for easy deployment
-   **Security Guidelines**: See `PRODUCTION_DEPLOYMENT.md`
-   **Monitoring**: Built-in logging and error tracking
-   **Maintenance**: Regular update procedures

## Files Structure

```
quotation_pdf_downloader/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── sale_order.py
├── views/
│   └── sale_order_views.xml
├── report/
│   ├── quotation_report.xml
│   └── quotation_report_templates.xml
├── security/
│   └── ir.model.access.csv
└── README.md
```

## Support

For issues or questions, please contact your system administrator or refer to the Odoo documentation.
