from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTeamAssignmentWizard(models.TransientModel):
    _name = 'project.team.assignment.wizard'
    _description = 'Project Team Assignment Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead/Opportunity', required=True)
    project_type_id = fields.Many2one('crm.project.type', string='Project Type', readonly=True)
    planned_start_date = fields.Date(string='Planned Start Date', required=True)

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
            lead.planned_start_date or fields.Date.today()
        )

        res.update({
            'project_type_id': lead.review_project_type_id.id,
            'planned_start_date': lead.planned_start_date or fields.Date.today(),
            'suggested_team_id': suggested_team.id if suggested_team else False,
            'selected_team_id': suggested_team.id if suggested_team else False,
            'assigned_employee_ids': [(6, 0, suggested_team.member_ids.ids)] if suggested_team else False,
        })
        return res

    def _get_suggested_team(self, project_type, planned_start_date):
        if not project_type or not planned_start_date:
            return False

        month_value = str(planned_start_date.month)
        year_value = planned_start_date.year

        matching_teams = self.env['project.assignment.team'].search([
            ('project_type_ids', 'in', project_type.id),
            ('active', '=', True),
        ])

        if not matching_teams:
            return False

        available_teams = self.env['project.team.availability'].search([
            ('team_id', 'in', matching_teams.ids),
            ('month', '=', month_value),
            ('year', '=', year_value),
            ('availability_status', 'in', ['available', 'partial']),
        ], limit=1)

        if available_teams:
            return available_teams.team_id

        return False

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

        month_value = str(self.planned_start_date.month)
        year_value = self.planned_start_date.year

        availability = self.env['project.team.availability'].search([
            ('team_id', '=', self.selected_team_id.id),
            ('month', '=', month_value),
            ('year', '=', year_value),
        ], limit=1)

        if availability and availability.availability_status == 'unavailable':
            raise ValidationError(_("The selected team is unavailable for the planned start month."))

        self.lead_id.write({
            'assigned_team_id': self.selected_team_id.id,
            'assigned_employee_ids': [(6, 0, self.assigned_employee_ids.ids)],
            'planned_start_date': self.planned_start_date,
        })

        self.lead_id.message_post(
            body=_("Project team assigned: %s") % self.selected_team_id.name
        )

        return {'type': 'ir.actions.act_window_close'}