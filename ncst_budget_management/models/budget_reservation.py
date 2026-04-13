from odoo import api, fields, models # type: ignore
from odoo.exceptions import ValidationError # type: ignore


class BudgetReservation(models.Model):
    _name = 'budget.reservation'
    _description = 'Budget Reservation'
    _order = 'id desc'

    name = fields.Char(
        string='Reservation Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    date = fields.Date(
        string='Reservation Date',
        default=fields.Date.context_today,
        required=True,
    )
    general_budget_id = fields.Many2one(
        'budget.general',
        string='General Budget',
        readonly=True,
        ondelete='cascade',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
    )
    department_budget_id = fields.Many2one(
        'budget.department',
        string='Department Budget',
        readonly=True,
        ondelete='cascade',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )

    department_budget_amount = fields.Monetary(
        string='Department Budget',
        currency_field='currency_id',
        compute='_compute_department_budget_amount',
        store=False,
    )

    line_ids = fields.One2many(
    'budget.reservation.line',
    'reservation_id',
    string='Reservation Lines',
    )
    
    
    amount = fields.Monetary(
        string='Reservation Amount',
        required=True,
        currency_field='currency_id',
    )
    request_ref = fields.Char(
        string='Related Request Reference',
    )
    description = fields.Text(
        string='Description',
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
    )

    can_cancel = fields.Boolean(
    string='Can Cancel',
    compute='_compute_action_access',
    )

    can_mark_used = fields.Boolean(
        string='Can Mark Used',
        compute='_compute_action_access',
    )

    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    created_date = fields.Datetime(
        string='Created On',
        default=fields.Datetime.now,
        readonly=True,
    )
    submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
    )
    submitted_date = fields.Datetime(
        string='Submitted On',
        readonly=True,
    )
    reserved_by = fields.Many2one(
        'res.users',
        string='Reserved By',
        readonly=True,
    )
    reserved_date = fields.Datetime(
        string='Reserved On',
        readonly=True,
    )
    used_by = fields.Many2one(
        'res.users',
        string='Marked Used By',
        readonly=True,
    )
    used_date = fields.Datetime(
        string='Marked Used On',
        readonly=True,
    )
    cancelled_by = fields.Many2one(
        'res.users',
        string='Cancelled By',
        readonly=True,
    )
    cancelled_date = fields.Datetime(
        string='Cancelled On',
        readonly=True,
    )
    cancel_reason = fields.Text(
        string='Cancellation Reason',
        readonly=True,
    )

    @api.depends('department_id')
    def _compute_department_budget_amount(self):
        for record in self:
            record.department_budget_amount = 0.0
            record.currency_id = False

            if not record.department_id:
                continue

            department_budgets = self.env['budget.department'].search([
                ('department_id', '=', record.department_id.id),
                ('state', '=', 'approved'),
                ('general_budget_id.state', '=', 'active'),
            ])

            record.department_budget_amount = sum(department_budgets.mapped('remaining_balance'))

            if department_budgets:
                record.currency_id = department_budgets[0].currency_id.id



    @api.onchange('department_id')
    def _onchange_department_id(self):
        for record in self:
            record.department_budget_id = False
            record.general_budget_id = False
            record.currency_id = False
            record.line_ids = [(5, 0, 0)]

            if not record.department_id:
                return

            department_budgets = self.env['budget.department'].search([
                ('department_id', '=', record.department_id.id),
                ('state', '=', 'approved'),
                ('general_budget_id.state', '=', 'active'),
            ], order='approval_date asc, id asc')

            if department_budgets:
                first_budget = department_budgets[0]
                record.department_budget_id = first_budget.id
                record.general_budget_id = first_budget.general_budget_id.id if first_budget.general_budget_id else False
                record.currency_id = first_budget.currency_id.id if first_budget.currency_id else False


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('budget.reservation') or 'New'

        record = super().create(vals)

        if record.department_id:
            department_budgets = self.env['budget.department'].search([
                ('department_id', '=', record.department_id.id),
                ('state', '=', 'approved'),
                ('general_budget_id.state', '=', 'active'),
            ], order='approval_date asc, id asc', limit=1)

            if department_budgets:
                record.department_budget_id = department_budgets.id
                record.general_budget_id = department_budgets.general_budget_id.id if department_budgets.general_budget_id else False
                record.currency_id = department_budgets.currency_id.id if department_budgets.currency_id else False

        return record


    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError('Reservation amount must be greater than zero.')


    @api.constrains('department_id', 'amount', 'state')
    def _check_available_balance(self):
        for record in self:
            if not record.department_id:
                continue

            if record.state == 'reserved' and record.amount > record.department_budget_amount:
                raise ValidationError(
                    'The reservation amount exceeds the available department budget balance.'
                )


    def _compute_action_access(self):
        for record in self:
            is_manager = self.env.user.has_group('ncst_budget_management.group_budget_finance_manager')
            is_creator = record.created_by == self.env.user

            record.can_cancel = record.state == 'reserved' and (is_creator or is_manager)
            record.can_mark_used = record.state == 'reserved' and (is_creator or is_manager)


    def action_submit(self):
        for record in self:
            if record.state != 'draft':
                continue

            if not record.department_id:
                raise ValidationError('Please select a department.')

            if record.amount <= 0:
                raise ValidationError('Reservation amount must be greater than zero.')

            if record.amount > record.department_budget_amount:
                raise ValidationError(
                    'The reservation amount exceeds the available department budget balance.'
                )

            if self.env.user.has_group('ncst_budget_management.group_budget_finance_manager'):
                record._allocate_reservation_lines()
                record.state = 'reserved'
                record.submitted_by = self.env.user
                record.submitted_date = fields.Datetime.now()
                record.reserved_by = self.env.user
                record.reserved_date = fields.Datetime.now()
            else:
                record.state = 'submitted'
                record.submitted_by = self.env.user
                record.submitted_date = fields.Datetime.now() 

    def action_approve_reservation(self):
        if not self.env.user.has_group('ncst_budget_management.group_budget_finance_manager'):
            raise ValidationError('Only the Finance Manager can approve reservations.')

        for record in self:
            if record.state != 'submitted':
                continue

            if record.amount > record.department_budget_amount:
                raise ValidationError(
                    'The reservation amount exceeds the available department budget balance.'
                )

            record._allocate_reservation_lines()
            record.state = 'reserved'
            record.reserved_by = self.env.user
            record.reserved_date = fields.Datetime.now()


    def action_mark_used(self):
        for record in self:
            is_manager = self.env.user.has_group('ncst_budget_management.group_budget_finance_manager')
            is_creator = record.created_by == self.env.user

            if not (is_manager or is_creator):
                raise ValidationError('Only the reservation creator or the Finance Manager can mark this reservation as used.')

            if record.state != 'reserved':
                continue

            record.state = 'used'
            record.used_by = self.env.user
            record.used_date = fields.Datetime.now()

    def action_cancel_reservation(self):
        for record in self:
            is_manager = self.env.user.has_group('ncst_budget_management.group_budget_finance_manager')
            is_creator = record.created_by == self.env.user

            if not (is_manager or is_creator):
                raise ValidationError('Only the reservation creator or the Finance Manager can cancel this reservation.')

            if record.state != 'reserved':
                continue

            return {
                'type': 'ir.actions.act_window',
                'name': 'Cancel Reservation',
                'res_model': 'budget.reservation.cancel.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_budget_reservation_id': record.id,
                },
            }

    def action_reset_to_draft(self):
        for record in self:
            if record.state in ['used', 'reserved']:
                raise ValidationError('Reserved or used reservations cannot be reset to draft directly.')

            record.state = 'draft'
            record.submitted_by = False
            record.submitted_date = False
            record.cancelled_by = False
            record.cancelled_date = False
            record.cancel_reason = False

    def _get_available_department_budgets(self):
        self.ensure_one()

        return self.env['budget.department'].search([
            ('department_id', '=', self.department_id.id),
            ('state', '=', 'approved'),
            ('general_budget_id.state', '=', 'active'),
            ('remaining_balance', '>', 0),
        ], order='approval_date asc, id asc')
    

    def _allocate_reservation_lines(self):
        for record in self:
            if not record.department_id:
                raise ValidationError('Please select a department.')

            if record.amount <= 0:
                raise ValidationError('Reservation amount must be greater than zero.')

            available_budgets = record._get_available_department_budgets()

            if not available_budgets:
                raise ValidationError(
                    'No approved department budget with available balance was found for the selected department.'
                )

            total_available = sum(available_budgets.mapped('remaining_balance'))
            if record.amount > total_available:
                raise ValidationError(
                    'The reservation amount exceeds the available department budget balance.'
                )

            # remove old lines before rebuilding
            record.line_ids.unlink()

            remaining_to_allocate = record.amount
            first_budget = False

            for budget in available_budgets:
                if remaining_to_allocate <= 0:
                    break

                available = budget.remaining_balance
                if available <= 0:
                    continue

                allocate_now = min(remaining_to_allocate, available)

                self.env['budget.reservation.line'].create({
                    'reservation_id': record.id,
                    'department_budget_id': budget.id,
                    'amount': allocate_now,
                })

                if not first_budget:
                    first_budget = budget

                remaining_to_allocate -= allocate_now

            if remaining_to_allocate > 0:
                raise ValidationError(
                    'The reservation could not be fully allocated across department budgets.'
                )

            # optional: keep one linked budget only for compatibility/reference
            record.department_budget_id = first_budget.id if first_budget else False
            record.general_budget_id = first_budget.general_budget_id.id if first_budget and first_budget.general_budget_id else False
            record.currency_id = first_budget.currency_id.id if first_budget and first_budget.currency_id else False