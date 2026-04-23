from odoo import api, fields, models

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
        compute='_compute_assigned_employee_ids',
        store=True,
    )

    assignment_line_ids = fields.One2many(
        'project.team.assignment.line',
        'assignment_id',
        string='Assigned Resources',
    )

    planned_start_date = fields.Date(string='Planned Start Date', required=True)
    estimated_duration_months = fields.Integer(
        string='Estimated Duration (Months)',
        default=1,
        required=True
    )

    workload_percentage = fields.Float(
        string='Total Workload (%)',
        compute='_compute_workload_percentage',
        store=True,
    )

    notes = fields.Text(string='Notes')


    @api.depends('assignment_line_ids.workload_percentage')
    def _compute_workload_percentage(self):
        for rec in self:
            rec.workload_percentage = sum(rec.assignment_line_ids.mapped('workload_percentage'))

    @api.depends('assignment_line_ids.employee_id')
    def _compute_assigned_employee_ids(self):
        for rec in self:
            rec.assigned_employee_ids = [(6, 0, rec.assignment_line_ids.mapped('employee_id').ids)]