# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PDCWizardExtension(models.Model):
    _inherit = 'pdc.wizard'

    cheque_book_id = fields.Many2one('cheque.book', string='Cheque Book', tracking=True)
    auto_assign_cheque = fields.Boolean('Auto Assign Cheque Number', default=True, tracking=True)
    text_free = fields.Char('Free Text')
    partner_text = fields.Char('Partner Title')
    is_cheque = fields.Boolean('Is Cheque')

    @api.onchange('journal_id')
    def _onchange_journal_id_extension(self):
        """Update cheque book domain when journal changes and auto-assign if enabled"""
        # Clear current cheque book selection when journal changes
        self.cheque_book_id = False
        self.reference = False
        # Also clear cheque_no field for dev_print_cheque integration
        if hasattr(self, 'cheque_no'):
            self.cheque_no = False

        # Only auto-assign for send money (outbound) payments
        if self.journal_id and self.payment_type == 'send_money':
            # Get available cheque books for this journal
            available_cheque_books = self.env['cheque.book'].get_available_cheque_books(self.journal_id.id)
            
            # Auto-assign the first available cheque book if auto_assign_cheque is enabled
            if self.auto_assign_cheque and available_cheque_books:
                default_cheque_book = self.env['cheque.book'].get_default_cheque_book(self.journal_id.id)
                if default_cheque_book:
                    self.cheque_book_id = default_cheque_book
                    # Auto-assign the next available cheque number
                    next_cheque_no = default_cheque_book.get_next_cheque_number_safe()
                    if next_cheque_no:
                        self.reference = next_cheque_no
                        # Also set cheque_no for dev_print_cheque integration
                        if hasattr(self, 'cheque_no'):
                            self.cheque_no = next_cheque_no

            return {
                'domain': {'cheque_book_id': [('id', 'in', available_cheque_books.ids)]},
            }
        else:
            return {
                'domain': {'cheque_book_id': [('id', '=', False)]},
            }

    @api.onchange('cheque_book_id')
    def _onchange_cheque_book_id(self):
        """Auto-assign cheque number when cheque book is selected"""
        # Only auto-assign for send money (outbound) payments
        if self.cheque_book_id and self.auto_assign_cheque and self.payment_type == 'send_money':
            next_cheque_no = self.cheque_book_id.get_next_cheque_number_safe()
            if next_cheque_no:
                self.reference = next_cheque_no
                # Also set cheque_no for dev_print_cheque integration
                if hasattr(self, 'cheque_no'):
                    self.cheque_no = next_cheque_no

    @api.onchange('auto_assign_cheque')
    def _onchange_auto_assign_cheque(self):
        """Handle auto-assignment toggle"""
        # Only auto-assign for send money (outbound) payments
        if self.auto_assign_cheque and self.cheque_book_id and self.payment_type == 'send_money':
            next_cheque_no = self.cheque_book_id.get_next_cheque_number_safe()
            if next_cheque_no:
                self.reference = next_cheque_no
                # Also set cheque_no for dev_print_cheque integration
                if hasattr(self, 'cheque_no'):
                    self.cheque_no = next_cheque_no

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        """Handle payment type change - clear cheque book for receive money"""
        if self.payment_type == 'receive_money':
            # Clear cheque book and reference for receive money payments
            self.cheque_book_id = False
            self.reference = False
            if hasattr(self, 'cheque_no'):
                self.cheque_no = False
            self.auto_assign_cheque = False
        elif self.payment_type == 'send_money':
            # Enable auto-assignment for send money payments
            self.auto_assign_cheque = True

    @api.onchange('reference')
    def _onchange_reference(self):
        """Sync reference with cheque_no for dev_print_cheque integration"""
        if hasattr(self, 'cheque_no') and self.reference:
            self.cheque_no = self.reference

    def action_register(self):
        """Override to mark cheque as used when registering PDC"""
        result = super().action_register()
        
        # Mark cheque as used if cheque book is selected and reference is provided
        # Only for send money payments
        if self.cheque_book_id and self.reference and self.payment_type == 'send_money':
            try:
                self.cheque_book_id.mark_cheque_as_used(self.reference, self.id)
            except UserError as e:
                # If there's an error marking the cheque as used, show the error
                raise e
        
        return result

    @api.model
    def default_get(self, fields):
        """Override to add cheque fields context and auto-assignment"""
        rec = super().default_get(fields)
        
        # Set auto_assign_cheque to True by default only for send money
        if 'auto_assign_cheque' in fields:
            payment_type = self._context.get('default_payment_type', 'send_money')
            rec['auto_assign_cheque'] = (payment_type == 'send_money')
            
        return rec

    def action_register_check(self):
        """Override to add cheque fields context"""
        result = super().action_register_check()
        if result and 'context' in result:
            result['context']['show_cheque_fields'] = True
        return result

    def get_cheque_number_from_book(self):
        """Get the next available cheque number from the selected cheque book and assign it"""
        # Only allow for send money payments
        if self.payment_type != 'send_money':
            raise UserError(_('Cheque number assignment is only available for "Send Money" payments.'))
        
        if not self.cheque_book_id:
            raise UserError(_('Please select a cheque book first.'))
        
        if not self.auto_assign_cheque:
            raise UserError(_('Auto assignment is disabled. Please enable it or manually enter the cheque number.'))
        
        next_cheque_no = self.cheque_book_id.get_next_cheque_number_safe()
        if not next_cheque_no:
            raise UserError(_('No more cheque numbers available in the selected cheque book.'))
        
        # Update the fields
        self.write({
            'reference': next_cheque_no,
        })
        
        # Also update cheque_no if it exists (for dev_print_cheque integration)
        if hasattr(self, 'cheque_no'):
            self.write({
                'cheque_no': next_cheque_no,
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cheque Number Assigned'),
                'message': _('Cheque number %s has been assigned successfully.') % next_cheque_no,
                'type': 'success',
                'sticky': False,
            }
        }

    def force_auto_assign(self):
        """Force auto-assignment of cheque book and number"""
        # Only allow for send money payments
        if self.payment_type != 'send_money':
            raise UserError(_('Auto assignment is only available for "Send Money" payments.'))
        
        if not self.journal_id:
            raise UserError(_('Please select a journal first.'))
        
        # Get available cheque books
        available_cheque_books = self.env['cheque.book'].get_available_cheque_books(self.journal_id.id)
        if not available_cheque_books:
            raise UserError(_('No available cheque books found for the selected journal.'))
        
        # Get default cheque book
        default_cheque_book = self.env['cheque.book'].get_default_cheque_book(self.journal_id.id)
        if not default_cheque_book:
            raise UserError(_('No default cheque book found for the selected journal.'))
        
        # Get next cheque number
        next_cheque_no = default_cheque_book.get_next_cheque_number_safe()
        if not next_cheque_no:
            raise UserError(_('No more cheque numbers available in the default cheque book.'))
        
        # Update the fields
        self.write({
            'cheque_book_id': default_cheque_book.id,
            'reference': next_cheque_no,
            'auto_assign_cheque': True,
        })
        
        # Also update cheque_no if it exists
        if hasattr(self, 'cheque_no'):
            self.write({
                'cheque_no': next_cheque_no,
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto Assignment Complete'),
                'message': _('Cheque book %s and number %s have been assigned successfully.') % (default_cheque_book.name, next_cheque_no),
                'type': 'success',
                'sticky': False,
            }
        }

    def debug_auto_assignment(self):
        """Debug method to check auto-assignment status"""
        debug_info = {
            'journal_id': self.journal_id.name if self.journal_id else 'Not selected',
            'payment_type': self.payment_type,
            'cheque_book_id': self.cheque_book_id.name if self.cheque_book_id else 'Not selected',
            'auto_assign_cheque': self.auto_assign_cheque,
            'reference': self.reference or 'Not assigned',
            'state': self.state,
        }
        
        if self.journal_id and self.payment_type == 'send_money':
            available_books = self.env['cheque.book'].get_available_cheque_books(self.journal_id.id)
            debug_info['available_cheque_books'] = [book.name for book in available_books]
            
            if self.cheque_book_id:
                debug_info['cheque_book_status'] = {
                    'state': self.cheque_book_id.state,
                    'total_cheques': self.cheque_book_id.total_cheques,
                    'used_cheques': self.cheque_book_id.used_cheques,
                    'available_cheques': self.cheque_book_id.available_cheques,
                    'current_cheque_no': self.cheque_book_id.current_cheque_no,
                    'first_cheque_no': self.cheque_book_id.first_cheque_no,
                    'last_cheque_no': self.cheque_book_id.last_cheque_no,
                }
        else:
            debug_info['note'] = 'Cheque assignment only available for "Send Money" payments'
        
        # Return debug info as notification
        debug_message = "\n".join([f"{k}: {v}" for k, v in debug_info.items()])
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-Assignment Debug Info'),
                'message': debug_message,
                'type': 'info',
                'sticky': True,
            }
        }