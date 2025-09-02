# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ChequeBookWizard(models.TransientModel):
    _name = 'cheque.book.wizard'
    _description = 'Cheque Book Creation Wizard'

    name = fields.Char('Name', required=True)
    journal_id = fields.Many2one('account.journal', string='Bank Account', required=True, domain=[('type', '=', 'bank')])
    bank_account_id = fields.Many2one('account.account', string='Bank Account', compute='_compute_bank_account', store=True)
    first_cheque_no = fields.Char('First Cheque Number', required=True)
    last_cheque_no = fields.Char('Last Cheque Number', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Enhanced fields for smart features
    auto_calculate_range = fields.Boolean('Auto Calculate Range', default=True, help="Automatically calculate cheque number range")
    suggested_range = fields.Char('Suggested Range', compute='_compute_suggested_range', help="Suggested cheque number range based on existing books")
    total_cheques = fields.Integer('Total Cheques', compute='_compute_total_cheques', help="Total number of cheques in the range")
    existing_books_info = fields.Text('Existing Books Info', compute='_compute_existing_books_info', help="Information about existing cheque books")
    
    # Smart selection fields
    smart_name = fields.Char('Smart Name', compute='_compute_smart_name', help="Automatically generated name")
    use_smart_name = fields.Boolean('Use Smart Name', default=True, help="Use automatically generated name")

    @api.depends('journal_id')
    def _compute_bank_account(self):
        """Compute bank account based on selected journal"""
        for record in self:
            if record.journal_id and record.journal_id.default_account_id:
                record.bank_account_id = record.journal_id.default_account_id
            else:
                record.bank_account_id = False

    @api.depends('journal_id')
    def _compute_suggested_range(self):
        """Compute suggested cheque number range based on existing books"""
        for record in self:
            if record.journal_id:
                existing_books = self.env['cheque.book'].search([
                    ('journal_id', '=', record.journal_id.id),
                    ('state', 'in', ['active', 'completed'])
                ], order='last_cheque_no desc', limit=1)
                
                if existing_books:
                    try:
                        last_used = int(existing_books.last_cheque_no)
                        suggested_start = last_used + 1
                        suggested_end = suggested_start + 99  # Default 100 cheques
                        record.suggested_range = f"{suggested_start} - {suggested_end}"
                    except (ValueError, TypeError):
                        record.suggested_range = "1001 - 1100"
                else:
                    record.suggested_range = "1001 - 1100"
            else:
                record.suggested_range = ""

    @api.depends('first_cheque_no', 'last_cheque_no')
    def _compute_total_cheques(self):
        """Compute total number of cheques in the range"""
        for record in self:
            if record.first_cheque_no and record.last_cheque_no:
                try:
                    first = int(record.first_cheque_no)
                    last = int(record.last_cheque_no)
                    record.total_cheques = max(0, last - first + 1)
                except (ValueError, TypeError):
                    record.total_cheques = 0
            else:
                record.total_cheques = 0

    @api.depends('journal_id')
    def _compute_existing_books_info(self):
        """Compute information about existing cheque books"""
        for record in self:
            if record.journal_id:
                existing_books = self.env['cheque.book'].search([
                    ('journal_id', '=', record.journal_id.id)
                ])
                
                if existing_books:
                    info_lines = []
                    for book in existing_books:
                        status = book.state
                        available = book.available_cheques
                        info_lines.append(f"• {book.name}: {status} ({available} available)")
                    
                    record.existing_books_info = f"Existing Books:\n" + "\n".join(info_lines)
                else:
                    record.existing_books_info = "No existing cheque books for this journal."
            else:
                record.existing_books_info = ""

    @api.depends('journal_id', 'first_cheque_no', 'last_cheque_no')
    def _compute_smart_name(self):
        """Compute smart name based on journal and cheque range"""
        for record in self:
            if record.journal_id and record.first_cheque_no and record.last_cheque_no:
                try:
                    first = int(record.first_cheque_no)
                    last = int(record.last_cheque_no)
                    record.smart_name = f"{record.journal_id.name} - {first:06d}-{last:06d}"
                except (ValueError, TypeError):
                    record.smart_name = f"{record.journal_id.name} - Cheque Book"
            elif record.journal_id:
                record.smart_name = f"{record.journal_id.name} - Cheque Book"
            else:
                record.smart_name = ""

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Handle journal change - update suggested range and clear fields"""
        if self.journal_id:
            # Clear current values
            self.first_cheque_no = False
            self.last_cheque_no = False
            
            # Update suggested range
            self._compute_suggested_range()
            
            # Update smart name
            self._compute_smart_name()
            
            # Update existing books info
            self._compute_existing_books_info()

    @api.onchange('auto_calculate_range')
    def _onchange_auto_calculate_range(self):
        """Handle auto calculate range toggle"""
        if self.auto_calculate_range and self.suggested_range:
            try:
                start, end = self.suggested_range.split(' - ')
                self.first_cheque_no = start.strip()
                self.last_cheque_no = end.strip()
            except (ValueError, AttributeError):
                pass

    @api.onchange('use_smart_name')
    def _onchange_use_smart_name(self):
        """Handle smart name toggle"""
        if self.use_smart_name and self.smart_name:
            self.name = self.smart_name

    @api.constrains('first_cheque_no', 'last_cheque_no')
    def _check_cheque_numbers(self):
        for record in self:
            if record.first_cheque_no and record.last_cheque_no:
                try:
                    first = int(record.first_cheque_no)
                    last = int(record.last_cheque_no)
                    if first > last:
                        raise ValidationError(_('First cheque number must be less than or equal to last cheque number.'))
                    if first < 0 or last < 0:
                        raise ValidationError(_('Cheque numbers must be positive integers.'))
                    
                    # Check for overlap with existing books
                    if record.journal_id:
                        existing_books = self.env['cheque.book'].search([
                            ('journal_id', '=', record.journal_id.id),
                            ('state', 'in', ['active', 'completed'])
                        ])
                        
                        for existing_book in existing_books:
                            try:
                                existing_first = int(existing_book.first_cheque_no)
                                existing_last = int(existing_book.last_cheque_no)
                                
                                # Check for overlap
                                if not (last < existing_first or first > existing_last):
                                    raise ValidationError(_(
                                        'Cheque number range overlaps with existing book "%s" (%s-%s). '
                                        'Please choose a different range.'
                                    ) % (existing_book.name, existing_book.first_cheque_no, existing_book.last_cheque_no))
                            except (ValueError, TypeError):
                                continue
                                
                except ValueError:
                    raise ValidationError(_('Cheque numbers must be valid integers.'))

    def action_auto_fill_range(self):
        """Auto-fill the cheque number range based on suggestion"""
        if not self.journal_id:
            raise UserError(_('Please select a journal first.'))
        
        if not self.suggested_range:
            raise UserError(_('No suggested range available.'))
        
        try:
            start, end = self.suggested_range.split(' - ')
            self.write({
                'first_cheque_no': start.strip(),
                'last_cheque_no': end.strip(),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Range Auto-Filled'),
                    'message': _('Cheque number range has been set to %s.') % self.suggested_range,
                    'type': 'success',
                    'sticky': False,
                }
            }
        except (ValueError, AttributeError):
            raise UserError(_('Error parsing suggested range.'))

    def action_validate_range(self):
        """Validate the current cheque number range"""
        if not self.first_cheque_no or not self.last_cheque_no:
            raise UserError(_('Please enter both first and last cheque numbers.'))
        
        try:
            first = int(self.first_cheque_no)
            last = int(self.last_cheque_no)
            total = last - first + 1
            
            message = f"Range Validation:\n"
            message += f"• First: {first}\n"
            message += f"• Last: {last}\n"
            message += f"• Total: {total} cheques\n"
            
            if total <= 0:
                message += "• Status: ❌ Invalid range"
            elif total > 1000:
                message += "• Status: ⚠️ Large range ({total} cheques)"
            else:
                message += "• Status: ✅ Valid range"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Range Validation'),
                    'message': message,
                    'type': 'info',
                    'sticky': True,
                }
            }
        except ValueError:
            raise UserError(_('Invalid cheque numbers. Please enter valid integers.'))

    def action_show_existing_books(self):
        """Show detailed information about existing cheque books"""
        if not self.journal_id:
            raise UserError(_('Please select a journal first.'))
        
        existing_books = self.env['cheque.book'].search([
            ('journal_id', '=', self.journal_id.id)
        ])
        
        if not existing_books:
            raise UserError(_('No existing cheque books found for this journal.'))
        
        message = f"Existing Cheque Books for {self.journal_id.name}:\n\n"
        
        for book in existing_books:
            message += f"📖 {book.name}\n"
            message += f"   • Status: {book.state}\n"
            message += f"   • Range: {book.first_cheque_no} - {book.last_cheque_no}\n"
            message += f"   • Available: {book.available_cheques}/{book.total_cheques}\n"
            message += f"   • Next: {book.current_cheque_no}\n\n"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Existing Cheque Books'),
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }

    def action_debug_info(self):
        """Show debug information about the wizard state"""
        debug_info = {
            'Journal': self.journal_id.name if self.journal_id else 'Not selected',
            'Bank Account': self.bank_account_id.name if self.bank_account_id else 'Not available',
            'Company': self.company_id.name if self.company_id else 'Not set',
            'Auto Calculate': self.auto_calculate_range,
            'Use Smart Name': self.use_smart_name,
            'Suggested Range': self.suggested_range or 'Not available',
            'Smart Name': self.smart_name or 'Not available',
            'Total Cheques': self.total_cheques,
        }
        
        if self.journal_id:
            existing_books = self.env['cheque.book'].search([
                ('journal_id', '=', self.journal_id.id)
            ])
            debug_info['Existing Books Count'] = len(existing_books)
            
            active_books = existing_books.filtered(lambda x: x.state == 'active')
            debug_info['Active Books Count'] = len(active_books)
        
        debug_message = "\n".join([f"• {k}: {v}" for k, v in debug_info.items()])
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Debug Information'),
                'message': debug_message,
                'type': 'info',
                'sticky': True,
            }
        }

    def action_create_cheque_book(self):
        """Create the cheque book with enhanced validation"""
        self.ensure_one()
        
        # Validate required fields
        if not self.name:
            raise UserError(_('Please enter a name for the cheque book.'))
        
        if not self.journal_id:
            raise UserError(_('Please select a journal.'))
        
        if not self.first_cheque_no or not self.last_cheque_no:
            raise UserError(_('Please enter both first and last cheque numbers.'))
        
        # Check if there's already an active cheque book for this bank account
        existing = self.env['cheque.book'].search([
            ('bank_account_id', '=', self.bank_account_id.id),
            ('state', '=', 'active')
        ])
        
        if existing:
            raise UserError(_('There is already an active cheque book for this bank account. Please complete or cancel the existing one first.'))
        
        # Create the cheque book
        cheque_book = self.env['cheque.book'].create({
            'name': self.name,
            'bank_account_id': self.bank_account_id.id,
            'journal_id': self.journal_id.id,
            'first_cheque_no': self.first_cheque_no,
            'last_cheque_no': self.last_cheque_no,
            'company_id': self.company_id.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'cheque.book',
            'res_id': cheque_book.id,
            'view_mode': 'form',
            'target': 'current',
        } 