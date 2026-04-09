from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BudgetReservation(models.Model):
    _name = 'budget.reservation'
    _description = 'Budget Reservation'
    _order = 'id desc'

    name = fields.Char(
        string='Reservation Reference',
        required=True,
        copy=False,
        default='New',
        readonly=True,
    )
    department_budget_id = fields.Many2one(
        'budget.department',
        string='Department Budget',
        required=True,
        ondelete='cascade',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='department_budget_id.department_id',
        store=True,
        readonly=True,
    )
    general_budget_id = fields.Many2one(
        'budget.general',
        string='General Budget',
        related='department_budget_id.general_budget_id',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related='department_budget_id.currency_id',
        string='Currency',
        store=True,
    )
    amount = fields.Monetary(
        string='Reservation Amount',
        required=True,
        currency_field='currency_id',
    )
    date = fields.Date(
        string='Reservation Date',
        required=True,
        default=fields.Date.context_today,
    )
    description = fields.Text(
        string='Description',
    )
    request_ref = fields.Char(
        string='Related Request Reference',
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
    )
    company_id = fields.Many2one(
        related='department_budget_id.company_id',
        string='Company',
        store=True,
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('budget.reservation') or 'New'
        return super().create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError('Reservation amount must be greater than zero.')

    def action_reserve(self):
        for record in self:
            if record.state != 'draft':
                continue

            if record.amount > record.department_budget_id.remaining_balance:
                raise ValidationError(
                    'The reservation amount exceeds the remaining department budget balance.'
                )

            record.state = 'reserved'

    def action_mark_used(self):
        for record in self:
            if record.state != 'reserved':
                continue
            record.state = 'used'

    def action_cancel(self):
        for record in self:
            if record.state not in ['draft', 'reserved']:
                continue
            record.state = 'cancelled'

    def action_reset_to_draft(self):
        for record in self:
            if record.state in ['used', 'cancelled']:
                continue
            record.state = 'draft'