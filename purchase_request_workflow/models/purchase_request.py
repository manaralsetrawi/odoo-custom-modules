from odoo import models, fields, api


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

    @api.model
    def _default_requester(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return employee.id if employee else False

    @api.depends('line_ids.subtotal')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = sum(rec.line_ids.mapped('subtotal'))