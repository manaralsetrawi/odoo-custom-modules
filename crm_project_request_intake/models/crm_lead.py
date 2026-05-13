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
        string='Assigned Project Team',
        readonly=True,
        copy=False,
    )

    assigned_employee_ids = fields.Many2many(
        'hr.employee',
        'crm_lead_assigned_employee_rel',
        'lead_id',
        'employee_id',
        string='Assigned Employees',
        readonly=True,
        copy=False,
    )

    planned_start_date = fields.Date(
        string='Project Start Date',
        copy=False,
    )

    planned_end_date = fields.Date(
        string='Project End Date',
        copy=False,
    )


    assignment_count = fields.Integer(
    string='Assignment Count',
    compute='_compute_assignment_count',
    )

    assignment_ids = fields.One2many(
        'project.team.assignment',
        'lead_id',
        string='Project Assignments',
    )

    email_log_ids = fields.One2many(
    'crm.email.log',
    'lead_id',
    string='Email Logs',
    )

    email_log_count = fields.Integer(
        string='Email Log Count',
        compute='_compute_email_log_count',
    )

    def _compute_email_log_count(self):
        for rec in self:
            rec.email_log_count = len(rec.email_log_ids)

    def _compute_assignment_count(self):
        for rec in self:
            rec.assignment_count = len(rec.assignment_ids)



    def action_view_email_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Email Logs'),
            'res_model': 'crm.email.log',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }

    def action_view_project_assignments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project Assignments'),
            'res_model': 'project.team.assignment',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }

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
        self.ensure_one()

        if self.request_type != 'project_request' or self.type != 'lead':
            raise ValidationError(_("Only project request leads can be approved."))

        if self.intake_state != 'under_review':
            raise ValidationError(_("Only requests under review can be approved."))

        missing_fields = []

        if not self.review_project_type_id:
            missing_fields.append(_("Project Type"))


        if not self.review_client_segment_id:
            missing_fields.append(_("Client Segment"))
        

        if not self.review_project_feature_ids:
            missing_fields.append(_("Development and Features"))

        if not self.review_project_features or not self.review_project_features.strip():
            missing_fields.append(_("Project Features"))

        if not self.intake_meeting_notes or not self.intake_meeting_notes.strip():
            missing_fields.append(_("Meeting Notes"))

        if not self.intake_project_requirements or not self.intake_project_requirements.strip():
            missing_fields.append(_("Project Requirements"))

        if not self.intake_solution_summary or not self.intake_solution_summary.strip():
            missing_fields.append(_("Solution Summary"))

        if not self.review_recommendation or not self.review_recommendation.strip():
            missing_fields.append(_("Manager Recommendation"))

        if not self.review_risk_notes or not self.review_risk_notes.strip():
            missing_fields.append(_("Risk Notes"))

        if missing_fields:
            raise ValidationError(_(
                "You cannot approve this request until the Project Review Details are completed.\n\n"
                "Please fill in:\n- %s"
            ) % "\n- ".join(missing_fields))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Assign Project Team'),
            'res_model': 'project.team.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'approval_flow': True,
            },
        }


    def _get_company_email_for_notifications(self):
        self.ensure_one()
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        return mail_server.smtp_user if mail_server and mail_server.smtp_user else False


    def _send_project_request_approval_email(self):
        self.ensure_one()

        company_email = self._get_company_email_for_notifications()
        client_email = self.intake_client_email or self.email_from

        if not company_email or not client_email:
            return

        logo_url = "https://ncst.edu.bh/wp-content/uploads/2025/05/ncst-logo.png"
        subject = "Your project request has been approved"

        body_html = """
        <div style="margin:0; padding:0; background-color:#f4f6f8;">
            <div style="max-width:700px; margin:0 auto; background-color:#ffffff; padding:30px; font-family:Arial, sans-serif; color:#333333; border:1px solid #dddddd; border-radius:8px;">

                <div style="text-align:center; margin-bottom:20px;">
                    <img src="%s" alt="Company Logo" style="max-height:80px; max-width:220px;"/>
                </div>

                <div style="border-bottom:2px solid #0b2c3d; padding-bottom:15px; margin-bottom:25px;">
                    <h2 style="margin:0; color:#0b2c3d;">Project Request Approved</h2>
                </div>

                <p>Dear %s,</p>

                <p>
                    We are pleased to inform you that your project request has been reviewed and approved.
                </p>

                <p>
                    Our team will proceed with the next steps and may contact you if additional coordination is required.
                </p>

                <div style="margin-top:20px;">
                    <p style="font-weight:bold; margin-bottom:10px;">Request Summary:</p>
                    <table style="width:100%%; border-collapse:collapse; font-size:14px;">
                        <tr>
                            <td style="padding:8px 0; width:180px; font-weight:bold;">Project Title:</td>
                            <td style="padding:8px 0;">%s</td>
                        </tr>
                        <tr>
                            <td style="padding:8px 0; font-weight:bold;">Project Type:</td>
                            <td style="padding:8px 0;">%s</td>
                        </tr>
                    </table>
                </div>

                <p style="margin-top:25px;">
                    Best regards,<br/>
                    NCST Team
                </p>

                <div style="margin-top:30px; border-top:1px solid #dddddd; padding-top:15px; font-size:12px; color:#777777;">
                    This is an automated notification email.
                </div>
            </div>
        </div>
        """ % (
            logo_url,
            self.intake_client_name or self.contact_name or 'Client',
            self.intake_project_title or self.name or '-',
            self.review_project_type_id.name or '-',
        )

        self.env['mail.mail'].sudo().create({
            'subject': subject,
            'email_from': company_email,
            'email_to': client_email,
            'reply_to': company_email,
            'body_html': body_html,
        }).send()


    def _send_project_request_rejection_email(self):
        self.ensure_one()

        company_email = self._get_company_email_for_notifications()
        client_email = self.intake_client_email or self.email_from

        if not company_email or not client_email:
            return

        logo_url = "https://ncst.edu.bh/wp-content/uploads/2025/05/ncst-logo.png"
        subject = "Update on your project request"

        body_html = """
        <div style="margin:0; padding:0; background-color:#f4f6f8;">
            <div style="max-width:700px; margin:0 auto; background-color:#ffffff; padding:30px; font-family:Arial, sans-serif; color:#333333; border:1px solid #dddddd; border-radius:8px;">

                <div style="text-align:center; margin-bottom:20px;">
                    <img src="%s" alt="Company Logo" style="max-height:80px; max-width:220px;"/>
                </div>

                <div style="border-bottom:2px solid #0b2c3d; padding-bottom:15px; margin-bottom:25px;">
                    <h2 style="margin:0; color:#0b2c3d;">Project Request Review Result</h2>
                </div>

                <p>Dear %s,</p>

                <p>
                    Thank you for your interest and for submitting your project request.
                    After review, we regret to inform you that we are unable to proceed with the request at this time.
                </p>

                <div style="margin-top:20px;">
                    <p style="font-weight:bold; margin-bottom:10px;">Request Summary:</p>
                    <table style="width:100%%; border-collapse:collapse; font-size:14px;">
                        <tr>
                            <td style="padding:8px 0; width:180px; font-weight:bold;">Project Title:</td>
                            <td style="padding:8px 0;">%s</td>
                        </tr>
                    </table>
                </div>

                <div style="margin-top:20px;">
                    <p style="font-weight:bold; margin-bottom:10px;">Reason:</p>
                    <div style="background-color:#f8f9fa; border:1px solid #e0e0e0; padding:15px; border-radius:6px; line-height:1.6;">
                        %s
                    </div>
                </div>

                <p style="margin-top:25px;">
                    Best regards,<br/>
                    NCST Team
                </p>

                <div style="margin-top:30px; border-top:1px solid #dddddd; padding-top:15px; font-size:12px; color:#777777;">
                    This is an automated notification email.
                </div>
            </div>
        </div>
        """ % (
            logo_url,
            self.intake_client_name or self.contact_name or 'Client',
            self.intake_project_title or self.name or '-',
            self.intake_rejection_reason or 'Not specified.',
        )

        self.env['mail.mail'].sudo().create({
            'subject': subject,
            'email_from': company_email,
            'email_to': client_email,
            'reply_to': company_email,
            'body_html': body_html,
        }).send()



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
    

    def message_post(self, **kwargs):
        messages = super().message_post(**kwargs)

        for lead in self:
            body = kwargs.get('body') or ''
            subject = kwargs.get('subject') or _('Message')

            # Only log manual messages, not internal notes
            message_type = kwargs.get('message_type')
            subtype_xmlid = kwargs.get('subtype_xmlid')

            if message_type == 'comment' and subtype_xmlid != 'mail.mt_note':
                recipient_emails = ', '.join(
                    partner.email for partner in lead.message_partner_ids
                    if partner.email
                )

                self.env['crm.email.log'].sudo().create({
                    'lead_id': lead.id,
                    'subject': subject or 'Manual Message',
                    'sender_email': self.env.user.email or '',
                    'recipient_email': recipient_emails or lead.email_from or lead.intake_client_email or '',
                    'email_type': 'general',
                    'direction': 'outgoing',
                    'body_preview': body,
                    'notes': 'Manual message sent from the CRM chatter.',
                })

        return messages
    

    @api.model
    def get_project_request_dashboard_data(self):
        Lead = self.env['crm.lead'].with_context(active_test=False)

        domain_base = [
            ('request_type', '=', 'project_request'),
            ('type', '=', 'lead'),
        ]

        pending_domain = domain_base + [('intake_state', '=', 'submitted')]
        under_review_domain = domain_base + [('intake_state', '=', 'under_review')]
        approved_domain = domain_base + [('intake_state', '=', 'approved')]
        rejected_domain = domain_base + [('intake_state', '=', 'rejected')]

        high_priority_domain = domain_base + [
            ('intake_state', 'in', ['submitted', 'under_review']),
            ('priority', '=', '2'),
        ]

        very_high_priority_domain = domain_base + [
            ('intake_state', 'in', ['submitted', 'under_review']),
            ('priority', '=', '3'),
        ]

    
        recent_requests = Lead.search(
            domain_base,
            order='create_date desc',
            limit=6
        )

        return {
            'total_requests': Lead.search_count(domain_base),
            'pending_requests': Lead.search_count(pending_domain),
            'under_review_requests': Lead.search_count(under_review_domain),
            'approved_requests': Lead.search_count(approved_domain),
            'rejected_requests': Lead.search_count(rejected_domain),
            'high_priority_requests': Lead.search_count(high_priority_domain),
            'very_high_priority_requests': Lead.search_count(very_high_priority_domain),
            'recent_requests': [{
                'id': lead.id,
                'name': lead.name,
                'client': lead.contact_name or lead.intake_client_name or '-',
                'company': lead.intake_company_name or '-',
                'status': dict(lead._fields['intake_state'].selection).get(lead.intake_state),
                'priority': lead.priority,
                'budget': lead.intake_requested_budget,
                'active': lead.active,
            } for lead in recent_requests],
        }
    

    @api.model
    def action_open_project_request_leads_from_dashboard(self, status=False, priority=False):
        domain = [
            ('request_type', '=', 'project_request'),
            ('type', '=', 'lead'),
        ]

        if status:
            domain.append(('intake_state', '=', status))

        if priority:
            domain.append(('priority', '=', priority))
            domain.append(('intake_state', 'in', ['submitted', 'under_review']))

        kanban_view = self.env.ref('crm.view_crm_lead_kanban', raise_if_not_found=False)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Project Requests',
            'res_model': 'crm.lead',
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view.id, 'kanban') if kanban_view else (False, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': domain,
            'context': {
                'default_type': 'lead',
                'default_request_type': 'project_request',
                'group_by': False,
                'active_test': False,
            },
            'target': 'current',
        }