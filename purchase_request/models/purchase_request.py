from odoo import models, fields, api
from odoo.exceptions import UserError
from lxml import etree


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
        default=lambda self: self._default_requester_category(),
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


    is_current_user_department_manager = fields.Boolean(
        string='Is Current User Department Manager',
        compute='_compute_user_access_flags',
    )

    is_current_user_finance = fields.Boolean(
        string='Is Current User Finance',
        compute='_compute_user_access_flags',
    )


    is_current_user_coordinator = fields.Boolean(
        string='Is Current User Coordinator',
        compute='_compute_user_access_flags',
    )

    is_current_user_principal = fields.Boolean(
        string='Is Current User Principal',
        compute='_compute_user_access_flags',
    )


    is_current_user_can_reject = fields.Boolean(
        string='Can Current User Reject',
        compute='_compute_user_access_flags',
    )

    allowed_user_ids = fields.Many2many(
        'res.users',
        string='Allowed Users',
        compute='_compute_allowed_user_ids',
        store=True,
    )


    is_current_user_can_create_pr = fields.Boolean(
        string='Can Current User Create Purchase Request',
        compute='_compute_user_access_flags',
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
        user_group_ids = self.env.user.groups_id.ids

        if 79 not in user_group_ids and 61 not in user_group_ids:
            raise UserError("Only users in the Teacher or Administrator groups can create a Purchase Request.")

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or 'New'

        return super().create(vals)

    @api.model
    def _default_requester_category(self):
        user_group_ids = self.env.user.groups_id.ids

        if 79 in user_group_ids:
            return 'teacher'
        elif 61 in user_group_ids:
            return 'admin'
        return False


    @api.onchange('requester_id')
    def _onchange_requester(self):
        if self.requester_id and self.requester_id.user_id:
            requester_group_ids = self.requester_id.user_id.groups_id.ids

            if 79 in requester_group_ids:
                self.requester_category = 'teacher'
            elif 61 in requester_group_ids:
                self.requester_category = 'admin'
            else:
                self.requester_category = False


    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)

        user_group_ids = self.env.user.groups_id.ids
        can_create = 79 in user_group_ids or 61 in user_group_ids

        if view_type in ['list', 'form']:
            arch = etree.fromstring(res['arch'])
            arch.set('create', 'true' if can_create else 'false')
            res['arch'] = etree.tostring(arch, encoding='unicode')

        return res


    @api.depends(
    'state',
    'requester_id',
    'requester_id.user_id',
    'department_id',
    'department_id.manager_id',
    'department_id.manager_id.user_id',
    'requester_category',
    )
    def _compute_allowed_user_ids(self):
        coordinator_users = self.env['res.users'].search([('groups_id', 'in', [81])])
        principal_users = self.env['res.users'].search([('groups_id', 'in', [96])])
        finance_users = self.env['res.users'].search([('employee_ids.department_id', '=', 2)])
        procurement_users = self.env['res.users'].search([('employee_ids.department_id', '=', 5)])


        procurement_officer_users = self.env['res.users'].search([('groups_id', 'in', [90])])
        director_finance_users = self.env['res.users'].search([('groups_id', 'in', [91])])
        deputy_ceo_users = self.env['res.users'].search([('groups_id', 'in', [92])])
        ceo_users = self.env['res.users'].search([('groups_id', 'in', [93])])


        for rec in self:
            users = self.env['res.users']

            # requester can always see own request
            if rec.requester_id and rec.requester_id.user_id:
                users |= rec.requester_id.user_id

            # while still draft, only requester can see it
            if rec.state == 'draft':
                rec.allowed_user_ids = [(6, 0, users.ids)]
                continue

            # after submission, expand visibility by route
            if rec.requester_category == 'admin':
                if rec.department_id and rec.department_id.manager_id and rec.department_id.manager_id.user_id:
                    users |= rec.department_id.manager_id.user_id

            elif rec.requester_category == 'teacher':
                users |= coordinator_users
                users |= principal_users

            # finance can see requests at budget stage and after approval
            if rec.state in ('waiting_budget', 'approved'):
                users |= finance_users

            # procurement can see approved requests
            if rec.state == 'approved':
                users |= procurement_officer_users
                users |= director_finance_users
                users |= deputy_ceo_users
                users |= ceo_users

            rec.allowed_user_ids = [(6, 0, users.ids)]


    def _compute_user_access_flags(self):
        current_user = self.env.user
        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', current_user.id)],
            limit=1
        )

        for rec in self:
            rec.is_current_user_department_manager = bool(
                rec.department_id
                and rec.department_id.manager_id
                and rec.department_id.manager_id.user_id
                and rec.department_id.manager_id.user_id == current_user
            )

            rec.is_current_user_finance = bool(
                current_employee
                and current_employee.department_id
                and current_employee.department_id.id == 2
            )

            rec.is_current_user_coordinator = 81 in current_user.groups_id.ids
            rec.is_current_user_principal = 96 in current_user.groups_id.ids
           
            rec.is_current_user_can_reject = (
                (rec.state == 'waiting_coordinator' and rec.is_current_user_coordinator)
                or (rec.state == 'waiting_principal' and rec.is_current_user_principal)
                or (rec.state == 'waiting_director' and rec.is_current_user_department_manager)
                or (rec.state == 'waiting_budget' and rec.is_current_user_finance)
            )

            rec.is_current_user_can_create_pr = 79 in current_user.groups_id.ids or 61 in current_user.groups_id.ids

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

            if 81 not in self.env.user.groups_id.ids:
                raise UserError("Only Coordinator users can approve at this stage.")

            rec.state = 'waiting_principal'
            rec.coordinator_approved_by = self.env.user
            rec.coordinator_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Coordinator.")
    

    def action_principal_approve(self):
        for rec in self:
            if rec.state != 'waiting_principal':
                continue

            if 96 not in self.env.user.groups_id.ids:
                raise UserError("Only Academic Principal users can approve at this stage.")

            rec.state = 'waiting_budget'
            rec.principal_approved_by = self.env.user
            rec.principal_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Academic Principal / Vice Principal.")


    def action_director_approve(self):
        for rec in self:
            if rec.state != 'waiting_director':
                continue
            
            if not rec.department_id or not rec.department_id.manager_id or not rec.department_id.manager_id.user_id:
                raise UserError("This request's department does not have a manager with a linked user.")

            if rec.department_id.manager_id.user_id != self.env.user:
                raise UserError("Only the manager of the request department can approve this request.")

            rec.state = 'waiting_budget'
            rec.director_approved_by = self.env.user
            rec.director_approved_date = fields.Datetime.now()
            rec.message_post(body="Purchase Request approved by Department Director.")



    def action_verify_budget(self):
        self.ensure_one()

        current_employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )

        if self.state != 'waiting_budget':
            raise UserError("This purchase request is not waiting for budget verification.")

        if not current_employee or not current_employee.department_id:
            raise UserError("The current user is not linked to an employee with a department.")

        if current_employee.department_id.id != 2:
            raise UserError("Only employees in the Finance & Accounting department can verify budget.")

        return {
            'name': 'Verify Budget',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.request.budget.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_request_id': self.id,
                'default_available_budget': self.budget_available_amount,
                'default_budget_note': self.budget_note,
            },
        }


    def action_reject(self):
        self.ensure_one()

        if not self.is_current_user_can_reject:
            raise UserError("You are not allowed to reject this request at the current stage.")


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

            if 'requester_category' in vals:
                raise UserError("Requester Category cannot be changed manually. It is assigned automatically.")

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
    

    def unlink(self):
        user_group_ids = self.env.user.groups_id.ids

        for rec in self:
            if 79 not in user_group_ids and 61 not in user_group_ids:
                raise UserError("Only users in the Teacher or Administrator groups can delete purchase requests.")

            if rec.state != 'draft':
                raise UserError("Only draft purchase requests can be deleted.")

        return super().unlink()


    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        if operation == 'create':
            user_group_ids = self.env.user.groups_id.ids
            if 79 in user_group_ids or 61 in user_group_ids:
                return True
        return super().check_access_rights(operation, raise_exception=raise_exception)