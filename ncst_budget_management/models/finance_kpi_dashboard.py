from odoo import api, fields, models


class FinanceKPIDashboard(models.Model):
    _name = 'finance.kpi.dashboard'
    _description = 'Finance KPI Dashboard'

    name = fields.Char(string='Name', default='Finance KPI Dashboard')

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

    approved_reservations = fields.Integer(
        string='Approved Reservations',
        compute='_compute_kpi_values',
        store=False,
    )

    used_reservations = fields.Integer(
        string='Used Reservations',
        compute='_compute_kpi_values',
        store=False,
    )

    rejected_budget_requests = fields.Integer(
        string='Rejected Budget Requests',
        compute='_compute_kpi_values',
        store=False,
    )

    last_updated = fields.Datetime(
        string='Last Updated',
        compute='_compute_kpi_values',
        store=False,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )

    remaining_budget_status = fields.Selection(
        [
            ('normal', 'Normal'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
        ],
        string='Remaining Budget Status',
        compute='_compute_kpi_values',
        store=False,
    )

    remaining_budget_message = fields.Char(
        string='Remaining Budget Message',
        compute='_compute_kpi_values',
        store=False,
    )

    budget_chart_allocated = fields.Float(
        string='Budget Chart Allocated',
        compute='_compute_kpi_values',
        store=False,
    )

    budget_chart_reserved = fields.Float(
        string='Budget Chart Reserved',
        compute='_compute_kpi_values',
        store=False,
    )

    budget_chart_paid = fields.Float(
        string='Budget Chart Paid',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_type_1 = fields.Char(
        string='Top Expense Type 1',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_type_1_amount = fields.Monetary(
        string='Top Expense Type 1 Amount',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_type_2 = fields.Char(
        string='Top Expense Type 2',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_type_2_amount = fields.Monetary(
        string='Top Expense Type 2 Amount',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_type_3 = fields.Char(
        string='Top Expense Type 3',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_type_3_amount = fields.Monetary(
        string='Top Expense Type 3 Amount',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_department_1 = fields.Char(
        string='Top Expense Department 1',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_department_1_amount = fields.Monetary(
        string='Top Expense Department 1 Amount',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_department_2 = fields.Char(
        string='Top Expense Department 2',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_department_2_amount = fields.Monetary(
        string='Top Expense Department 2 Amount',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_department_3 = fields.Char(
        string='Top Expense Department 3',
        compute='_compute_kpi_values',
        store=False,
    )

    top_expense_department_3_amount = fields.Monetary(
        string='Top Expense Department 3 Amount',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    expenses_this_month = fields.Monetary(
        string='Expenses This Month',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    expenses_this_year = fields.Monetary(
        string='Expenses This Year',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    general_budget_this_year = fields.Monetary(
        string='General Budget This Year',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    reserved_budget_percentage = fields.Float(
        string='Reserved Budget Percentage',
        compute='_compute_kpi_values',
        store=False,
    )

    paid_budget_percentage = fields.Float(
        string='Paid Budget Percentage',
        compute='_compute_kpi_values',
        store=False,
    )

    remaining_budget_percentage = fields.Float(
        string='Remaining Budget Percentage',
        compute='_compute_kpi_values',
        store=False,
    )

    average_monthly_expense = fields.Monetary(
        string='Average Monthly Expense',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    projected_annual_expense = fields.Monetary(
        string='Projected Annual Expense',
        currency_field='currency_id',
        compute='_compute_kpi_values',
        store=False,
    )

    highest_expense_type_summary = fields.Char(
        string='Highest Expense Type Summary',
        compute='_compute_kpi_values',
        store=False,
    )

    highest_department_summary = fields.Char(
        string='Highest Department Summary',
        compute='_compute_kpi_values',
        store=False,
    )

    alert_1 = fields.Char(
        string='Alert 1',
        compute='_compute_kpi_values',
        store=False,
    )

    alert_2 = fields.Char(
        string='Alert 2',
        compute='_compute_kpi_values',
        store=False,
    )

    alert_3 = fields.Char(
        string='Alert 3',
        compute='_compute_kpi_values',
        store=False,
    )

    this_month_of_year_percentage = fields.Float(
        string='This Month of Year Percentage',
        compute='_compute_kpi_values',
        store=False,
    )

    approved_reservations_percentage = fields.Float(
        string='Approved Reservations Percentage',
        compute='_compute_kpi_values',
        store=False,
    )

    used_reservations_percentage = fields.Float(
        string='Used Reservations Percentage',
        compute='_compute_kpi_values',
        store=False,
    )

    @api.depends_context('uid')
    def _compute_kpi_values(self):
        budget_department_model = self.env['budget.department']
        budget_reservation_model = self.env['budget.reservation']
        expense_request_model = self.env['expense.request']
        general_budget_model = self.env['budget.general']

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

        expense_type_totals = {}
        for expense in paid_expenses:
            expense_type_name = expense.expense_type_id.name if expense.expense_type_id else 'Unknown'
            expense_type_totals[expense_type_name] = expense_type_totals.get(expense_type_name, 0.0) + expense.amount

        sorted_expense_types = sorted(
            expense_type_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )

        expense_department_totals = {}
        for expense in paid_expenses:
            department_name = expense.department_id.name if expense.department_id else 'Unknown'
            expense_department_totals[department_name] = expense_department_totals.get(department_name, 0.0) + expense.amount

        sorted_expense_departments = sorted(
            expense_department_totals.items(),
            key=lambda item: item[1],
            reverse=True
        )

        dept_1_name = sorted_expense_departments[0][0] if len(sorted_expense_departments) > 0 else 'No Data'
        dept_1_amount = sorted_expense_departments[0][1] if len(sorted_expense_departments) > 0 else 0.0
        dept_2_name = sorted_expense_departments[1][0] if len(sorted_expense_departments) > 1 else 'No Data'
        dept_2_amount = sorted_expense_departments[1][1] if len(sorted_expense_departments) > 1 else 0.0
        dept_3_name = sorted_expense_departments[2][0] if len(sorted_expense_departments) > 2 else 'No Data'
        dept_3_amount = sorted_expense_departments[2][1] if len(sorted_expense_departments) > 2 else 0.0

        top_1_name = sorted_expense_types[0][0] if len(sorted_expense_types) > 0 else 'No Data'
        top_1_amount = sorted_expense_types[0][1] if len(sorted_expense_types) > 0 else 0.0
        top_2_name = sorted_expense_types[1][0] if len(sorted_expense_types) > 1 else 'No Data'
        top_2_amount = sorted_expense_types[1][1] if len(sorted_expense_types) > 1 else 0.0
        top_3_name = sorted_expense_types[2][0] if len(sorted_expense_types) > 2 else 'No Data'
        top_3_amount = sorted_expense_types[2][1] if len(sorted_expense_types) > 2 else 0.0

        pending_expense_requests = expense_request_model.search_count([
            ('state', 'in', ['submitted', 'approved_manager'])
        ])

        pending_reservations = budget_reservation_model.search_count([
            ('state', '=', 'submitted')
        ])

        approved_reservations = budget_reservation_model.search_count([
            ('state', '=', 'reserved')
        ])

        used_reservations = budget_reservation_model.search_count([
            ('state', '=', 'used')
        ])

        rejected_budget_requests = budget_department_model.search_count([
            ('state', '=', 'rejected')
        ])

        remaining_budget = total_budget_allocated - total_reserved_amount - total_paid_expenses

        if total_budget_allocated > 0:
            remaining_ratio = remaining_budget / total_budget_allocated
            reserved_budget_percentage = (total_reserved_amount / total_budget_allocated) * 100
            paid_budget_percentage = (total_paid_expenses / total_budget_allocated) * 100
            remaining_budget_percentage = (remaining_budget / total_budget_allocated) * 100
        else:
            remaining_ratio = 0
            reserved_budget_percentage = 0.0
            paid_budget_percentage = 0.0
            remaining_budget_percentage = 0.0

        if remaining_budget <= 0:
            remaining_budget_status = 'danger'
            remaining_budget_message = 'Budget exhausted or exceeded'
        elif remaining_ratio <= 0.2:
            remaining_budget_status = 'warning'
            remaining_budget_message = 'Remaining budget is low'
        else:
            remaining_budget_status = 'normal'
            remaining_budget_message = 'Budget level is healthy'

        now_value = fields.Datetime.now()
        today = fields.Date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)
        current_year = today.year

        general_budgets_this_year = general_budget_model.search([
            ('period_start', '>=', fields.Date.to_date(f'{current_year}-01-01')),
            ('period_end', '<=', fields.Date.to_date(f'{current_year}-12-31')),
            ('state', '=', 'active'),
            ('company_id', '=', self.env.company.id),
        ])
        general_budget_this_year = sum(general_budgets_this_year.mapped('total_amount'))

        expenses_this_month_records = expense_request_model.search([
            ('state', '=', 'paid'),
            ('expense_date', '>=', month_start)
        ])

        expenses_this_year_records = expense_request_model.search([
            ('state', '=', 'paid'),
            ('expense_date', '>=', year_start)
        ])

        total_expenses_month = sum(expenses_this_month_records.mapped('amount'))
        total_expenses_year = sum(expenses_this_year_records.mapped('amount'))

        current_month_number = today.month if today.month else 1
        average_monthly_expense = total_expenses_year / current_month_number if current_month_number else 0.0
        projected_annual_expense = average_monthly_expense * 12

        if total_expenses_year > 0:
            this_month_of_year_percentage = (total_expenses_month / total_expenses_year) * 100
        else:
            this_month_of_year_percentage = 0.0

        total_reservation_activity = approved_reservations + used_reservations
        if total_reservation_activity > 0:
            approved_reservations_percentage = (approved_reservations / total_reservation_activity) * 100
            used_reservations_percentage = (used_reservations / total_reservation_activity) * 100
        else:
            approved_reservations_percentage = 0.0
            used_reservations_percentage = 0.0

        highest_expense_type_summary = (
            f'{top_1_name} is the highest paid expense type.'
            if top_1_name != 'No Data'
            else 'No paid expense type data yet.'
        )

        highest_department_summary = (
            f'{dept_1_name} has the highest paid expenses.'
            if dept_1_name != 'No Data'
            else 'No department expense data yet.'
        )

        alerts = []

        if not general_budgets_this_year:
            alerts.append('No active general budget found for this year.')

        if remaining_budget <= 0:
            alerts.append('Budget has been exhausted or exceeded.')
        elif remaining_ratio <= 0.2:
            alerts.append('Remaining budget is below 20%.')

        if pending_expense_requests > 0:
            alerts.append(f'{pending_expense_requests} expense request(s) are waiting for action.')

        if pending_reservations > 0:
            alerts.append(f'{pending_reservations} reservation request(s) are still pending.')

        if top_1_name != 'No Data':
            alerts.append(f'Highest paid expense type is {top_1_name}.')

        alert_1 = alerts[0] if len(alerts) > 0 else 'No major alerts right now.'
        alert_2 = alerts[1] if len(alerts) > 1 else 'Budget activity is being monitored normally.'
        alert_3 = alerts[2] if len(alerts) > 2 else 'Dashboard values were updated successfully.'

        for record in self:
            record.total_budget_allocated = total_budget_allocated
            record.total_reserved_amount = total_reserved_amount
            record.total_paid_expenses = total_paid_expenses
            record.remaining_budget = remaining_budget
            record.pending_expense_requests = pending_expense_requests
            record.pending_reservations = pending_reservations
            record.approved_reservations = approved_reservations
            record.used_reservations = used_reservations
            record.rejected_budget_requests = rejected_budget_requests
            record.last_updated = now_value
            record.remaining_budget_status = remaining_budget_status
            record.remaining_budget_message = remaining_budget_message
            record.budget_chart_allocated = total_budget_allocated
            record.budget_chart_reserved = total_reserved_amount
            record.budget_chart_paid = total_paid_expenses
            record.top_expense_type_1 = top_1_name
            record.top_expense_type_1_amount = top_1_amount
            record.top_expense_type_2 = top_2_name
            record.top_expense_type_2_amount = top_2_amount
            record.top_expense_type_3 = top_3_name
            record.top_expense_type_3_amount = top_3_amount
            record.top_expense_department_1 = dept_1_name
            record.top_expense_department_1_amount = dept_1_amount
            record.top_expense_department_2 = dept_2_name
            record.top_expense_department_2_amount = dept_2_amount
            record.top_expense_department_3 = dept_3_name
            record.top_expense_department_3_amount = dept_3_amount
            record.expenses_this_month = total_expenses_month
            record.expenses_this_year = total_expenses_year
            record.general_budget_this_year = general_budget_this_year
            record.reserved_budget_percentage = reserved_budget_percentage
            record.paid_budget_percentage = paid_budget_percentage
            record.remaining_budget_percentage = remaining_budget_percentage
            record.average_monthly_expense = average_monthly_expense
            record.projected_annual_expense = projected_annual_expense
            record.highest_expense_type_summary = highest_expense_type_summary
            record.highest_department_summary = highest_department_summary
            record.alert_1 = alert_1
            record.alert_2 = alert_2
            record.alert_3 = alert_3
            record.this_month_of_year_percentage = this_month_of_year_percentage
            record.approved_reservations_percentage = approved_reservations_percentage
            record.used_reservations_percentage = used_reservations_percentage

    @api.model
    def get_dashboard_record(self):
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({
                'name': 'Finance KPI Dashboard',
            })
        return dashboard
    

    def action_print_dashboard_pdf(self):
        dashboard = self[:1]
        if not dashboard:
            dashboard = self.get_dashboard_record()
        return self.env.ref(
            'ncst_budget_management.action_report_finance_kpi_dashboard'
        ).report_action(dashboard)