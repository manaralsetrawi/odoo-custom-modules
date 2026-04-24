from calendar import monthrange
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProjectTeamAssignmentWizard(models.TransientModel):
    _name = 'project.team.assignment.wizard'
    _description = 'Project Team Assignment Wizard'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead/Opportunity',
        required=True
    )

    project_type_id = fields.Many2one(
        'crm.project.type',
        string='Project Type',
        readonly=True
    )

    planned_start_date = fields.Date(
        string='Planned Start Date',
        required=True
    )

    planned_end_date = fields.Date(
        string='Planned End Date',
        required=True
    )

    estimated_duration_months = fields.Integer(
        string='Estimated Duration (Months)',
        default=1,
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

    assignment_line_ids = fields.One2many(
        'project.team.assignment.wizard.line',
        'wizard_id',
        string='Assigned Resources',
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
            0.0,
        )

        start_date = lead.planned_start_date or fields.Date.today()
        end_date = lead.planned_start_date or fields.Date.today()

        res.update({
            'project_type_id': lead.review_project_type_id.id,
            'planned_start_date': start_date,
            'planned_end_date': end_date,
            'suggested_team_id': suggested_team.id if suggested_team else False,
            'selected_team_id': suggested_team.id if suggested_team else False,
            'assignment_line_ids': [
                (0, 0, {
                    'employee_id': emp.id,
                    'workload_percentage': 0.0,
                })
                for emp in suggested_team.member_ids
            ] if suggested_team else [],
        })
        return res

    def _get_month_date_range(self, dt):
        first_day = dt.replace(day=1)
        last_day = dt.replace(day=monthrange(dt.year, dt.month)[1])
        return first_day, last_day

    def _get_month_keys_between(self, start_date, end_date):
        months = []
        current_year = start_date.year
        current_month = start_date.month

        while (current_year, current_month) <= (end_date.year, end_date.month):
            months.append((current_year, current_month))
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        return months

    def _get_month_count(self, start_date, end_date):
        return len(self._get_month_keys_between(start_date, end_date))

    def _get_employee_month_usage(self, employee, year, month):
        month_start = fields.Date.from_string(f"{year}-{month:02d}-01")
        month_end = month_start.replace(day=monthrange(year, month)[1])

        lines = self.env['project.team.assignment.line'].search([
            ('employee_id', '=', employee.id),
            ('assignment_id.planned_start_date', '<=', month_end),
            ('assignment_id.planned_end_date', '>=', month_start),
        ])

        total = 0.0
        for line in lines:
            total += line.monthly_reserved_percentage
        return total

    def _get_suggested_team(self, project_type, planned_start_date, required_workload=0.0):
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
                ('planned_start_date', '<=', month_end),
                ('planned_end_date', '>=', month_start),
            ])

            used_capacity = sum(same_month_assignments.mapped('workload_percentage'))
            remaining_capacity = team.monthly_capacity - used_capacity

            if remaining_capacity >= required_workload and remaining_capacity > best_remaining:
                best_team = team
                best_remaining = remaining_capacity

        return best_team

    @api.onchange('selected_team_id')
    def _onchange_selected_team_id(self):
        self.assignment_line_ids = [(5, 0, 0)]

        if self.selected_team_id:
            self.assignment_line_ids = [
                (0, 0, {
                    'employee_id': emp.id,
                    'workload_percentage': 0.0,
                })
                for emp in self.selected_team_id.member_ids
            ]

    def action_confirm_assignment(self):
        self.ensure_one()

        if not self.selected_team_id:
            raise ValidationError(_("Please select a team."))

        if not self.planned_start_date:
            raise ValidationError(_("Please enter the planned start date."))

        if not self.planned_end_date:
            raise ValidationError(_("Please enter the planned end date."))

        if self.planned_end_date < self.planned_start_date:
            raise ValidationError(_("Planned end date cannot be before planned start date."))

        if not self.assignment_line_ids:
            raise ValidationError(_("Please add at least one assigned resource."))

        employee_ids = []
        month_keys = self._get_month_keys_between(self.planned_start_date, self.planned_end_date)
        month_count = len(month_keys)

        if month_count <= 0:
            raise ValidationError(_("Invalid project duration."))

        total_workload = 0.0

        for line in self.assignment_line_ids:
            if not line.employee_id:
                raise ValidationError(_("Each resource line must have an employee."))

            if line.employee_id.id in employee_ids:
                raise ValidationError(_("The same employee cannot be added more than once."))

            employee_ids.append(line.employee_id.id)

            if line.workload_percentage <= 0:
                raise ValidationError(_("Each assigned employee must have a workload percentage greater than 0."))

            monthly_reserved = line.workload_percentage / month_count

            for year, month in month_keys:
                used = self._get_employee_month_usage(line.employee_id, year, month)
                remaining = line.employee_id.monthly_capacity - used

                if remaining < monthly_reserved:
                    raise ValidationError(_(
                        "Employee %s does not have enough remaining capacity for %s/%s."
                    ) % (line.employee_id.name, month, year))

            total_workload += line.workload_percentage

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
                'assigned_team_id': self.selected_team_id.id,
                'assigned_employee_ids': [(6, 0, self.assignment_line_ids.mapped('employee_id').ids)],
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
                    "Planned Start Date: %s\n"
                    "Planned End Date: %s"
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
                'assigned_employee_ids': [(6, 0, self.assignment_line_ids.mapped('employee_id').ids)],
                'planned_start_date': self.planned_start_date,
            })

        assignment = self.env['project.team.assignment'].create({
            'lead_id': opportunity.id,
            'team_id': self.selected_team_id.id,
            'planned_start_date': self.planned_start_date,
            'planned_end_date': self.planned_end_date,
            'estimated_duration_months': month_count,
            'notes': self.assignment_notes,
        })

        for line in self.assignment_line_ids:
            self.env['project.team.assignment.line'].create({
                'assignment_id': assignment.id,
                'employee_id': line.employee_id.id,
                'workload_percentage': line.workload_percentage,
                'notes': line.notes,
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