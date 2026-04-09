from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BudgetDepartment(models.Model):
    _name = 'budget.department'
    _description = 'Department Budget'
    _order = 'id desc'

    name = fields.Char(
        string='Department Budget Name',
        required=True,
    )
    general_budget_id = fields.Many2one(
        'budget.general',
        string='General Budget',
        required=True,
        ondelete='cascade',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
    )
    currency_id = fields.Many2one(
        related='general_budget_id.currency_id',
        string='Currency',
        store=True,
    )
    allocated_amount = fields.Monetary(
        string='Allocated Amount',
        required=True,
        currency_field='currency_id',
    )
    reserved_amount = fields.Monetary(
        string='Reserved Amount',
        compute='_compute_budget_usage',
        store=True,
        currency_field='currency_id',
    )
    used_amount = fields.Monetary(
        string='Used Amount',
        compute='_compute_budget_usage',
        store=True,
        currency_field='currency_id',
    )
    remaining_balance = fields.Monetary(
        string='Remaining Balance',
        compute='_compute_budget_usage',
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
    reservation_ids = fields.One2many(
        'budget.reservation',
        'department_budget_id',
        string='Reservations',
    )
    company_id = fields.Many2one(
        related='general_budget_id.company_id',
        string='Company',
        store=True,
    )

    @api.depends('allocated_amount', 'reservation_ids.amount', 'reservation_ids.state')
    def _compute_budget_usage(self):
        for record in self:
            reserved = sum(
                record.reservation_ids.filtered(lambda r: r.state == 'reserved').mapped('amount')
            )
            used = sum(
                record.reservation_ids.filtered(lambda r: r.state == 'used').mapped('amount')
            )
            record.reserved_amount = reserved
            record.used_amount = used
            record.remaining_balance = record.allocated_amount - reserved - used

    @api.constrains('allocated_amount')
    def _check_allocated_amount(self):
        for record in self:
            if record.allocated_amount <= 0:
                raise ValidationError('Department allocated amount must be greater than zero.')

    @api.constrains('department_id', 'general_budget_id')
    def _check_unique_department_budget(self):
        for record in self:
            existing_budget = self.search([
                ('id', '!=', record.id),
                ('general_budget_id', '=', record.general_budget_id.id),
                ('department_id', '=', record.department_id.id),
            ], limit=1)

            if existing_budget:
                raise ValidationError(
                    'This department already has a budget under the selected general budget.'
                )

    @api.constrains('allocated_amount', 'general_budget_id')
    def _check_general_budget_limit(self):
        for record in self:
            if not record.general_budget_id:
                continue

            other_department_budgets = record.general_budget_id.department_budget_ids.filtered(
                lambda d: d.id != record.id
            )
            other_allocated_total = sum(other_department_budgets.mapped('allocated_amount'))
            allowed_balance = record.general_budget_id.total_amount - other_allocated_total

            if record.allocated_amount > allowed_balance:
                raise ValidationError(
                    'The allocated amount exceeds the remaining general budget.'
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