from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class CrmProjectRequestLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================
    # Request Type
    # =========================================================
    request_type = fields.Selection([
        ('general_inquiry', 'General Inquiry'),
        ('project_request', 'Project Request'),
    ], string='Request Type', default='general_inquiry', tracking=True)

    # =========================================================
    # Client Submission Fields
    # =========================================================
    intake_client_name = fields.Char(string='Client Name', tracking=True)
    intake_client_email = fields.Char(string='Client Email', tracking=True)
    intake_client_phone = fields.Char(string='Client Phone', tracking=True)
    intake_company_name = fields.Char(string='Company Name', tracking=True)

    intake_project_title = fields.Char(string='Requested Project Title', tracking=True)
    intake_project_description = fields.Text(string='Requested Project Description', tracking=True)
    intake_requested_budget = fields.Float(string='Requested Budget', tracking=True)
    intake_requested_duration = fields.Char(string='Requested Duration', tracking=True)
    intake_requested_notes = fields.Text(string='Additional Notes', tracking=True)

    # =========================================================
    # Internal Workflow Fields
    # =========================================================
    intake_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted to Opportunity'),
    ], string='Intake Status', default='draft', tracking=True)

    intake_reviewed_by = fields.Many2one('res.users', string='Reviewed By', tracking=True)
    intake_review_date = fields.Datetime(string='Review Date', tracking=True)
    intake_rejection_reason = fields.Text(string='Rejection Reason', tracking=True)

    # =========================================================
    # Project Manager Fields
    # =========================================================
    intake_meeting_notes = fields.Text(string='Meeting Notes', tracking=True)
    intake_project_requirements = fields.Text(string='Project Requirements', tracking=True)

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

    intake_estimated_budget_final = fields.Float(string='Final Estimated Budget', tracking=True)
    intake_estimated_duration_final = fields.Char(string='Final Estimated Duration', tracking=True)
    intake_project_deadline = fields.Date(string='Project Deadline', tracking=True)
    intake_solution_summary = fields.Text(string='Solution Summary', tracking=True)

    # =========================================================
    # Helper Fields
    # =========================================================
    intake_is_project_request = fields.Boolean(
        string='Is Project Request',
        compute='_compute_intake_is_project_request',
        store=False
    )

    intake_can_create_opportunity = fields.Boolean(
        string='Can Create Opportunity',
        compute='_compute_intake_can_create_opportunity',
        store=False
    )

    @api.depends('request_type')
    def _compute_intake_is_project_request(self):
        for record in self:
            record.intake_is_project_request = record.request_type == 'project_request'

    @api.depends('request_type', 'intake_state')
    def _compute_intake_can_create_opportunity(self):
        for record in self:
            record.intake_can_create_opportunity = (
                record.request_type == 'project_request'
                and record.intake_state == 'approved'
            )

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
        new_stage = self.env.ref(
            'crm_project_request_intake.crm_stage_project_request_new',
            raise_if_not_found=False
        )

        for vals in vals_list:
            if vals.get('request_type') == 'project_request':
                if not vals.get('intake_state') or vals.get('intake_state') == 'draft':
                    vals['intake_state'] = 'submitted'
                if new_stage and not vals.get('stage_id'):
                    vals['stage_id'] = new_stage.id
                if vals.get('type') != 'opportunity':
                    vals['type'] = 'lead'

        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)

        new_stage = self.env.ref(
            'crm_project_request_intake.crm_stage_project_request_new',
            raise_if_not_found=False
        )

        if 'request_type' in vals:
            for record in self:
                if record.request_type == 'project_request':
                    if record.intake_state == 'draft':
                        record.intake_state = 'submitted'
                    if new_stage and not record.stage_id:
                        record.stage_id = new_stage.id
                    if record.type != 'opportunity':
                        record.type = 'lead'

        return result

    # =========================================================
    # Workflow Actions
    # =========================================================
    def action_intake_start_review(self):
        stage = self._get_stage_by_xmlid('crm_project_request_intake.crm_stage_project_request_review')
        for record in self:
            if record.request_type != 'project_request':
                raise ValidationError(_("Only project requests can be reviewed through this flow."))

            record.intake_state = 'under_review'
            record.stage_id = stage.id

    def action_intake_approve_request(self):
        stage = self._get_stage_by_xmlid('crm_project_request_intake.crm_stage_project_request_approved')
        for record in self:
            if record.request_type != 'project_request':
                raise ValidationError(_("Only project requests can be approved through this flow."))

            record.intake_state = 'approved'
            record.intake_reviewed_by = self.env.user
            record.intake_review_date = fields.Datetime.now()
            record.stage_id = stage.id

    def action_intake_reject_request(self):
        stage = self._get_stage_by_xmlid('crm_project_request_intake.crm_stage_project_request_rejected')
        for record in self:
            if record.request_type != 'project_request':
                raise ValidationError(_("Only project requests can be rejected through this flow."))

            if not record.intake_rejection_reason:
                raise ValidationError(_("Please enter the rejection reason before rejecting the request."))

            record.intake_state = 'rejected'
            record.intake_reviewed_by = self.env.user
            record.intake_review_date = fields.Datetime.now()
            record.stage_id = stage.id

    def action_intake_create_project_opportunity(self):
        stage = self._get_stage_by_xmlid('crm_project_request_intake.crm_stage_project_request_opportunity')
        for record in self:
            if record.request_type != 'project_request':
                raise ValidationError(_("Only project requests can be converted into opportunities."))

            if record.intake_state != 'approved':
                raise ValidationError(_("Only approved project requests can be converted into opportunities."))

            if not record.intake_project_requirements:
                raise ValidationError(_("Please fill in the project requirements before creating the opportunity."))

            if not record.intake_solution_summary:
                raise ValidationError(_("Please fill in the solution summary before creating the opportunity."))

            record.type = 'opportunity'
            record.intake_state = 'converted'
            record.stage_id = stage.id

    # =========================================================
    # Optional Helper When Website Creates Request
    # =========================================================
    @api.model
    def create_project_request_lead(self, vals):
        stage = self.env.ref(
            'crm_project_request_intake.crm_stage_project_request_new',
            raise_if_not_found=False
        )

        vals.update({
            'request_type': 'project_request',
            'type': 'lead',
            'intake_state': 'submitted',
        })

        if stage:
            vals['stage_id'] = stage.id

        return self.create(vals)