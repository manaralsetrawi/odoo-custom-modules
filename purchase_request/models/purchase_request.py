from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='PR Number',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True,
    )

    requester_id = fields.Many2one(
        'hr.employee',
        string='Requester',
        required=True,
        default=lambda self: self._default_requester(),
        readonly=True,
        tracking=True
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
        required=True,
        tracking=True,
    )

    required_date = fields.Date(
        string='Required Date',
        required=True,
        tracking=True,
    )

    request_reason = fields.Text(
        string='Reason',
        required=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('waiting_coordinator', 'Waiting Coordinator Approval'),
            ('waiting_principal', 'Waiting Academic Principal Approval'),
            ('waiting_director', 'Waiting Department Director Approval'),
            ('waiting_budget', 'Waiting Budget Verification'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )

    line_ids = fields.One2many(
        'purchase.request.line',
        'request_id',
        string='Request Lines',
    )

    amount_total = fields.Float(
        string='Total Amount',
        compute='_compute_amount_total',
        store=True,
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
        string='Principal Approved By',
        readonly=True,
        tracking=True,
    )

    principal_approved_date = fields.Datetime(
        string='Principal Approval Date',
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

    budget_available_amount = fields.Float(
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

    @api.model
    def _default_requester(self):
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )
        return employee.id

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('subtotal'))
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or 'New'
        return super().create(vals)


    @api.onchange('requester_id')
    def _onchange_requester(self):
        if self.requester_id and self.requester_id.department_id:
            if 'Academic' in self.requester_id.department_id.name:
                self.requester_category = 'teacher'
            else:
                self.requester_category = 'admin'
    

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError("Please add at least one request line before submitting.")

            if not rec.requester_category:
                raise UserError("Please select the requester category before submitting.")

            if rec.requester_category == 'teacher':
                rec.state = 'waiting_coordinator'
                rec.message_post(body="Purchase Request submitted and routed to Coordinator.")

            elif rec.requester_category == 'admin':
                rec.state = 'waiting_director'
                rec.message_post(body="Purchase Request submitted and routed to Department Director.")


    def action_coordinator_approve(self):
        for rec in self:
            if rec.state != 'waiting_coordinator':
                continue

            rec.state = 'waiting_principal'
            rec.coordinator_approved_by = self.env.user
            rec.coordinator_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Coordinator.")
    
    def action_principal_approve(self):
        for rec in self:
            if rec.state != 'waiting_principal':
                continue

            rec.state = 'waiting_budget'
            rec.principal_approved_by = self.env.user
            rec.principal_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Academic Principal / Vice Principal.")


    def action_director_approve(self):
        for rec in self:
            if rec.state != 'waiting_director':
                continue

            rec.state = 'waiting_budget'
            rec.director_approved_by = self.env.user
            rec.director_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Department Director.")

    def action_verify_budget(self):
        for rec in self:
            if rec.state != 'waiting_budget':
                continue

            if rec.budget_available_amount < rec.amount_total:
                raise UserError("Budget is insufficient for this purchase request.")

            rec.budget_verified = True
            rec.budget_verified_by = self.env.user
            rec.budget_verified_date = fields.Datetime.now()
            rec.state = 'approved'
            rec.message_post(body="Budget verified by Finance. Purchase Request approved.")

    def action_reject(self):
        self.ensure_one()

        return {
            'name': 'Reject Purchase Request',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_request_id': self.id,
            },
        }


    def write(self, vals):

        for rec in self:

            # Prevent changing requester completely
            if 'requester_id' in vals:
                raise UserError("Requester cannot be changed. It is automatically assigned to the logged-in user.")

            protected_fields = {
                'requester_category',
                'required_date',
                'request_reason',
                'line_ids',
            }

            if rec.state != 'draft' and protected_fields.intersection(vals.keys()):
                raise UserError(
                    "You cannot modify request details after submission."
                )

        return super().write(vals)