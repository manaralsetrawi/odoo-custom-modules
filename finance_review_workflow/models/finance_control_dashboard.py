"""Finance control dashboard model.

This model exists to show a small set of KPI counters and provide buttons that
open the corresponding `account.move` lists.
"""

from odoo import api, fields, models


class FinanceControlDashboard(models.Model):
    """Dashboard record used by a form view.

    Quick Odoo reminder:
    - Computed fields: `compute=...` fills values automatically.
    - Action methods: `action_*` returns an `ir.actions.*` dict to open a view.
    """

    _name = 'finance.control.dashboard'
    _description = 'Finance Control Dashboard'

    # Single title field shown in the dashboard header.
    name = fields.Char(default='Finance Control', readonly=True)

    # KPI counters (computed, read-only). These are displayed as tiles.
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
        """Compute all KPI counters.

        Uses `search_count` for performance.
        """
        # `sudo()` makes the KPI numbers stable regardless of the user's access
        # rights (common for dashboards). If you want per-user numbers, remove it.
        Move = self.env['account.move'].sudo()

        for rec in self:
            # Standard Odoo invoice model:
            # - move_type = out_invoice -> customer invoices
            # - state = draft/posted -> document state
            rec.draft_invoice_count = Move.search_count([
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'draft'),
            ])

            # Custom workflow fields (added by this module):
            # - finance_review_state: tracks finance review status (submitted/approved/rejected)
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
                # finance_exception_status is a custom flag used to block processing.
                ('finance_exception_status', '=', 'blocked'),
            ])

            # Unpaid posted documents (used for finance follow-up).
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
        """Open (and create if missing) the single dashboard record."""
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
        """Helper: build an action that opens `account.move` with a domain."""
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
        # Action method (button): open draft customer invoices.
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
        # Action method (button): open invoices with finance review submitted.
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
        # Action method (button): open finance-approved invoices.
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
        # Action method (button): open finance-rejected invoices.
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
        # Action method (button): open blocked customer/vendor documents.
        self.ensure_one()
        return self._open_moves(
            'Blocked Documents',
            [
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('finance_exception_status', '=', 'blocked'),
            ],
        )

    def action_open_unpaid_posted_documents(self):
        # Action method (button): open posted documents that still need payment follow-up.
        self.ensure_one()
        return self._open_moves(
            'Unpaid Posted Documents',
            [
                ('move_type', 'in', ['out_invoice', 'in_invoice']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial', 'in_payment']),
            ],
        )