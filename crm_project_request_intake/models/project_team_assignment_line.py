from odoo import api, fields, models


class ProjectTeamAssignmentLine(models.Model):
    _name = 'project.team.assignment.line'
    _description = 'Project Team Assignment Line'

    assignment_id = fields.Many2one(
        'project.team.assignment',
        string='Assignment',
        required=True,
        ondelete='cascade',
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
    )

    employee_team_id = fields.Many2one(
        'project.assignment.team',
        string='Employee Team',
        compute='_compute_employee_team_id',
        store=False,
    )

    workload_percentage = fields.Float(
        string='Total Allocation (%)',
        required=True,
        default=0.0,
    )

    monthly_reserved_percentage = fields.Float(
        string='Monthly Reserved (%)',
        compute='_compute_monthly_reserved_percentage',
        store=False,
    )

    notes = fields.Char(string='Notes')

    @api.depends('employee_id')
    def _compute_employee_team_id(self):
        Team = self.env['project.assignment.team']
        for line in self:
            team = Team.search([
                ('member_ids', 'in', line.employee_id.id)
            ], limit=1)
            line.employee_team_id = team.id if team else False

    @api.depends(
        'workload_percentage',
        'assignment_id.planned_start_date',
        'assignment_id.planned_end_date',
    )
    def _compute_monthly_reserved_percentage(self):
        for line in self:
            months = 1
            if line.assignment_id.planned_start_date and line.assignment_id.planned_end_date:
                start = line.assignment_id.planned_start_date
                end = line.assignment_id.planned_end_date
                months = ((end.year - start.year) * 12) + (end.month - start.month) + 1
                if months < 1:
                    months = 1
            line.monthly_reserved_percentage = line.workload_percentage / months