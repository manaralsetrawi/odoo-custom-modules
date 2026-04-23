from odoo import fields, models


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