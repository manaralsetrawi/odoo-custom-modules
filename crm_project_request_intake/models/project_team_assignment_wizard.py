from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTeamAssignmentWizard(models.TransientModel):
    _name = 'project.team.assignment.wizard'
    _description = 'Project Team Assignment Wizard'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead / Opportunity',
        required=True,
    )

    project_type_id = fields.Many2one(
        'crm.project.type',
        string='Project Type',
        readonly=True,
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

    employee_ids = fields.Many2many(
        'hr.employee',
        'project_team_assignment_wizard_employee_rel',
        'wizard_id',
        'employee_id',
        string='Assigned Employees',
        required=True,
        domain="[('department_id.name', '=', 'AI Research and Development')]",
    )

    planned_start_date = fields.Date(
        string='Project Start Date',
        required=True,
    )

    planned_end_date = fields.Date(
        string='Project End Date',
        required=True,
    )

    assignment_notes = fields.Text(
        string='Assignment Notes',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        lead_id = self.env.context.get('default_lead_id')
        if not lead_id:
            return res

        lead = self.env['crm.lead'].browse(lead_id)

        project_type = lead.review_project_type_id
        suggested_team = self.env['project.assignment.team'].search([
            ('project_type_ids', 'in', project_type.id),
            ('active', '=', True),
        ], limit=1)

        start_date = lead.planned_start_date or fields.Date.today()
        end_date = lead.planned_end_date or start_date

        res.update({
            'lead_id': lead.id,
            'project_type_id': project_type.id if project_type else False,
            'suggested_team_id': suggested_team.id if suggested_team else False,
            'selected_team_id': suggested_team.id if suggested_team else False,
            'employee_ids': [(6, 0, suggested_team.employee_ids.ids)] if suggested_team else False,
            'planned_start_date': start_date,
            'planned_end_date': end_date,
        })

        return res

    @api.onchange('selected_team_id')
    def _onchange_selected_team_id(self):
        if self.selected_team_id:
            self.employee_ids = [(6, 0, self.selected_team_id.employee_ids.ids)]
        else:
            self.employee_ids = [(5, 0, 0)]

    def action_confirm_assignment(self):
        self.ensure_one()

        if not self.selected_team_id:
            raise ValidationError(_("Please select a team."))

        if not self.employee_ids:
            raise ValidationError(_("Please select at least one employee."))

        if not self.planned_start_date:
            raise ValidationError(_("Please enter the project start date."))

        if not self.planned_end_date:
            raise ValidationError(_("Please enter the project end date."))

        if self.planned_end_date < self.planned_start_date:
            raise ValidationError(_("Project end date cannot be before the project start date."))

        lead = self.lead_id
        opportunity = lead

        if lead.type == 'lead' and lead.request_type == 'project_request':
            initial_discussion_stage = self.env.ref(
                'crm_workflow_custom.stage_initial_discussion',
                raise_if_not_found=False
            )

            if not initial_discussion_stage:
                raise ValidationError(_("Initial Discussion stage was not found."))

            Partner = self.env['res.partner']
            partner = False

            if lead.intake_client_email:
                partner = Partner.search([
                    ('email', '=', lead.intake_client_email)
                ], limit=1)

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

                'partner_id': partner.id,
                'partner_name': False,
                'contact_name': lead.intake_client_name or lead.contact_name,
                'email_from': lead.intake_client_email or lead.email_from,
                'phone': lead.intake_client_phone or lead.phone,
                'description': lead.intake_project_description or lead.description,
                'user_id': lead.user_id.id,
                'team_id': lead.team_id.id,
                'stage_id': initial_discussion_stage.id,

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

                'review_project_type_id': lead.review_project_type_id.id,
                'review_client_segment_id': lead.review_client_segment_id.id,
                'review_project_feature_ids': [(6, 0, lead.review_project_feature_ids.ids)],
                'review_project_features': lead.review_project_features,
                'review_risk_notes': lead.review_risk_notes,
                'review_recommendation': lead.review_recommendation,

                'intake_meeting_notes': lead.intake_meeting_notes,
                'intake_project_requirements': lead.intake_project_requirements,
                'intake_solution_summary': lead.intake_solution_summary,

                'planned_start_date': self.planned_start_date,
                'planned_end_date': self.planned_end_date,
                'assigned_team_id': self.selected_team_id.id,
                'assigned_employee_ids': [(6, 0, self.employee_ids.ids)],
            }

            opportunity = self.env['crm.lead'].create(opportunity_vals)

            lead.write({
                'intake_state': 'approved',
                'intake_opportunity_id': opportunity.id,
                'active': False,
            })

            lead._send_project_request_approval_email()

            self.env['crm.email.log'].create({
                'lead_id': opportunity.id,
                'subject': 'Project Request Approved - %s' % (opportunity.name or lead.name or ''),
                'sender_email': self.env.user.email or '',
                'recipient_email': lead.email_from or lead.intake_client_email or '',
                'email_type': 'approval',
                'direction': 'outgoing',
                'body_preview': (
                    "Your project request has been approved and converted into an opportunity.\n\n"
                    "Project: %s\n"
                    "Assigned Team: %s\n"
                    "Project Start Date: %s\n"
                    "Project End Date: %s"
                ) % (
                    opportunity.name or '',
                    self.selected_team_id.name or '',
                    self.planned_start_date or '',
                    self.planned_end_date or '',
                ),
                'notes': 'Automatic approval email sent after the project request was approved.',
            })

            lead.message_post(
                body=_("Project request approved and converted into an opportunity: %s") % opportunity.name
            )

        else:
            opportunity.write({
                'assigned_team_id': self.selected_team_id.id,
                'assigned_employee_ids': [(6, 0, self.employee_ids.ids)],
                'planned_start_date': self.planned_start_date,
                'planned_end_date': self.planned_end_date,
            })

        assignment = self.env['project.team.assignment'].create({
            'lead_id': opportunity.id,
            'team_id': self.selected_team_id.id,
            'employee_ids': [(6, 0, self.employee_ids.ids)],
            'planned_start_date': self.planned_start_date,
            'planned_end_date': self.planned_end_date,
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