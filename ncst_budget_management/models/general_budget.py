from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BudgetGeneral(models.Model):
    _name = 'budget.general'
    _description = 'General Budget'
    _order = 'period_start desc, id desc'

    name = fields.Char(
        string='Budget Name',
        required=True,
    )
    period_start = fields.Date(
        string='Period Start',
        required=True,
    )
    period_end = fields.Date(
        string='Period End',
        required=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    total_amount = fields.Monetary(
        string='Total General Budget',
        required=True,
        currency_field='currency_id',
    )
    allocated_amount = fields.Monetary(
        string='Allocated Amount',
        compute='_compute_budget_amounts',
        store=True,
        currency_field='currency_id',
    )
    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        compute='_compute_budget_amounts',
        store=True,
        currency_field='currency_id',
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='draft',
        required=True,
    )
    department_budget_ids = fields.One2many(
        'budget.department',
        'general_budget_id',
        string='Department Budgets',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id,
    )
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user.id,
        readonly=True,
    )

    @api.depends('total_amount', 'department_budget_ids.allocated_amount')
    def _compute_budget_amounts(self):
        for record in self:
            allocated = sum(record.department_budget_ids.mapped('allocated_amount'))
            record.allocated_amount = allocated
            record.remaining_amount = record.total_amount - allocated

    @api.constrains('period_start', 'period_end')
    def _check_period_dates(self):
        for record in self:
            if record.period_end < record.period_start:
                raise ValidationError('Period end date cannot be earlier than period start date.')

    @api.constrains('total_amount')
    def _check_total_amount(self):
        for record in self:
            if record.total_amount <= 0:
                raise ValidationError('The general budget amount must be greater than zero.')

    @api.constrains('period_start', 'period_end', 'company_id')
    def _check_period_overlap(self):
        for record in self:
            overlapping_budget = self.search([
                ('id', '!=', record.id),
                ('company_id', '=', record.company_id.id),
                ('period_start', '<=', record.period_end),
                ('period_end', '>=', record.period_start),
            ], limit=1)

            if overlapping_budget:
                raise ValidationError(
                    'You cannot create overlapping general budgets for the same company.'
                )

    def action_activate(self):
        for record in self:
            if record.state != 'draft':
                continue
            record.state = 'active'

    def action_close(self):
        for record in self:
            if record.state != 'active':
                continue
            record.state = 'closed'

    def action_reset_to_draft(self):
        for record in self:
            if record.state == 'closed':
                continue
            record.state = 'draft'