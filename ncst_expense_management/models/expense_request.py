from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ExpenseRequest(models.Model):
    _name = 'expense.request'
    _description = 'Expense Request'
    _order = 'id desc'

    name = fields.Char(
        string='Expense Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self._default_employee(),
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        store=True,
        readonly=True,
    )

    manager_id = fields.Many2one(
    'hr.employee',
    string='Manager',
    compute='_compute_manager_id',
    store=True,
    readonly=True,
)

    manager_user_id = fields.Many2one(
        'res.users',
        string='Manager User',
        compute='_compute_manager_id',
        store=True,
        readonly=True,
    )

    expense_type_id = fields.Many2one(
        'expense.type',
        string='Expense Type',
        required=True,
    )

    expense_date = fields.Date(
        string='Expense Date',
        default=fields.Date.context_today,
        required=True,
    )

    amount = fields.Monetary(
        string='Amount',
        required=True,
        currency_field='currency_id',
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    description = fields.Text(
        string='Description',
        required=True,
    )

    attachment = fields.Binary(string='Attachment')
    attachment_name = fields.Char(string='Attachment Name')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved_manager', 'Approved by Manager'),
        ('approved_finance', 'Approved by Finance'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', required=True)

    budget_reservation_id = fields.Many2one(
        'budget.reservation',
        string='Budget Reservation',
        readonly=True,
        copy=False,
    )

    submitted_by = fields.Many2one('res.users', string='Submitted By', readonly=True)
    submitted_date = fields.Datetime(string='Submitted On', readonly=True)

    manager_approved_by = fields.Many2one('res.users', string='Manager Approved By', readonly=True)
    manager_approval_date = fields.Datetime(string='Manager Approval Date', readonly=True)

    finance_approved_by = fields.Many2one('res.users', string='Finance Approved By', readonly=True)
    finance_approval_date = fields.Datetime(string='Finance Approval Date', readonly=True)

    paid_by = fields.Many2one('res.users', string='Paid By', readonly=True)
    paid_date = fields.Datetime(string='Paid Date', readonly=True)

    rejected_by = fields.Many2one('res.users', string='Rejected By', readonly=True)
    rejected_date = fields.Datetime(string='Rejected Date', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)

    @api.model
    def _default_employee(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)

    @api.depends('employee_id')
    def _compute_manager_id(self):
        for record in self:
            manager = False

            if record.employee_id and record.employee_id.parent_id:
                manager = record.employee_id.parent_id

            record.manager_id = manager
            record.manager_user_id = manager.user_id.id if manager and manager.user_id else False


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('expense.request') or 'New'
        return super().create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError('Expense amount must be greater than zero.')

    def action_submit(self):
        for record in self:
            if not record.attachment:
                raise ValidationError('Please attach a receipt or invoice before submitting.')

            record.state = 'submitted'
            record.submitted_by = self.env.user
            record.submitted_date = fields.Datetime.now()

    def action_manager_approve(self):
        for record in self:
            if record.state != 'submitted':
                continue

            if not record.manager_user_id or record.manager_user_id != self.env.user:
                raise ValidationError('Only the employee manager can approve this expense request.')

            record.state = 'approved_manager'
            record.manager_approved_by = self.env.user
            record.manager_approval_date = fields.Datetime.now()

    def action_finance_approve(self):
        if not self.env.user.has_group('ncst_expense_management.group_expense_finance'):
            raise ValidationError('Only Finance can approve expense requests.')

        for record in self:
            if record.state != 'approved_manager':
                continue

            reservation = self.env['budget.reservation'].create({
                'department_id': record.department_id.id,
                'amount': record.amount,
                'description': record.description,
                'request_ref': record.name,
            })
            reservation.action_submit()

            record.budget_reservation_id = reservation.id
            record.state = 'approved_finance'
            record.finance_approved_by = self.env.user
            record.finance_approval_date = fields.Datetime.now()

    def action_mark_paid(self):
        for record in self:
            if record.state != 'approved_finance':
                continue

            if record.budget_reservation_id and record.budget_reservation_id.state == 'reserved':
                record.budget_reservation_id.action_mark_used()

            record.state = 'paid'
            record.paid_by = self.env.user
            record.paid_date = fields.Datetime.now()