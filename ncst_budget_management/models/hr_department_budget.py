from odoo import api, fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    budget_currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_budget_overview',
        string='Currency',
    )
    current_budget_amount = fields.Monetary(
        string='Current Budget',
        compute='_compute_budget_overview',
        currency_field='budget_currency_id',
    )
    approved_allocation_count = fields.Integer(
        string='Approved Allocations',
        compute='_compute_budget_overview',
    )

    def _compute_budget_overview(self):
        active_budget = self.env['budget.general'].search([
            ('state', '=', 'active'),
        ], order='period_start desc, id desc', limit=1)

        for department in self:
            if not active_budget:
                department.budget_currency_id = self.env.company.currency_id
                department.current_budget_amount = 0.0
                department.approved_allocation_count = 0
                continue

            approved_allocations = active_budget.department_budget_ids.filtered(
                lambda d: d.department_id == department and d.state == 'approved'
            )

            department.budget_currency_id = active_budget.currency_id
            department.current_budget_amount = sum(approved_allocations.mapped('allocated_amount'))
            department.approved_allocation_count = len(approved_allocations)