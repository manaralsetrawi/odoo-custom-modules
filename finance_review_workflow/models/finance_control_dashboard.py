from odoo import api, fields, models


class FinanceControlDashboard(models.Model):
    _name = 'finance.control.dashboard'
    _description = 'Finance Control Dashboard'

    name = fields.Char(default='Finance Control', readonly=True)

    draft_invoice_count = fields.Integer(
        string='Draft Invoices',
        compute='_compute_dashboard_counts',
        readonly=True,
    )
    waiting_review_count = fields.Integer(
        string='Waiting Review',
        compute='_compute_dashboard_counts',
        readonly=True,
    )
    approved_invoice_count = fields.Integer(
        string='Approved Invoices',
        compute='_compute_dashboard_counts',
        readonly=True,
    )
    rejected_invoice_count = fields.Integer(
        string='Rejected Invoices',
        compute='_compute_dashboard_counts',
        readonly=True,
    )
    blocked_documents_count = fields.Integer(
        string='Blocked Documents',
        compute='_compute_dashboard_counts',
        readonly=True,
    )
    unpaid_posted_count = fields.Integer(
        string='Unpaid Posted Documents',
        compute='_compute_dashboard_counts',
        readonly=True,
    )

    @api.depends()
    def _compute_dashboard_counts(self):
        """Compute quick finance control counts."""
        Move = self.env['account.move'].sudo()

        for rec in self:
            rec.draft_invoice_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
            ])

            rec.waiting_review_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
                ('finance_review_state', '=', 'submitted'),
            ])

            rec.approved_invoice_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('finance_review_state', '=', 'approved'),
            ])

            rec.rejected_invoice_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('finance_review_state', '=', 'rejected'),
            ])

            rec.blocked_documents_count = Move.search_count([
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('finance_exception_status', '=', 'blocked'),
            ])

            rec.unpaid_posted_count = Move.search_count([
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial', 'in_payment']),
            ])

    # ---------------------------------------------------------
    # Dashboard open
    # ---------------------------------------------------------

    @api.model
    def action_open_finance_control_dashboard(self):
        """Open or create the single dashboard record."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Finance Control',
            'res_model': 'finance.control.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ---------------------------------------------------------
    # Helper action builder
    # ---------------------------------------------------------

    def _open_moves(self, title, domain, context=None):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'res_model': 'account.move',
            'view_mode': 'kanban,list,form',
            'domain': domain,
            'context': context or {},
            'target': 'current',
        }

    # ---------------------------------------------------------
    # KPI / action buttons
    # ---------------------------------------------------------

    def action_open_draft_invoices(self):
        self.ensure_one()
        return self._open_moves(
            'Draft Invoices',
            [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
            ],
            {'default_move_type': 'out_invoice'},
        )

    def action_open_waiting_review_invoices(self):
        self.ensure_one()
        return self._open_moves(
            'Invoices Waiting Review',
            [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
                ('finance_review_state', '=', 'submitted'),
            ],
            {'default_move_type': 'out_invoice'},
        )

    def action_open_approved_invoices(self):
        self.ensure_one()
        return self._open_moves(
            'Approved Invoices',
            [
                ('move_type', '=', 'out_invoice'),
                ('finance_review_state', '=', 'approved'),
            ],
            {'default_move_type': 'out_invoice'},
        )

    def action_open_rejected_invoices(self):
        self.ensure_one()
        return self._open_moves(
            'Rejected Invoices',
            [
                ('move_type', '=', 'out_invoice'),
                ('finance_review_state', '=', 'rejected'),
            ],
            {'default_move_type': 'out_invoice'},
        )

    def action_open_blocked_documents(self):
        self.ensure_one()
        return self._open_moves(
            'Blocked Documents',
            [
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('finance_exception_status', '=', 'blocked'),
            ],
        )

    def action_open_unpaid_posted_documents(self):
        self.ensure_one()
        return self._open_moves(
            'Unpaid Posted Documents',
            [
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial', 'in_payment']),
            ],
        )