from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='PR Reference',
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
        tracking=True,
        default=lambda self: self._default_requester(),
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        tracking=True,
        related='requester_id.department_id',
        store=True,
        readonly=False,
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

    reason = fields.Text(
        string='Reason',
        required=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('waiting_coordinator', 'Waiting Coordinator Approval'),
            ('waiting_principal', 'Waiting Principal Approval'),
            ('waiting_director', 'Waiting Director Approval'),
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

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError("Please add at least one request line before submitting.")

            if rec.requester_category == 'teacher':
                rec.state = 'waiting_coordinator'
                rec.message_post(body='Purchase Request submitted and routed to Coordinator for approval.')
            elif rec.requester_category == 'admin':
                rec.state = 'waiting_director'
                rec.message_post(body='Purchase Request submitted and routed to Department Director for approval.')
            else:
                rec.state = 'submitted'
                rec.message_post(body='Purchase Request submitted.')


    def action_coordinator_approve(self):
        for rec in self:
            if rec.state != 'waiting_coordinator':
                continue
            rec.state = 'waiting_principal'
            rec.coordinator_approved_by = self.env.user
            rec.coordinator_approved_date = fields.Datetime.now()
            rec.message_post(body='Coordinator approved the Purchase Request.')

    def action_principal_approve(self):
        for rec in self:
            if rec.state != 'waiting_principal':
                continue
            rec.state = 'waiting_budget'
            rec.principal_approved_by = self.env.user
            rec.principal_approved_date = fields.Datetime.now()
            rec.message_post(body='Academic Principal / Vice Principal approved the Purchase Request.')

    def action_director_approve(self):
        for rec in self:
            if rec.state != 'waiting_director':
                continue
            rec.state = 'waiting_budget'
            rec.director_approved_by = self.env.user
            rec.director_approved_date = fields.Datetime.now()
            rec.message_post(body='Department Director approved the Purchase Request.')

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
            rec.message_post(body='Purchase Request has been rejected.')


    @api.model
    def _default_requester(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee.id if employee else False

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('subtotal'))
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or 'New'
        return super().create(vals_list) 