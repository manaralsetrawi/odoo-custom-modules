from odoo import fields, models


class ProjectTeamAssignment(models.Model):
    _name = 'project.team.assignment'
    _description = 'Project Team Assignment'
    _order = 'planned_start_date desc'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Opportunity',
        required=True,
        ondelete='cascade',
    )

    team_id = fields.Many2one(
        'project.assignment.team',
        string='Assigned Team',
        required=True,
        ondelete='cascade',
    )

    assigned_employee_ids = fields.Many2many(
        'hr.employee',
        'project_team_assignment_employee_rel',
        'assignment_id',
        'employee_id',
        string='Assigned Employees',
    )

    planned_start_date = fields.Date(string='Planned Start Date', required=True)
    estimated_duration_months = fields.Integer(string='Estimated Duration (Months)', default=1, required=True)

    workload_percentage = fields.Float(
        string='Workload (%)',
        required=True,
        default=25.0,
    )

    notes = fields.Text(string='Notes')