from datetime import date
from calendar import monthrange

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTeamAssignmentWizard(models.TransientModel):
    _name = 'project.team.assignment.wizard'
    _description = 'Project Team Assignment Wizard'

    lead_id = fields.Many2one(
        'crm.lead', string='Lead/Opportunity', required=True)
    project_type_id = fields.Many2one(
        'crm.project.type', string='Project Type', readonly=True)
    planned_start_date = fields.Date(
        string='Planned Start Date', required=True)

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

            used_capacity = sum(
                same_month_assignments.mapped('workload_percentage'))
            remaining_capacity = team.monthly_capacity - used_capacity

            if remaining_capacity >= required_workload and remaining_capacity > best_remaining:
                best_team = team
                best_remaining = remaining_capacity

        return best_team

    @api.onchange('selected_team_id')
    def _onchange_selected_team_id(self):
        if self.selected_team_id:
            self.assigned_employee_ids = [
                (6, 0, self.selected_team_id.member_ids.ids)]

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
            raise ValidationError(
                _("The selected team does not have enough remaining capacity for this month.")
            )

        lead = self.lead_id
        opportunity = lead

        # If this is still a project request lead, create the opportunity now
        if lead.type == 'lead' and lead.request_type == 'project_request':
            initial_discussion_stage = self.env.ref(
                'crm_workflow_custom.stage_initial_discussion',
                raise_if_not_found=False
            )
            if not initial_discussion_stage:
                raise ValidationError(_("Initial Discussion stage was not found."))

            Partner = self.env['res.partner']
            partner = False

            # Try to find existing individual contact by email
            if lead.intake_client_email:
                partner = Partner.search([
                    ('email', '=', lead.intake_client_email)
                ], limit=1)

            # If not found, create only one person contact
            if not partner:
                partner = Partner.create({
                    'name': lead.intake_client_name or lead.contact_name or _("New Contact"),
                    'email': lead.intake_client_email or lead.email_from,
                    'phone': lead.intake_client_phone or lead.phone,
                    'company_type': 'person',
                })

            opportunity_vals = {
                'name': lead.intake_project_title or lead.name,
                'type': 'opportunity',
                'request_type': lead.request_type,
                'intake_state': 'approved',

                # Standard CRM / contact fields
                'partner_id': partner.id,
                'partner_name': False,
                'contact_name': lead.intake_client_name or lead.contact_name,
                'email_from': lead.intake_client_email or lead.email_from,
                'phone': lead.intake_client_phone or lead.phone,
                'description': lead.intake_project_description or lead.description,
                'user_id': lead.user_id.id,
                'team_id': lead.team_id.id,
                'stage_id': initial_discussion_stage.id,

                # Intake fields
                'intake_client_name': lead.intake_client_name,
                'intake_client_email': lead.intake_client_email,
                'intake_client_phone': lead.intake_client_phone,
                'intake_company_name': lead.intake_company_name,
                'intake_project_title': lead.intake_project_title,
                'intake_project_description': lead.intake_project_description,
                'intake_requested_budget': lead.intake_requested_budget,
                'intake_requested_duration': lead.intake_requested_duration,
                'intake_requested_notes': lead.intake_requested_notes,
                'intake_reviewed_by': lead.intake_reviewed_by.id,
                'intake_review_date': lead.intake_review_date,

                # Review fields
                'review_project_type_id': lead.review_project_type_id.id,
                'review_client_segment_id': lead.review_client_segment_id.id,
                'review_complexity': lead.review_complexity,
                'review_priority_level': lead.review_priority_level,
                'review_project_feature_ids': [(6, 0, lead.review_project_feature_ids.ids)],
                'review_project_features': lead.review_project_features,
                'review_estimated_team': lead.review_estimated_team,
                'review_risk_notes': lead.review_risk_notes,
                'review_recommendation': lead.review_recommendation,

                # Project manager fields
                'intake_meeting_notes': lead.intake_meeting_notes,
                'intake_project_requirements': lead.intake_project_requirements,
                'intake_technical_feasibility': lead.intake_technical_feasibility,
                'intake_complexity_level': lead.intake_complexity_level,
                'intake_estimated_budget_final': lead.intake_estimated_budget_final,
                'intake_estimated_duration_final': lead.intake_estimated_duration_final,
                'intake_project_deadline': lead.intake_project_deadline,
                'intake_solution_summary': lead.intake_solution_summary,

                # Planning / assignment
                'planned_start_date': self.planned_start_date,
                'assigned_team_id': self.selected_team_id.id,
                'assigned_employee_ids': [(6, 0, self.assigned_employee_ids.ids)],
            }

            opportunity = self.env['crm.lead'].create(opportunity_vals)

            lead.write({
                'intake_state': 'approved',
                'intake_opportunity_id': opportunity.id,
                'active': False,
            })

            lead.message_post(
                body=_("Project request approved and converted into an opportunity: %s") % opportunity.name
            )

        else:
            # Already an opportunity: just update assignment info
            opportunity.write({
                'assigned_team_id': self.selected_team_id.id,
                'assigned_employee_ids': [(6, 0, self.assigned_employee_ids.ids)],
                'planned_start_date': self.planned_start_date,
            })

        self.env['project.team.assignment'].create({
            'lead_id': opportunity.id,
            'team_id': self.selected_team_id.id,
            'assigned_employee_ids': [(6, 0, self.assigned_employee_ids.ids)],
            'planned_start_date': self.planned_start_date,
            'estimated_duration_months': self.estimated_duration_months,
            'workload_percentage': self.required_workload_percentage,
            'notes': self.assignment_notes,
        })

        opportunity.message_post(
            body=_("Project team assigned: %s") % self.selected_team_id.name
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': opportunity.id,
            'view_mode': 'form',
            'target': 'current',
        }