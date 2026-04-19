from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================
    # Workflow / Project Fields
    # =========================================================
    technical_feasibility = fields.Selection([
        ('pending', 'Pending'),
        ('feasible', 'Feasible'),
        ('not_feasible', 'Not Feasible'),
    ], string="Technical Feasibility Status", default='pending', tracking=True)

    complexity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Complexity Level", tracking=True)

    estimated_duration = fields.Char(
        string="Estimated Delivery Duration",
        tracking=True
    )

    project_deadline = fields.Date(
        string="Project Deadline",
        tracking=True
    )

    proposal_summary = fields.Text(
        string="Proposal Summary",
        tracking=True
    )

    proposal_amount = fields.Float(
        string="Estimated Project Value",
        tracking=True
    )

    negotiation_notes = fields.Text(
        string="Negotiation Notes",
        tracking=True
    )

    rejection_reason = fields.Text(
        string="Rejection Reason",
        tracking=True
    )

    approval_state = fields.Selection([
        ('not_needed', 'Not Needed'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Approval State", default='not_needed', tracking=True)

    # =========================================================
    # Follow-up Fields
    # =========================================================
    last_followup_date = fields.Date(
        string="Last Follow-up Date",
        tracking=True
    )

    next_followup_date = fields.Date(
        string="Next Follow-up Date",
        tracking=True
    )

    followup_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done'),
        ('overdue', 'Overdue'),
    ], string="Follow-up Status", default='not_started', tracking=True)

    inactive_alert = fields.Boolean(
        string="Needs Follow-up",
        default=False,
        tracking=True
    )

    # =========================================================
    # Support Integration
    # =========================================================
    support_ticket_count = fields.Integer(
        string="Support Ticket Count",
        compute="_compute_support_ticket_count"
    )

    # =========================================================
    # Helper Boolean Fields For Button Visibility
    # =========================================================
    is_stage_new_inquiry = fields.Boolean(compute="_compute_stage_flags")
    is_stage_initial_discussion = fields.Boolean(compute="_compute_stage_flags")
    is_stage_analysis = fields.Boolean(compute="_compute_stage_flags")
    is_stage_solution_design = fields.Boolean(compute="_compute_stage_flags")
    is_stage_proposal = fields.Boolean(compute="_compute_stage_flags")
    is_stage_waiting_approval = fields.Boolean(compute="_compute_stage_flags")
    is_stage_approved = fields.Boolean(compute="_compute_stage_flags")
    is_stage_rejected = fields.Boolean(compute="_compute_stage_flags")

    # =========================================================
    # Create Override
    # =========================================================
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_followup_activity(
                summary="Initial Follow-up",
                note="A new project request was created. Please review and follow up."
            )
        return records

    # =========================================================
    # Compute Methods
    # =========================================================
    @api.depends('stage_id')
    def _compute_stage_flags(self):
        for record in self:
            stage_name = (record.stage_id.name or '').strip()

            record.is_stage_new_inquiry = stage_name == 'New Inquiry'
            record.is_stage_initial_discussion = stage_name == 'Initial Discussion'
            record.is_stage_analysis = stage_name == 'Requirement Analysis'
            record.is_stage_solution_design = stage_name == 'Solution Design'
            record.is_stage_proposal = stage_name == 'Proposal Submitted'
            record.is_stage_waiting_approval = stage_name == 'Waiting Approval'
            record.is_stage_approved = stage_name == 'Approved'
            record.is_stage_rejected = stage_name == 'Rejected'

    def _compute_support_ticket_count(self):
        for lead in self:
            lead.support_ticket_count = self.env['crm.support.ticket'].search_count([
                ('lead_id', '=', lead.id)
            ])

    # =========================================================
    # Helper Methods
    # =========================================================
    def _get_stage_by_name(self, stage_name):
        stage = self.env['crm.stage'].search([('name', '=', stage_name)], limit=1)
        if not stage:
            raise UserError(_("Stage '%s' was not found.") % stage_name)
        return stage

    def _create_followup_activity(self, summary, note=''):
        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return

        model_id = self.env['ir.model']._get_id('crm.lead')

        for record in self:
            if not record.user_id:
                continue

            self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'summary': summary,
                'note': note,
                'res_model_id': model_id,
                'res_id': record.id,
                'user_id': record.user_id.id,
                'date_deadline': fields.Date.today(),
            })

    # =========================================================
    # Stage Cleanup / Sync
    # Safe version: creates/updates your stages and remaps old leads
    # Does NOT use 'active' because crm.stage has no active field here
    # =========================================================
    @api.model
    def sync_workflow_stages(self):
        stage_model = self.env['crm.stage'].sudo()
        lead_model = self.env['crm.lead'].sudo()

        desired_stages = [
            {'name': 'New Inquiry', 'sequence': 1, 'is_won': False, 'fold': False},
            {'name': 'Initial Discussion', 'sequence': 2, 'is_won': False, 'fold': False},
            {'name': 'Requirement Analysis', 'sequence': 3, 'is_won': False, 'fold': False},
            {'name': 'Solution Design', 'sequence': 4, 'is_won': False, 'fold': False},
            {'name': 'Proposal Submitted', 'sequence': 5, 'is_won': False, 'fold': False},
            {'name': 'Waiting Approval', 'sequence': 6, 'is_won': False, 'fold': False},
            {'name': 'Approved', 'sequence': 7, 'is_won': True, 'fold': False},
            {'name': 'Rejected', 'sequence': 8, 'is_won': False, 'fold': True},
        ]

        created_or_existing = {}
        for vals in desired_stages:
            stage = stage_model.search([('name', '=', vals['name'])], limit=1)
            if stage:
                stage.write({
                    'sequence': vals['sequence'],
                    'is_won': vals['is_won'],
                    'fold': vals['fold'],
                })
            else:
                stage = stage_model.create({
                    'name': vals['name'],
                    'sequence': vals['sequence'],
                    'is_won': vals['is_won'],
                    'fold': vals['fold'],
                })
            created_or_existing[vals['name']] = stage

        # Move leads from old default stages to your custom stages
        stage_mapping = {
            'New': 'New Inquiry',
            'Qualified': 'Initial Discussion',
            'Proposition': 'Proposal Submitted',
            'Won': 'Approved',
            'Lost': 'Rejected',
        }

        for old_name, new_name in stage_mapping.items():
            old_stage = stage_model.search([('name', '=', old_name)], limit=1)
            new_stage = created_or_existing.get(new_name)
            if old_stage and new_stage and old_stage.id != new_stage.id:
                leads = lead_model.search([('stage_id', '=', old_stage.id)])
                if leads:
                    leads.write({'stage_id': new_stage.id})

        # NOTE:
        # We are not archiving/deleting old stages here because that caused issues
        # and can be risky. We will hide default Won/Lost buttons with SCSS and
        # you can manually remove unused stages later from CRM configuration if needed.

        return True

    # =========================================================
    # Workflow Actions
    # =========================================================
    def action_start_analysis(self):
        for record in self:
            stage = record._get_stage_by_name('Requirement Analysis')
            record.stage_id = stage.id
            record.followup_status = 'ongoing'
            record.last_followup_date = fields.Date.today()

            record._create_followup_activity(
                summary="Technical Analysis Required",
                note="Please review the project requirements and update the technical evaluation."
            )

    def action_submit_proposal(self):
        for record in self:
            if not record.proposal_summary:
                raise ValidationError(_("Please enter the proposal summary before submitting the proposal."))
            if not record.proposal_amount:
                raise ValidationError(_("Please enter the estimated project value before submitting the proposal."))
            if not record.project_deadline:
                raise ValidationError(_("Please enter the project deadline before submitting the proposal."))

            stage = record._get_stage_by_name('Proposal Submitted')
            record.stage_id = stage.id
            record.approval_state = 'to_approve'
            record.followup_status = 'ongoing'
            record.last_followup_date = fields.Date.today()

            record._create_followup_activity(
                summary="Proposal Follow-up",
                note="The proposal has been submitted. Follow up with the client or internal team as needed."
            )

    def action_send_to_approval(self):
        for record in self:
            if not record.proposal_summary:
                raise ValidationError(_("Please enter the proposal summary before sending for approval."))
            if not record.proposal_amount:
                raise ValidationError(_("Please enter the estimated project value before sending for approval."))
            if not record.project_deadline:
                raise ValidationError(_("Please enter the project deadline before sending for approval."))

            stage = record._get_stage_by_name('Waiting Approval')
            record.stage_id = stage.id
            record.approval_state = 'to_approve'
            record.last_followup_date = fields.Date.today()

            record._create_followup_activity(
                summary="Approval Needed",
                note="This project request is waiting for approval."
            )

    def action_approve_project(self):
        for record in self:
            stage = record._get_stage_by_name('Approved')
            record.stage_id = stage.id
            record.approval_state = 'approved'
            record.followup_status = 'done'
            record.last_followup_date = fields.Date.today()
            record.inactive_alert = False

    def action_reject_project(self):
        for record in self:
            if not record.rejection_reason:
                raise ValidationError(_("Please enter the rejection reason before rejecting the project."))

            stage = record._get_stage_by_name('Rejected')
            record.stage_id = stage.id
            record.approval_state = 'rejected'
            record.followup_status = 'done'
            record.last_followup_date = fields.Date.today()
            record.inactive_alert = False

    # =========================================================
    # Support Actions
    # =========================================================
    def action_create_support_ticket(self):
        self.ensure_one()

        ticket = self.env['crm.support.ticket'].create({
            'lead_id': self.id,
            'partner_id': self.partner_id.id,
            'subject': self.name or "Support Request",
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Support Ticket',
            'res_model': 'crm.support.ticket',
            'view_mode': 'form',
            'res_id': ticket.id,
            'target': 'current',
        }

    def action_view_support_tickets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Support Tickets',
            'res_model': 'crm.support.ticket',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'target': 'current',
        }

    # =========================================================
    # Scheduled Action (Cron)
    # =========================================================
    @api.model
    def _cron_check_inactive_leads(self):
        today = fields.Date.today()

        leads = self.search([
            ('next_followup_date', '!=', False),
            ('next_followup_date', '<', today),
            ('approval_state', 'not in', ['approved', 'rejected']),
        ])

        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        model_id = self.env['ir.model']._get_id('crm.lead')

        for lead in leads:
            lead.followup_status = 'overdue'
            lead.inactive_alert = True

            if activity_type and lead.user_id:
                existing_activity = self.env['mail.activity'].search([
                    ('res_model_id', '=', model_id),
                    ('res_id', '=', lead.id),
                    ('activity_type_id', '=', activity_type.id),
                    ('summary', '=', 'Overdue Follow-up Reminder'),
                    ('user_id', '=', lead.user_id.id),
                ], limit=1)

                if not existing_activity:
                    self.env['mail.activity'].create({
                        'activity_type_id': activity_type.id,
                        'summary': 'Overdue Follow-up Reminder',
                        'note': 'This project request has passed its next follow-up date and needs attention.',
                        'res_model_id': model_id,
                        'res_id': lead.id,
                        'user_id': lead.user_id.id,
                        'date_deadline': today,
                    })