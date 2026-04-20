from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
    # Workflow Actions
    # =========================================================
    def action_intake_start_review(self):
        for record in self:
            if record.request_type != 'project_request':
                raise ValidationError(_("Only project requests can be reviewed through this flow."))

            record.intake_state = 'under_review'

    def action_intake_approve_request(self):
        for record in self:
            if record.request_type != 'project_request':
                raise ValidationError(_("Only project requests can be approved through this flow."))

            record.intake_state = 'approved'
            record.intake_reviewed_by = self.env.user
            record.intake_review_date = fields.Datetime.now()

    def action_intake_reject_request(self):
        for record in self:
            if record.request_type != 'project_request':
                raise ValidationError(_("Only project requests can be rejected through this flow."))

            if not record.intake_rejection_reason:
                raise ValidationError(_("Please enter the rejection reason before rejecting the request."))

            record.intake_state = 'rejected'
            record.intake_reviewed_by = self.env.user
            record.intake_review_date = fields.Datetime.now()

    def action_intake_create_project_opportunity(self):
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