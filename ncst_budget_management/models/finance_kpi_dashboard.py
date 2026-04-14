from odoo import api, fields, models


class FinanceKPIDashboard(models.Model):
    _name = 'finance.kpi.dashboard'
    _description = 'Finance KPI Dashboard'

    name = fields.Char(default='Finance KPI Dashboard')

    total_budget_allocated = fields.Monetary(
        string='Total Budget Allocated',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    total_reserved_amount = fields.Monetary(
        string='Total Reserved Amount',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    total_paid_expenses = fields.Monetary(
        string='Total Paid Expenses',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    remaining_budget = fields.Monetary(
        string='Remaining Budget',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    pending_expense_requests = fields.Integer(
        string='Pending Expense Requests',
        compute='_compute_kpi_values',
        store=False,
    )

    pending_reservations = fields.Integer(
        string='Pending Reservations',
        compute='_compute_kpi_values',
        store=False,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends_context('uid')
    def _compute_kpi_values(self):
        budget_department_model = self.env['budget.department']
        budget_reservation_model = self.env['budget.reservation']
        expense_request_model = self.env['expense.request']

        approved_budget_allocations = budget_department_model.search([
            ('state', '=', 'approved')
        ])
        total_budget_allocated = sum(approved_budget_allocations.mapped('allocated_amount'))

        reserved_reservations = budget_reservation_model.search([
            ('state', '=', 'reserved')
        ])
        total_reserved_amount = sum(reserved_reservations.mapped('amount'))

        paid_expenses = expense_request_model.search([
            ('state', '=', 'paid')
        ])
        total_paid_expenses = sum(paid_expenses.mapped('amount'))

        pending_expense_requests = expense_request_model.search_count([
            ('state', 'in', ['submitted', 'approved_manager'])
        ])

        pending_reservations = budget_reservation_model.search_count([
            ('state', '=', 'submitted')
        ])

        remaining_budget = total_budget_allocated - total_reserved_amount - total_paid_expenses

        for record in self:
            record.total_budget_allocated = total_budget_allocated
            record.total_reserved_amount = total_reserved_amount
            record.total_paid_expenses = total_paid_expenses
            record.remaining_budget = remaining_budget
            record.pending_expense_requests = pending_expense_requests
            record.pending_reservations = pending_reservations

    @api.model
    def create_dashboard_record_if_missing(self):
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({
                'name': 'Finance KPI Dashboard'
            })
        return dashboard