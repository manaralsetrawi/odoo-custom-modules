from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    requester_id = fields.Many2one(
        'hr.employee',
        string='Requester',
        tracking=True,
        default=lambda self: self._default_requester(),
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='requester_id.department_id',
        store=True,
        readonly=True,
        tracking=True,
    )

    requester_category = fields.Selection(
        [
            ('teacher', 'Teacher'),
            ('admin', 'Administrative Staff'),
        ],
        string='Requester Category',
        tracking=True,
    )

    request_reason = fields.Text(
        string='Reason',
        tracking=True,
    )

    required_date = fields.Date(
        string='Required Date',
        tracking=True,
    )

    pr_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting_coordinator', 'Waiting Coordinator Approval'),
            ('waiting_principal', 'Waiting Academic Principal / Vice Principal Approval'),
            ('waiting_director', 'Waiting Department Director Approval'),
            ('waiting_budget', 'Waiting Budget Verification'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='PR Workflow Status',
        default='draft',
        tracking=True,
    )

    coordinator_approved_by = fields.Many2one(
        'res.users',
        string='Coordinator Approved By',
        readonly=True,
        tracking=True,
    )

    coordinator_approved_date = fields.Datetime(
        string='Coordinator Approval Date',
        readonly=True,
        tracking=True,
    )

    principal_approved_by = fields.Many2one(
        'res.users',
        string='Principal / Vice Principal Approved By',
        readonly=True,
        tracking=True,
    )

    principal_approved_date = fields.Datetime(
        string='Principal / Vice Principal Approval Date',
        readonly=True,
        tracking=True,
    )

    director_approved_by = fields.Many2one(
        'res.users',
        string='Department Director Approved By',
        readonly=True,
        tracking=True,
    )

    director_approved_date = fields.Datetime(
        string='Department Director Approval Date',
        readonly=True,
        tracking=True,
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True,
    )

    budget_available = fields.Float(
        string='Available Budget',
        tracking=True,
    )

    budget_verified = fields.Boolean(
        string='Budget Verified',
        readonly=True,
        tracking=True,
    )

    budget_verified_by = fields.Many2one(
        'res.users',
        string='Budget Verified By',
        readonly=True,
        tracking=True,
    )

    budget_verified_date = fields.Datetime(
        string='Budget Verification Date',
        readonly=True,
        tracking=True,
    )

    budget_note = fields.Text(
        string='Budget Verification Note',
        tracking=True,
    )

    pr_estimated_total = fields.Float(
        string='PR Estimated Total',
        compute='_compute_pr_total',
        store=True,
    )

    @api.depends('order_line.price_subtotal')
    def _compute_pr_total(self):
        for order in self:
            order.pr_estimated_total = sum(order.order_line.mapped('price_subtotal'))

    @api.model
    def _default_requester(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )
        return employee.id if employee else False

    @api.onchange('requester_id')
    def _onchange_requester(self):
        for rec in self:
            if rec.requester_id:
                rec.department_id = rec.requester_id.department_id

    def action_submit_pr(self):
        for rec in self:
            if not rec.requester_category:
                raise UserError("Please select the requester category before submitting.")

            if rec.requester_category == 'teacher':
                rec.pr_state = 'waiting_coordinator'
            elif rec.requester_category == 'admin':
                rec.pr_state = 'waiting_director'

            rec.message_post(body="Purchase Request submitted for approval.")

    def action_coordinator_approve(self):
        for rec in self:
            if rec.pr_state != 'waiting_coordinator':
                continue

            rec.pr_state = 'waiting_principal'
            rec.coordinator_approved_by = self.env.user
            rec.coordinator_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Coordinator.")

    def action_principal_approve(self):
        for rec in self:
            if rec.pr_state != 'waiting_principal':
                continue

            rec.pr_state = 'waiting_budget'
            rec.principal_approved_by = self.env.user
            rec.principal_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Academic Principal / Vice Principal.")

    def action_director_approve(self):
        for rec in self:
            if rec.pr_state != 'waiting_director':
                continue

            rec.pr_state = 'waiting_budget'
            rec.director_approved_by = self.env.user
            rec.director_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Department Director.")

    def action_reject_pr(self):
        for rec in self:
            if rec.pr_state not in ['waiting_coordinator', 'waiting_principal', 'waiting_director', 'waiting_budget']:
                continue

            if not rec.rejection_reason:
                raise UserError("Please enter the rejection reason before rejecting the request.")

            rec.pr_state = 'rejected'
            rec.message_post(body=f"Purchase Request rejected. Reason: {rec.rejection_reason}")

    def action_verify_budget(self):
        for rec in self:
            if rec.pr_state != 'waiting_budget':
                continue

            if rec.budget_available < rec.pr_estimated_total:
                raise UserError("Budget is insufficient for this purchase request.")

            rec.budget_verified = True
            rec.budget_verified_by = self.env.user
            rec.budget_verified_date = fields.Datetime.now()
            rec.pr_state = 'approved'
            rec.message_post(body="Budget verified by Finance. Purchase Request approved.")