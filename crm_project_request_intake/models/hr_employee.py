from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    monthly_capacity = fields.Float(
        string='Monthly Capacity (%)',
        default=100.0,
        required=True,
    )

    remaining_capacity = fields.Float(
        string='Monthly Remaining Capacity (%)',
        compute='_compute_remaining_capacity',
        store=False,
    )

    assignment_line_ids = fields.One2many(
        'project.team.assignment.line',
        'employee_id',
        string='Project Assignment Lines',
    )

    @api.depends(
        'monthly_capacity',
        'assignment_line_ids.monthly_reserved_percentage',
    )
    def _compute_remaining_capacity(self):
        for employee in self:
            used_capacity = sum(employee.assignment_line_ids.mapped('monthly_reserved_percentage'))
            employee.remaining_capacity = employee.monthly_capacity - used_capacity