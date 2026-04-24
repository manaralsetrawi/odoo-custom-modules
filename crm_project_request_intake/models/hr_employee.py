from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_assignment_ids = fields.Many2many(
        'project.team.assignment',
        string='Project Assignments',
        compute='_compute_project_assignment_ids',
        readonly=True,
    )

    def _compute_project_assignment_ids(self):
        Assignment = self.env['project.team.assignment']

        for employee in self:
            employee.project_assignment_ids = Assignment.search([
                ('employee_ids', 'in', employee.id)
            ])