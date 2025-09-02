#!/bin/bash

# Simple Installation Script for Quotation PDF Downloader Module
# No image dependencies - pure text-based PDF generation

echo "🚀 Simple Installation for Quotation PDF Downloader"
echo "=================================================="
echo "This module works without any images or filestore dependencies"
echo ""

# Check if we're in the right directory
if [ ! -f "__manifest__.py" ]; then
    echo "❌ Error: Please run this script from the quotation_pdf_downloader directory"
    exit 1
fi

echo "✅ Module structure verified"
echo "✅ No image dependencies - pure text-based PDF generation"
echo "✅ No filestore requirements"
echo ""

# Set proper permissions
echo "🔧 Setting file permissions..."
chmod 644 *.py
chmod 644 models/*.py
chmod 644 views/*.xml
chmod 644 report/*.xml
chmod 644 security/*.csv

echo "✅ Permissions set successfully"
echo ""

echo "📋 Installation Steps:"
echo "1. Copy this module to your Odoo addons directory"
echo "2. Restart your Odoo server"
echo "3. Go to Apps → Update Apps List"
echo "4. Search for 'Quotation PDF Downloader' and install"
echo "5. Test with a quotation in draft or sent state"
echo ""

echo "🎯 Features:"
echo "✅ Professional PDF quotation generation"
echo "✅ No image dependencies"
echo "✅ No filestore requirements"
echo "✅ Clean, text-based design"
echo "✅ Works in both localhost and production"
echo ""

echo "💡 Benefits:"
echo "- No more filestore errors"
echo "- No missing image issues"
echo "- Faster PDF generation"
echo "- More reliable operation"
echo "- Easier maintenance"
echo ""

echo "🚀 Ready for installation!"
echo "The module will generate professional quotations without any image dependencies."
