from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    monthly_capacity = fields.Float(
        string='Monthly Capacity (%)',
        default=100.0,
        required=True,
    )

    remaining_capacity = fields.Float(
        string='Remaining Capacity (%)',
        compute='_compute_remaining_capacity',
        store=False,
    )

    @api.depends('monthly_capacity')
    def _compute_remaining_capacity(self):
        AssignmentLine = self.env['project.team.assignment.line']
        for employee in self:
            lines = AssignmentLine.search([
                ('employee_id', '=', employee.id),
            ])
            used_capacity = sum(lines.mapped('workload_percentage'))
            employee.remaining_capacity = employee.monthly_capacity - used_capacity