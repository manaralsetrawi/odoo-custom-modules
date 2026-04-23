from datetime import date
from calendar import monthrange

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTeamAssignmentWizard(models.TransientModel):
    _name = 'project.team.assignment.wizard'
    _description = 'Project Team Assignment Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', required=True)
    project_type_id = fields.Many2one('crm.project.type', string='Project Type', readonly=True)
    planned_start_date = fields.Date(string='Planned Start Date', required=True)

    estimated_duration_months = fields.Integer(
        string='Estimated Duration (Months)',
        default=1,
        required=True,
    )

    required_workload_percentage = fields.Float(
        string='Required Workload (%)',
        default=25.0,
        required=True,
    )

    suggested_team_id = fields.Many2one(
        'project.assignment.team',
        string='Suggested Team',
        readonly=True,
    )

    selected_team_id = fields.Many2one(
        'project.assignment.team',
        string='Selected Team',
        required=True,
    )

    assigned_employee_ids = fields.Many2many(
        'hr.employee',
        'project_team_assignment_wizard_employee_rel',
        'wizard_id',
        'employee_id',
        string='Assigned Employees',
        domain="[('department_id.name', '=', 'AI Research and Development')]",
    )

    assignment_notes = fields.Text(string='Assignment Notes')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        lead_id = self.env.context.get('default_lead_id')
        if not lead_id:
            return res

        lead = self.env['crm.lead'].browse(lead_id)
        suggested_team = self._get_suggested_team(
            lead.review_project_type_id,
            lead.planned_start_date or fields.Date.today(),
            25.0,
        )

        res.update({
            'project_type_id': lead.review_project_type_id.id,
            'planned_start_date': lead.planned_start_date or fields.Date.today(),
            'suggested_team_id': suggested_team.id if suggested_team else False,
            'selected_team_id': suggested_team.id if suggested_team else False,
            'assigned_employee_ids': [(6, 0, suggested_team.member_ids.ids)] if suggested_team else False,
        })
        return res

    def _get_month_date_range(self, dt):
        first_day = dt.replace(day=1)
        last_day = dt.replace(day=monthrange(dt.year, dt.month)[1])
        return first_day, last_day

    def _get_suggested_team(self, project_type, planned_start_date, required_workload=25.0):
        if not project_type or not planned_start_date:
            return False

        month_start, month_end = self._get_month_date_range(planned_start_date)

        matching_teams = self.env['project.assignment.team'].search([
            ('project_type_ids', 'in', project_type.id),
            ('active', '=', True),
        ])

        if not matching_teams:
            return False

        best_team = False
        best_remaining = -1

        for team in matching_teams:
            same_month_assignments = self.env['project.team.assignment'].search([
                ('team_id', '=', team.id),
                ('planned_start_date', '>=', month_start),
                ('planned_start_date', '<=', month_end),
            ])

            used_capacity = sum(same_month_assignments.mapped('workload_percentage'))
            remaining_capacity = team.monthly_capacity - used_capacity

            if remaining_capacity >= required_workload and remaining_capacity > best_remaining:
                best_team = team
                best_remaining = remaining_capacity

        return best_team

    @api.onchange('selected_team_id')
    def _onchange_selected_team_id(self):
        if self.selected_team_id:
            self.assigned_employee_ids = [(6, 0, self.selected_team_id.member_ids.ids)]

    def action_confirm_assignment(self):
        self.ensure_one()

        if not self.selected_team_id:
            raise ValidationError(_("Please select a team."))

        if not self.planned_start_date:
            raise ValidationError(_("Please enter the planned start date."))

        month_start, month_end = self._get_month_date_range(self.planned_start_date)

        existing_assignments = self.env['project.team.assignment'].search([
            ('team_id', '=', self.selected_team_id.id),
            ('planned_start_date', '>=', month_start),
            ('planned_start_date', '<=', month_end),
        ])

        used_capacity = sum(existing_assignments.mapped('workload_percentage'))
        remaining_capacity = self.selected_team_id.monthly_capacity - used_capacity

        if remaining_capacity < self.required_workload_percentage:
            raise ValidationError(_("The selected team does not have enough remaining capacity for this month."))

        self.lead_id.write({
            'assigned_team_id': self.selected_team_id.id,
            'assigned_employee_ids': [(6, 0, self.assigned_employee_ids.ids)],
            'planned_start_date': self.planned_start_date,
        })

        self.env['project.team.assignment'].create({
            'lead_id': self.lead_id.id,
            'team_id': self.selected_team_id.id,
            'assigned_employee_ids': [(6, 0, self.assigned_employee_ids.ids)],
            'planned_start_date': self.planned_start_date,
            'estimated_duration_months': self.estimated_duration_months,
            'workload_percentage': self.required_workload_percentage,
            'notes': self.assignment_notes,
        })

        self.lead_id.message_post(
            body=_("Project team assigned: %s") % self.selected_team_id.name
        )

        return {'type': 'ir.actions.act_window_close'}