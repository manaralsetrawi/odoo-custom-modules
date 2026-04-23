from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class CrmProjectRequestLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================
    # Project Review Fields
    # =========================================================
    review_project_type_id = fields.Many2one(
        'crm.project.type',
        string='Project Type',
        tracking=True,
    )

    review_project_feature_ids = fields.Many2many(
        'crm.project.feature',
        'crm_lead_project_feature_rel',
        'lead_id',
        'feature_id',
        string='Development and Features',
        tracking=True,
    )

    review_project_features = fields.Text(
        string='Project Features',
        tracking=True,
    )

    review_complexity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Project Complexity', tracking=True)

    review_priority_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Priority Level', tracking=True)

    review_client_segment_id = fields.Many2one(
        'crm.client.segment',
        string='Client Segment',
        tracking=True,
    )

    review_estimated_team = fields.Char(
        string='Suggested Team / Resources',
        tracking=True,
    )

    review_risk_notes = fields.Text(
        string='Risk Notes',
        tracking=True,
    )

    review_recommendation = fields.Text(
        string='Manager Recommendation',
        tracking=True,
    )

    # =========================================================
    # Request Type
    # =========================================================
    request_type = fields.Selection([
        ('general_inquiry', 'General Inquiry'),
        ('project_request', 'Project Request'),
    ], string='Request Type', default='project_request', tracking=True)

    # =========================================================
    # Client Submission Fields
    # =========================================================
    intake_client_name = fields.Char(string='Client Name', tracking=True)
    intake_client_email = fields.Char(string='Client Email', tracking=True)
    intake_client_phone = fields.Char(string='Client Phone', tracking=True)
    intake_company_name = fields.Char(string='Company Name', tracking=True)

    intake_project_title = fields.Char(
        string='Requested Project Title',
        tracking=True,
    )
    intake_project_description = fields.Text(
        string='Requested Project Description',
        tracking=True,
    )
    intake_requested_budget = fields.Float(
        string='Requested Budget',
        tracking=True,
    )
    intake_requested_duration = fields.Char(
        string='Requested Duration',
        tracking=True,
    )
    intake_requested_notes = fields.Text(
        string='Additional Notes',
        tracking=True,
    )

    # =========================================================
    # Internal Workflow Fields
    # =========================================================
    intake_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Intake Status', default='draft', tracking=True)

    intake_reviewed_by = fields.Many2one(
        'res.users',
        string='Reviewed By',
        tracking=True,
    )
    intake_review_date = fields.Datetime(
        string='Review Date',
        tracking=True,
    )
    intake_rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True,
    )

    intake_opportunity_id = fields.Many2one(
        'crm.lead',
        string='Created Opportunity',
        readonly=True,
        copy=False,
        tracking=True,
    )

    # =========================================================
    # Project Manager Fields
    # =========================================================
    intake_meeting_notes = fields.Text(
        string='Meeting Notes',
        tracking=True,
    )
    intake_project_requirements = fields.Text(
        string='Project Requirements',
        tracking=True,
    )

    intake_technical_feasibility = fields.Selection([
        ('pending', 'Pending'),
        ('feasible', 'Feasible'),
        ('not_feasible', 'Not Feasible'),
    ], string='Technical Feasibility', default='pending', tracking=True)

    intake_complexity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Complexity Level', tracking=True)

    intake_estimated_budget_final = fields.Float(
        string='Final Estimated Budget',
        tracking=True,
    )
    intake_estimated_duration_final = fields.Char(
        string='Final Estimated Duration',
        tracking=True,
    )
    intake_project_deadline = fields.Date(
        string='Project Deadline',
        tracking=True,
    )
    intake_solution_summary = fields.Text(
        string='Solution Summary',
        tracking=True,
    )

    # =========================================================
    # Helper Fields
    # =========================================================
    intake_is_project_request = fields.Boolean(
        string='Is Project Request',
        compute='_compute_intake_is_project_request',
        store=False,
    )

    intake_can_approve = fields.Boolean(
        string='Can Approve',
        compute='_compute_intake_button_flags',
        store=False,
    )

    intake_can_reject = fields.Boolean(
        string='Can Reject',
        compute='_compute_intake_button_flags',
        store=False,
    )


    assigned_team_id = fields.Many2one(
    'project.assignment.team',
    string='Assigned Team',
    tracking=True,
    )

    assigned_employee_ids = fields.Many2many(
        'hr.employee',
        'crm_lead_assigned_employee_rel',
        'lead_id',
        'employee_id',
        string='Assigned Employees',
        tracking=True,
        domain="[('department_id.name', '=', 'AI Research and Development')]",
    )

    planned_start_date = fields.Date(
        string='Planned Project Start Date',
        tracking=True,
    )


    # =========================================================
    # Compute Methods
    # =========================================================
    @api.depends('request_type')
    def _compute_intake_is_project_request(self):
        for record in self:
            record.intake_is_project_request = record.request_type == 'project_request'

    @api.depends('request_type', 'type', 'intake_state')
    def _compute_intake_button_flags(self):
        for record in self:
            is_reviewable = (
                record.request_type == 'project_request'
                and record.type == 'lead'
                and record.intake_state == 'under_review'
            )
            record.intake_can_approve = is_reviewable
            record.intake_can_reject = is_reviewable

    # =========================================================
    # Helper Methods
    # =========================================================
    def _get_stage_by_xmlid(self, xmlid):
        stage = self.env.ref(xmlid, raise_if_not_found=False)
        if not stage:
            raise UserError(_("The required CRM stage was not found: %s") % xmlid)
        return stage

    # =========================================================
    # Create / Write Overrides
    # =========================================================
    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    # =========================================================
    # Workflow Actions
    # =========================================================
    def action_intake_start_review(self):
        for record in self:
            if record.request_type != 'project_request' or record.type != 'lead':
                raise ValidationError(_("Only project request leads can start review."))

            if record.intake_state != 'submitted':
                raise ValidationError(_("Only submitted requests can be moved to under review."))

            record.write({
                'intake_state': 'under_review',
                'intake_reviewed_by': self.env.user.id,
                'intake_review_date': fields.Datetime.now(),
            })

            record.message_post(
                body=_("Project request moved to Under Review.")
            )

    def action_intake_open_reject_wizard(self):
        self.ensure_one()

        if self.request_type != 'project_request' or self.type != 'lead':
            raise ValidationError(_("Only project request leads can be rejected."))

        if self.intake_state != 'under_review':
            raise ValidationError(_("Only requests under review can be rejected."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Project Request'),
            'res_model': 'project.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            },
        }

    def action_intake_approve_request(self):
        initial_discussion_stage = self._get_stage_by_xmlid(
            'crm_workflow_custom.stage_initial_discussion'
        )

        Partner = self.env['res.partner']

        for record in self:
            if record.request_type != 'project_request' or record.type != 'lead':
                raise ValidationError(_("Only project request leads can be approved."))

            if record.intake_state != 'under_review':
                raise ValidationError(_("Only requests under review can be approved."))

            missing_fields = []

            if not record.review_project_type_id:
                missing_fields.append(_("Project Type"))

            if not record.review_complexity:
                missing_fields.append(_("Project Complexity"))

            if not record.review_client_segment_id:
                missing_fields.append(_("Client Segment"))

            if record.intake_technical_feasibility == 'pending':
                missing_fields.append(_("Technical Feasibility"))

            if not record.intake_estimated_budget_final:
                missing_fields.append(_("Final Estimated Budget"))

            if not record.intake_estimated_duration_final:
                missing_fields.append(_("Final Estimated Duration"))

            if not record.intake_project_deadline:
                missing_fields.append(_("Project Deadline"))

            if not record.intake_project_requirements:
                missing_fields.append(_("Project Requirements"))

            if not record.intake_solution_summary:
                missing_fields.append(_("Solution Summary"))

            if not record.review_recommendation:
                missing_fields.append(_("Manager Recommendation"))

            if not record.review_project_feature_ids:
                missing_fields.append(_("Development and Features"))

            if missing_fields:
                raise ValidationError(_(
                    "You cannot approve this request until the Project Review Details are completed.\n\n"
                    "Please fill in:\n- %s"
                ) % "\n- ".join(missing_fields))

            # =========================================================
            # Find or Create Contact in Contacts module
            # =========================================================
            partner = False

            if record.intake_client_email:
                partner = Partner.search([
                    ('email', '=', record.intake_client_email)
                ], limit=1)

            if not partner and record.intake_company_name:
                partner = Partner.search([
                    ('name', '=', record.intake_company_name),
                    ('is_company', '=', True)
                ], limit=1)

            if not partner:
                partner_vals = {
                    'name': record.intake_company_name or record.intake_client_name or record.contact_name or _("New Contact"),
                    'email': record.intake_client_email or record.email_from,
                    'phone': record.intake_client_phone or record.phone,
                    'is_company': bool(record.intake_company_name),
                    'company_type': 'company' if record.intake_company_name else 'person',
                }
                partner = Partner.create(partner_vals)
                contact_person = partner

            if partner.is_company and record.intake_client_name:
                existing_contact = Partner.search([
                    ('parent_id', '=', partner.id),
                    ('name', '=', record.intake_client_name)
                ], limit=1)

                if existing_contact:
                    contact_person = existing_contact
                else:
                    contact_person = Partner.create({
                        'name': record.intake_client_name,
                        'parent_id': partner.id,
                        'type': 'contact',
                        'email': record.intake_client_email or record.email_from,
                        'phone': record.intake_client_phone or record.phone,
                        'company_type': 'person',
                    })


            # =========================================================
            # Create Opportunity linked to Contact
            # =========================================================
            opportunity_vals = {
                'name': record.intake_project_title or record.name,
                'type': 'opportunity',
                'partner_id': contact_person.id,
                'partner_name': record.intake_company_name or partner.name,
                'contact_name': record.intake_client_name or record.contact_name,
                'email_from': record.intake_client_email or record.email_from,
                'phone': record.intake_client_phone or record.phone,
                'description': record.intake_project_description or record.description,
                'user_id': record.user_id.id,
                'team_id': record.team_id.id,
                'stage_id': initial_discussion_stage.id,
                'review_project_type_id': record.review_project_type_id.id,
                'review_client_segment_id': record.review_client_segment_id.id,
                'review_complexity': record.review_complexity,
                'review_project_feature_ids': [(6, 0, record.review_project_feature_ids.ids)],
                'planned_start_date': record.planned_start_date,
            }

            opportunity = self.env['crm.lead'].create(opportunity_vals)

            record.write({
                'intake_state': 'approved',
                'intake_opportunity_id': opportunity.id,
            })

            record.message_post(
                body=_("Project request approved, contact created/linked, and opportunity created in Initial Discussion stage.")
            )

            return {
                'type': 'ir.actions.act_window',
                'name': _('Assign Project Team'),
                'res_model': 'project.team.assignment.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_lead_id': opportunity.id,
                },
            }


    # =========================================================
    # Optional Helper When Website Creates Request
    # =========================================================
    @api.model
    def create_project_request_lead(self, vals):
        vals.update({
            'request_type': 'project_request',
            'type': 'lead',
            'intake_state': 'submitted',
        })
        return self.create(vals)