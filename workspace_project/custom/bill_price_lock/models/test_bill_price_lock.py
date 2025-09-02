from odoo.tests.common import TransactionCase


class TestBillPriceLock(TransactionCase):
    """Test the bill price lock functionality"""

    def setUp(self):
        super().setUp()
        # Create test data
        self.partner = self.env['res.partner'].create({
            'name': 'Test Vendor',
            'supplier_rank': 1,
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'purchase_ok': True,
            'list_price': 100.0,
        })

        # Create a purchase order
        self.purchase_order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_qty': 1.0,
                'price_unit': 100.0,
            })]
        })

    def test_price_field_readonly_with_po(self):
        """Test that price field is read-only when PO is selected"""

        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'purchase_vendor_bill_id': self.purchase_order.id,
        })


        self.assertTrue(bill.purchase_vendor_bill_id)
        self.assertEqual(bill.purchase_vendor_bill_id, self.purchase_order)

    def test_price_field_editable_without_po(self):
        """Test that price field is editable when no PO is selected"""
        # Create a bill without PO
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
        })


        self.assertFalse(bill.purchase_vendor_bill_id)