from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BudgetDepartment(models.Model):
    _name = 'budget.department'
    _description = 'Department Budget'
    _order = 'id desc'

    name = fields.Char(
        string='Department Budget Name',
        required=False,
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

    general_budget_remaining = fields.Monetary(
        string='General Budget Remaining',
        compute='_compute_budget_summary',
        currency_field='currency_id',
        store=False,
    )
    current_department_budget = fields.Monetary(
        string='Current Department Budget',
        compute='_compute_budget_summary',
        currency_field='currency_id',
        store=False,
    )
    new_department_budget = fields.Monetary(
        string='Department Budget After Assignment',
        compute='_compute_budget_summary',
        currency_field='currency_id',
        store=False,
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
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
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
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        readonly=True,
    )

    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        readonly=True,
    )

    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
    )


    rejected_by = fields.Many2one(
        'res.users',
        string='Rejected By',
        readonly=True,
    )
    rejection_date = fields.Datetime(
        string='Rejection Date',
        readonly=True,
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True,
    )

    @api.depends(
    'general_budget_id',
    'department_id',
    'allocated_amount',
    'state',
    'remaining_balance',
    'reserved_amount',
    'used_amount',
    )
    def _compute_budget_summary(self):
        for record in self:
            record._update_budget_summary_values()

    @api.onchange('general_budget_id', 'department_id', 'allocated_amount')
    def _onchange_budget_summary(self):
        for record in self:
            record._update_budget_summary_values()

    @api.onchange('department_id')
    def _onchange_department_id_set_active_budget(self):
        for record in self:
            active_budget = record.general_budget_id
            if not active_budget:
                active_budget = self.env['budget.general'].search([
                    ('state', '=', 'active'),
                ], order='period_start desc, id desc', limit=1)

            if active_budget:
                record.general_budget_id = active_budget

            record._update_budget_summary_values()

    def _update_budget_summary_values(self):
        for record in self:
            general_remaining = 0.0
            current_department_total = 0.0

            active_budget = record.general_budget_id
            if not active_budget:
                active_budget = self.env['budget.general'].search([
                    ('state', '=', 'active'),
                ], order='period_start desc, id desc', limit=1)

            if active_budget:
                approved_budgets = active_budget.department_budget_ids.filtered(
                    lambda d: d.state == 'approved' and d.id != record.id
                )
                total_approved = sum(
                    approved_budgets.mapped('allocated_amount'))

                if record.state == 'approved':
                    general_remaining = active_budget.total_amount - \
                        total_approved - (record.allocated_amount or 0.0)
                else:
                    general_remaining = active_budget.total_amount - total_approved

            if active_budget and record.department_id:
                current_department_budgets = active_budget.department_budget_ids.filtered(
                    lambda d: d.department_id == record.department_id and d.state == 'approved' and d.id != record.id
                )
                current_department_total = sum(
                    current_department_budgets.mapped('remaining_balance'))

            record.general_budget_remaining = general_remaining

            if record.state == 'approved':
                final_department_budget = current_department_total + \
                    (record.remaining_balance or 0.0)
                record.current_department_budget = final_department_budget
                record.new_department_budget = final_department_budget
            else:
                record.current_department_budget = current_department_total
                record.new_department_budget = current_department_total + \
                    (record.allocated_amount or 0.0)

    @api.depends('allocated_amount', 'reservation_ids.amount', 'reservation_ids.state')
    def _compute_budget_usage(self):
        for record in self:
            reserved = sum(
                record.reservation_ids.filtered(
                    lambda r: r.state == 'reserved').mapped('amount')
            )
            used = sum(
                record.reservation_ids.filtered(
                    lambda r: r.state == 'used').mapped('amount')
            )
            record.reserved_amount = reserved
            record.used_amount = used
            record.remaining_balance = record.allocated_amount - reserved - used

    @api.constrains('allocated_amount')
    def _check_allocated_amount(self):
        for record in self:
            if record.allocated_amount <= 0:
                raise ValidationError(
                    'Department allocated amount must be greater than zero.')

    @api.model
    def create(self, vals):
        if not vals.get('general_budget_id'):
            active_budget = self.env['budget.general'].search([
                ('state', '=', 'active'),
            ], order='period_start desc, id desc', limit=1)

            if not active_budget:
                raise ValidationError(
                    'No active general budget was found. Please ask the Finance Manager to prepare the yearly budget pool.'
                )

            vals['general_budget_id'] = active_budget.id
        else:
            active_budget = self.env['budget.general'].browse(
                vals['general_budget_id'])

        if not vals.get('name'):
            department_name = 'Department'
            if vals.get('department_id'):
                department = self.env['hr.department'].browse(
                    vals['department_id'])
                department_name = department.name or 'Department'

            budget_year = ''
            if active_budget and active_budget.period_start:
                budget_year = active_budget.period_start.year

            vals['name'] = f'{department_name} Budget {budget_year}'

        return super().create(vals)

    def action_submit(self):
        for record in self:
            if record.state != 'draft':
                continue

            if self.env.user.has_group('ncst_budget_management.group_budget_finance_manager'):
                record.state = 'approved'
                record.approved_by = self.env.user
                record.approval_date = fields.Datetime.now()
            else:
                record.state = 'submitted'

    def action_approve(self):
        if not self.env.user.has_group('ncst_budget_management.group_budget_finance_manager'):
            raise ValidationError(
                'Only the Finance Manager can approve department budgets.')

        for record in self:
            if record.state != 'submitted':
                continue
            record.state = 'approved'
            record.approved_by = self.env.user
            record.approval_date = fields.Datetime.now()

    def action_reject(self):
        if not self.env.user.has_group('ncst_budget_management.group_budget_finance_manager'):
            raise ValidationError('Only the Finance Manager can reject department budgets.')

        self.ensure_one()

        if self.state != 'submitted':
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Budget Request',
            'res_model': 'budget.department.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_department_budget_id': self.id,
            },
        }
    
    
    def action_reset_to_draft(self):
        for record in self:
            if record.state == 'approved':
                raise ValidationError('Approved budget allocations cannot be reset to draft.')

            record.state = 'draft'
            record.approved_by = False
            record.approval_date = False
            record.rejected_by = False
            record.rejection_date = False
            record.rejection_reason = False
