from odoo import fields, models


class ProjectAssignmentTeam(models.Model):
    _name = 'project.assignment.team'
    _description = 'Project Assignment Team'
    _order = 'name'

    name = fields.Char(
        string='Team Name',
        required=True
    )

    active = fields.Boolean(
        default=True
    )

    project_type_ids = fields.Many2many(
        'crm.project.type',
        'project_assignment_team_type_rel',
        'team_id',
        'project_type_id',
        string='Specialized Project Types',
    )

    employee_ids = fields.Many2many(
        'hr.employee',
        'project_assignment_team_employee_rel',
        'team_id',
        'employee_id',
        string='Team Employees',
        domain="[('department_id.name', '=', 'AI Research and Development')]",
    )

    assignment_ids = fields.One2many(
        'project.team.assignment',
        'team_id',
        string='Project Assignments',
        readonly=True,
    )

    notes = fields.Text(
        string='Notes'
    )