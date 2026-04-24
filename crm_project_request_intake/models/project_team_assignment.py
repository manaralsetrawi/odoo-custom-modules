from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTeamAssignment(models.Model):
    _name = 'project.team.assignment'
    _description = 'Project Team Assignment'
    _order = 'planned_start_date desc'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Project / Opportunity',
        required=True,
        ondelete='cascade',
    )

    team_id = fields.Many2one(
        'project.assignment.team',
        string='Assigned Team',
        required=True,
        ondelete='restrict',
    )

    employee_ids = fields.Many2many(
        'hr.employee',
        'project_team_assignment_employee_rel',
        'assignment_id',
        'employee_id',
        string='Assigned Employees',
        required=True,
    )

    planned_start_date = fields.Date(
        string='Project Start Date',
        required=True,
    )

    planned_end_date = fields.Date(
        string='Project End Date',
        required=True,
    )

    notes = fields.Text(
        string='Notes'
    )

    @api.constrains('planned_start_date', 'planned_end_date')
    def _check_project_dates(self):
        for rec in self:
            if rec.planned_start_date and rec.planned_end_date:
                if rec.planned_end_date < rec.planned_start_date:
                    raise ValidationError(
                        _("Project end date cannot be before the project start date.")
                    )

    @api.constrains('employee_ids', 'planned_start_date', 'planned_end_date')
    def _check_employee_overbooking(self):
        for rec in self:
            if not rec.employee_ids or not rec.planned_start_date or not rec.planned_end_date:
                continue

            overlapping_assignments = self.search([
                ('id', '!=', rec.id),
                ('employee_ids', 'in', rec.employee_ids.ids),
                ('planned_start_date', '<=', rec.planned_end_date),
                ('planned_end_date', '>=', rec.planned_start_date),
            ])

            if overlapping_assignments:
                conflict_messages = []

                for employee in rec.employee_ids:
                    employee_conflicts = overlapping_assignments.filtered(
                        lambda assignment: employee in assignment.employee_ids
                    )

                    for conflict in employee_conflicts:
                        conflict_messages.append(
                            _("%s is already assigned to %s from %s to %s.") % (
                                employee.name,
                                conflict.lead_id.name,
                                conflict.planned_start_date,
                                conflict.planned_end_date,
                            )
                        )

                if conflict_messages:
                    raise ValidationError(
                        _("Employee overbooking detected:\n\n%s") %
                        "\n".join(conflict_messages)
                    )