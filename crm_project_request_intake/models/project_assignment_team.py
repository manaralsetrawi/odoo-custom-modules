from odoo import api, fields, models


class ProjectAssignmentTeam(models.Model):
    _name = 'project.assignment.team'
    _description = 'Project Assignment Team'
    _order = 'name'

    name = fields.Char(string='Team Name', required=True)
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')

    project_type_ids = fields.Many2many(
        'crm.project.type',
        'project_assignment_team_type_rel',
        'team_id',
        'project_type_id',
        string='Supported Project Types',
    )

    member_ids = fields.Many2many(
        'hr.employee',
        'project_assignment_team_employee_rel',
        'team_id',
        'employee_id',
        string='Team Members',
        domain="[('department_id.name', '=', 'AI Research and Development')]",
    )

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

    assignment_ids = fields.One2many(
        'project.team.assignment',
        'team_id',
        string='Assignments',
    )

    @api.depends('monthly_capacity', 'assignment_ids.workload_percentage')
    def _compute_remaining_capacity(self):
        for team in self:
            total_workload = sum(team.assignment_ids.mapped('workload_percentage'))
            team.remaining_capacity = team.monthly_capacity - total_workload