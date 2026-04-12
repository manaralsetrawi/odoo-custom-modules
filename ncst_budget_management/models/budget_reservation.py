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

    @api.onchange('department_id')
    def _onchange_department_id(self):
        for record in self:
            record.department_budget_id = False
            record.general_budget_id = False
            record.currency_id = False

            if not record.department_id:
                return

            department_budget = self.env['budget.department'].search([
                ('department_id', '=', record.department_id.id),
                ('state', '=', 'approved'),
            ], order='id desc', limit=1)

            if department_budget:
                record.department_budget_id = department_budget.id
                record.general_budget_id = department_budget.general_budget_id.id if department_budget.general_budget_id else False
                record.currency_id = department_budget.currency_id.id if department_budget.currency_id else False

    @api.model
    def create(self, vals):
        if vals.get('department_id') and not vals.get('department_budget_id'):
            department_budget = self.env['budget.department'].search([
                ('department_id', '=', vals['department_id']),
                ('state', '=', 'approved'),
            ], order='id desc', limit=1)

            if not department_budget:
                raise ValidationError(
                    'No approved department budget was found for the selected department.'
                )

            vals['department_budget_id'] = department_budget.id
            vals['general_budget_id'] = department_budget.general_budget_id.id if department_budget.general_budget_id else False
            vals['currency_id'] = department_budget.currency_id.id if department_budget.currency_id else False

        if vals.get('department_budget_id'):
            department_budget = self.env['budget.department'].browse(vals['department_budget_id'])
            if department_budget.state != 'approved':
                raise ValidationError('Reservations can only be created for approved department budgets.')

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('budget.reservation') or 'New'

        return super().create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError('Reservation amount must be greater than zero.')

    @api.constrains('department_budget_id', 'amount', 'state')
    def _check_available_balance(self):
        for record in self:
            if not record.department_budget_id:
                continue

            if record.state == 'reserved':
                if record.amount > record.department_budget_id.remaining_balance:
                    raise ValidationError(
                        'The reservation amount exceeds the available department budget balance.'
                    )

    def action_submit(self):
        for record in self:
            if record.state != 'draft':
                continue

            if not record.department_id:
                raise ValidationError('Please select a department.')

            if not record.department_budget_id:
                raise ValidationError('No approved department budget was found for the selected department.')

            if record.amount <= 0:
                raise ValidationError('Reservation amount must be greater than zero.')

            if record.amount > record.department_budget_id.remaining_balance:
                raise ValidationError(
                    'The reservation amount exceeds the available department budget balance.'
                )

            if self.env.user.has_group('ncst_budget_management.group_budget_finance_manager'):
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

            if record.amount > record.department_budget_id.remaining_balance:
                raise ValidationError(
                    'The reservation amount exceeds the available department budget balance.'
                )

            record.state = 'reserved'
            record.reserved_by = self.env.user
            record.reserved_date = fields.Datetime.now()

    def action_mark_used(self):
        if not self.env.user.has_group('ncst_budget_management.group_budget_finance_manager'):
            raise ValidationError('Only the Finance Manager can mark reservations as used.')

        for record in self:
            if record.state != 'reserved':
                continue

            record.state = 'used'
            record.used_by = self.env.user
            record.used_date = fields.Datetime.now()

    def action_cancel_reservation(self):
        for record in self:
            if record.state not in ['draft', 'submitted', 'reserved']:
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