# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ChequeBook(models.Model):
    _name = 'cheque.book'
    _description = 'Cheque Book Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, create_date desc'

    name = fields.Char('Name', default='New', readonly=True, tracking=True)
    sequence = fields.Integer('Sequence', default=10, help="Determines the order of cheque books when multiple exist for the same account", tracking=True)
    journal_id = fields.Many2one('account.journal', string='Bank Account', required=True, tracking=True, domain=[('type', '=', 'bank')])
    bank_account_id = fields.Many2one('account.account', string='Bank Account', compute='_compute_bank_account', store=True, tracking=True)
    first_cheque_no = fields.Char('First Cheque Number', required=True, tracking=True)
    last_cheque_no = fields.Char('Last Cheque Number', required=True, tracking=True)
    current_cheque_no = fields.Char('Current Cheque Number', compute='_compute_current_cheque_no', store=True, tracking=True)
    total_cheques = fields.Integer('Total Cheques', compute='_compute_total_cheques', store=True)
    used_cheques = fields.Integer('Used Cheques', compute='_compute_used_cheques', store=True)
    available_cheques = fields.Integer('Available Cheques', compute='_compute_available_cheques', store=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='active', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    active = fields.Boolean(default=True)
    
    # Used cheque numbers tracking
    used_cheque_numbers = fields.One2many('cheque.number.used', 'cheque_book_id', string='Used Cheque Numbers')
    
    @api.depends('first_cheque_no', 'last_cheque_no')
    def _compute_total_cheques(self):
        for record in self:
            if record.first_cheque_no and record.last_cheque_no:
                try:
                    first = int(record.first_cheque_no)
                    last = int(record.last_cheque_no)
                    record.total_cheques = last - first + 1
                except ValueError:
                    record.total_cheques = 0
            else:
                record.total_cheques = 0

    @api.depends('used_cheque_numbers')
    def _compute_used_cheques(self):
        for record in self:
            record.used_cheques = len(record.used_cheque_numbers)

    @api.depends('total_cheques', 'used_cheques')
    def _compute_available_cheques(self):
        for record in self:
            record.available_cheques = record.total_cheques - record.used_cheques

    @api.depends('first_cheque_no', 'last_cheque_no', 'used_cheque_numbers')
    def _compute_current_cheque_no(self):
        for record in self:
            if record.first_cheque_no and record.last_cheque_no:
                try:
                    first = int(record.first_cheque_no)
                    last = int(record.last_cheque_no)
                    used_numbers = [int(x.cheque_number) for x in record.used_cheque_numbers]
                    
                    # Find the next available cheque number
                    for i in range(first, last + 1):
                        if i not in used_numbers:
                            record.current_cheque_no = str(i)
                            break
                    else:
                        record.current_cheque_no = False
                except ValueError:
                    record.current_cheque_no = False
            else:
                record.current_cheque_no = False

    def refresh_current_cheque_no(self):
        """Manually refresh the current cheque number"""
        self.ensure_one()
        # self.invalidate_cache(['current_cheque_no'])
        self._compute_current_cheque_no()
        return self.current_cheque_no

    @api.constrains('first_cheque_no', 'last_cheque_no', 'journal_id')
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
                    
                    # Check for overlapping cheque number ranges with other cheque books for the same journal
                    if record.journal_id:
                        overlapping_books = self.search([
                            ('id', '!=', record.id),
                            ('journal_id', '=', record.journal_id.id),
                            ('state', 'in', ['active', 'completed']),
                            '|',
                            '&', ('first_cheque_no', '<=', record.first_cheque_no), ('last_cheque_no', '>=', record.first_cheque_no),
                            '&', ('first_cheque_no', '<=', record.last_cheque_no), ('last_cheque_no', '>=', record.last_cheque_no)
                        ])
                        
                        if overlapping_books:
                            raise ValidationError(_(
                                'Cheque number range %s-%s overlaps with existing cheque books for this bank account. '
                                'Please use a different range.'
                            ) % (record.first_cheque_no, record.last_cheque_no))
                            
                except ValueError:
                    raise ValidationError(_('Cheque numbers must be valid integers.'))

    @api.depends('journal_id')
    def _compute_bank_account(self):
        """Compute bank account based on selected journal"""
        for record in self:
            if record.journal_id and record.journal_id.default_account_id:
                record.bank_account_id = record.journal_id.default_account_id
            else:
                record.bank_account_id = False

    def get_next_cheque_number(self):
        """Get the next available cheque number for this cheque book"""
        self.ensure_one()
        if not self.current_cheque_no:
            raise UserError(_('No more cheque numbers available in this cheque book.'))
        
        next_number = self.current_cheque_no
        return next_number

    def get_next_cheque_number_safe(self):
        """Get the next available cheque number safely (returns False if none available)"""
        self.ensure_one()
        # Refresh the computation to ensure it's up to date
        self.refresh_current_cheque_no()
        if not self.current_cheque_no:
            return False
        
        return self.current_cheque_no

    def mark_cheque_as_used(self, cheque_number, pdc_id):
        """Mark a cheque number as used with transaction safety"""
        self.ensure_one()
        
        # Use a more robust check with database-level constraint
        try:
            # Create used cheque number record - this will fail if already exists due to SQL constraint
            used_record = self.env['cheque.number.used'].create({
                'cheque_book_id': self.id,
                'cheque_number': cheque_number,
                'pdc_id': pdc_id,
                'used_date': fields.Date.today(),
            })
            
            # Refresh the current cheque number after successful creation
            # self.invalidate_cache(['current_cheque_no'])
            self._compute_current_cheque_no()
            
            return used_record
            
        except Exception as e:
            # If creation fails, it's likely due to duplicate constraint
            if 'unique_cheque_number_per_book' in str(e):
                raise UserError(_('Cheque number %s is already used in this cheque book.') % cheque_number)
            else:
                raise e

    def action_complete(self):
        """Mark cheque book as completed"""
        for record in self:
            if record.available_cheques > 0:
                raise UserError(_('Cannot complete cheque book. There are still %s available cheques.') % record.available_cheques)
            record.state = 'completed'

    def action_cancel(self):
        """Cancel cheque book"""
        for record in self:
            if record.used_cheques > 0:
                raise UserError(_('Cannot cancel cheque book. There are %s used cheques.') % record.used_cheques)
            record.state = 'cancelled'

    def action_reactivate(self):
        """Reactivate cancelled cheque book"""
        for record in self:
            record.state = 'active'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence for name"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('cheque.book') or 'New'
        return super().create(vals_list)

    def get_available_cheque_books(self, journal_id):
        """Get available cheque books for a journal, ordered by sequence"""
        return self.search([
            ('journal_id', '=', journal_id),
            ('state', '=', 'active'),
            ('available_cheques', '>', 0)
        ], order='sequence, create_date desc')

    def get_default_cheque_book(self, journal_id):
        """Get the default cheque book for a journal (first by sequence)"""
        available_books = self.get_available_cheque_books(journal_id)
        return available_books[0] if available_books else False

    @api.model
    def check_cheque_number_duplicate(self, cheque_number, journal_id, exclude_cheque_book_id=None):
        """Check if a cheque number is already used across all cheque books for a journal"""
        domain = [
            ('cheque_number', '=', cheque_number),
            ('cheque_book_id.journal_id', '=', journal_id)
        ]
        
        if exclude_cheque_book_id:
            domain.append(('cheque_book_id', '!=', exclude_cheque_book_id))
        
        existing_used = self.env['cheque.number.used'].search(domain)
        return existing_used

    @api.model
    def validate_cheque_number_range(self, first_number, last_number, journal_id, exclude_cheque_book_id=None):
        """Validate that a cheque number range doesn't overlap with existing ranges"""
        try:
            first = int(first_number)
            last = int(last_number)
            
            if first > last:
                return False, _('First cheque number must be less than or equal to last cheque number.')
            
            if first < 0 or last < 0:
                return False, _('Cheque numbers must be positive integers.')
            
            # Check for overlapping ranges
            overlapping_books = self.search([
                ('id', '!=', exclude_cheque_book_id) if exclude_cheque_book_id else ('id', '!=', 0),
                ('journal_id', '=', journal_id),
                ('state', 'in', ['active', 'completed']),
                '|',
                '&', ('first_cheque_no', '<=', first), ('last_cheque_no', '>=', first),
                '&', ('first_cheque_no', '<=', last), ('last_cheque_no', '>=', last)
            ])
            
            if overlapping_books:
                return False, _(
                    'Cheque number range %s-%s overlaps with existing cheque books for this bank account. '
                    'Please use a different range.'
                ) % (first_number, last_number)
            
            return True, None
            
        except ValueError:
            return False, _('Cheque numbers must be valid integers.')


class ChequeNumberUsed(models.Model):
    _name = 'cheque.number.used'
    _description = 'Used Cheque Numbers'
    _order = 'used_date desc'

    cheque_book_id = fields.Many2one('cheque.book', string='Cheque Book', required=True, ondelete='cascade')
    cheque_number = fields.Char('Cheque Number', required=True)
    pdc_id = fields.Many2one('pdc.wizard', string='PDC Payment', required=True, ondelete='cascade')
    used_date = fields.Date('Used Date', default=fields.Date.today)
    partner_id = fields.Many2one('res.partner', string='Partner', related='pdc_id.partner_id', store=True)
    payment_amount = fields.Monetary('Payment Amount', related='pdc_id.payment_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='pdc_id.currency_id', store=True)
    state = fields.Selection('State', related='pdc_id.state', store=True)

    _sql_constraints = [
        ('unique_cheque_number_per_book', 'unique(cheque_book_id, cheque_number)', 
         'Each cheque number can only be used once per cheque book!'),
    ] 