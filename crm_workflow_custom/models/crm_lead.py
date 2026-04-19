
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

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

    estimated_duration = fields.Char(string="Estimated Delivery Duration", tracking=True)
    project_deadline = fields.Date(string="Project Deadline", tracking=True)
    proposal_summary = fields.Text(string="Proposal Summary", tracking=True)
    proposal_amount = fields.Float(string="Estimated Project Value", tracking=True)
    negotiation_notes = fields.Text(string="Negotiation Notes", tracking=True)
    rejection_reason = fields.Text(string="Rejection Reason", tracking=True)

    approval_state = fields.Selection([
        ('not_needed', 'Not Needed'),
        ('to_approve', 'To Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Approval State", default='not_needed', tracking=True)

    last_followup_date = fields.Date(string="Last Follow-up Date", tracking=True)
    next_followup_date = fields.Date(string="Next Follow-up Date", tracking=True)
    followup_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('ongoing', 'Ongoing'),
        ('done', 'Done'),
        ('overdue', 'Overdue'),
    ], string="Follow-up Status", default='not_started', tracking=True)

    inactive_alert = fields.Boolean(string="Needs Follow-up", default=False, tracking=True)

    support_ticket_count = fields.Integer(
        string="Support Ticket Count",
        compute="_compute_support_ticket_count"
    )

    is_stage_new_inquiry = fields.Boolean(compute="_compute_stage_flags")
    is_stage_analysis = fields.Boolean(compute="_compute_stage_flags")
    is_stage_proposal = fields.Boolean(compute="_compute_stage_flags")
    is_stage_waiting_approval = fields.Boolean(compute="_compute_stage_flags")
    is_stage_approved = fields.Boolean(compute="_compute_stage_flags")
    is_stage_rejected = fields.Boolean(compute="_compute_stage_flags")

    @api.depends('stage_id')
    def _compute_stage_flags(self):
        for record in self:
            stage_name = (record.stage_id.name or '').strip()

            record.is_stage_new_inquiry = stage_name == 'New Inquiry'
            record.is_stage_analysis = stage_name == 'Requirement Analysis'
            record.is_stage_proposal = stage_name == 'Proposal Submitted'
            record.is_stage_waiting_approval = stage_name == 'Waiting Approval'
            record.is_stage_approved = stage_name == 'Approved'
            record.is_stage_rejected = stage_name == 'Rejected'

    def _compute_support_ticket_count(self):
        for lead in self:
            lead.support_ticket_count = self.env['crm.support.ticket'].search_count([
                ('lead_id', '=', lead.id)
            ])

    def _get_stage_by_name(self, stage_name):
        stage = self.env['crm.stage'].search([('name', '=', stage_name)], limit=1)
        if not stage:
            raise UserError(_("Stage '%s' was not found.") % stage_name)
        return stage

    def action_start_analysis(self):
        for record in self:
            stage = record._get_stage_by_name('Requirement Analysis')
            record.stage_id = stage.id

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

    def action_send_to_approval(self):
        for record in self:
            if not record.proposal_summary or not record.proposal_amount or not record.project_deadline:
                raise ValidationError(_("Proposal summary, estimated project value, and project deadline must be filled before sending for approval."))
            stage = record._get_stage_by_name('Waiting Approval')
            record.stage_id = stage.id
            record.approval_state = 'to_approve'

    def action_approve_project(self):
        for record in self:
            stage = record._get_stage_by_name('Approved')
            record.stage_id = stage.id
            record.approval_state = 'approved'

    def action_reject_project(self):
        for record in self:
            if not record.rejection_reason:
                raise ValidationError(_("Please enter the rejection reason before rejecting the project."))
            stage = record._get_stage_by_name('Rejected')
            record.stage_id = stage.id
            record.approval_state = 'rejected'

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

    @api.model
    def _cron_check_inactive_leads(self):
        today = fields.Date.today()
        leads = self.search([
            ('next_followup_date', '!=', False),
            ('next_followup_date', '<', today),
            ('approval_state', 'not in', ['approved', 'rejected']),
        ])
        for lead in leads:
            lead.followup_status = 'overdue'
            lead.inactive_alert = True