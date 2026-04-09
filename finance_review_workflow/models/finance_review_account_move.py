from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Finance review workflow for customer invoices only
    finance_review_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Review Status', default='draft', tracking=True, copy=False)

    # Submission tracking
    finance_submitted_by = fields.Many2one(
        'res.users',
        string='Submitted By',
        readonly=True,
        copy=False,
    )
    finance_submitted_on = fields.Datetime(
        string='Submitted On',
        readonly=True,
        copy=False,
    )

    # Approval tracking
    finance_approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False,
    )
    finance_approved_on = fields.Datetime(
        string='Approved On',
        readonly=True,
        copy=False,
    )

    # Rejection tracking
    finance_rejected_by = fields.Many2one(
        'res.users',
        string='Rejected By',
        readonly=True,
        copy=False,
    )
    finance_rejected_on = fields.Datetime(
        string='Rejected On',
        readonly=True,
        copy=False,
    )

    # Optional rejection reason
    finance_reject_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
    )

    # -------------------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------------------

    def _is_review_target_document(self):
        """
        Apply this workflow only to customer invoices.
        Vendor bills are excluded to avoid conflict with existing logic.
        """
        self.ensure_one()
        return self.move_type == 'out_invoice'

    def _check_finance_invoice_user_group(self):
        """Allow only invoice user / reviewer groups to submit invoices."""
        if not (
            self.env.user.has_group('finance_review_workflow.group_finance_invoice_user') or
            self.env.user.has_group('finance_review_workflow.group_finance_invoice_reviewer')
        ):
            raise ValidationError(
                _("You do not have permission to submit invoices for finance review.")
            )

    def _check_finance_invoice_reviewer_group(self):
        """Allow only reviewer group to approve, reject, or reset review."""
        if not self.env.user.has_group('finance_review_workflow.group_finance_invoice_reviewer'):
            raise ValidationError(
                _("Only the Finance Invoice Reviewer can perform this action.")
            )

    # -------------------------------------------------------------------------
    # Review actions
    # -------------------------------------------------------------------------

    def action_submit_finance_review(self):
        """Submit draft customer invoice for finance review."""
        self._check_finance_invoice_user_group()

        for move in self:
            if not move._is_review_target_document():
                continue

            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft customer invoices can be submitted for review.")
                )

            if move.finance_review_state != 'draft':
                raise ValidationError(
                    _("Only invoices in Draft review status can be submitted.")
                )

            move.write({
                'finance_review_state': 'submitted',
                'finance_submitted_by': self.env.user.id,
                'finance_submitted_on': fields.Datetime.now(),
                # Clear old rejection reason when resubmitting
                'finance_reject_reason': False,
            })

    def action_approve_finance_review(self):
        """Approve a submitted customer invoice."""
        self._check_finance_invoice_reviewer_group()

        for move in self:
            if not move._is_review_target_document():
                continue

            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft customer invoices can be approved.")
                )

            if move.finance_review_state != 'submitted':
                raise ValidationError(
                    _("Only submitted invoices can be approved.")
                )

            move.write({
                'finance_review_state': 'approved',
                'finance_approved_by': self.env.user.id,
                'finance_approved_on': fields.Datetime.now(),
            })

    def action_reject_finance_review(self):
        """Reject a submitted customer invoice."""
        self._check_finance_invoice_reviewer_group()

        for move in self:
            if not move._is_review_target_document():
                continue

            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft customer invoices can be rejected.")
                )

            if move.finance_review_state != 'submitted':
                raise ValidationError(
                    _("Only submitted invoices can be rejected.")
                )

            move.write({
                'finance_review_state': 'rejected',
                'finance_rejected_by': self.env.user.id,
                'finance_rejected_on': fields.Datetime.now(),
            })

    def action_reset_finance_review_to_draft(self):
        """Return finance review status back to Draft."""
        self._check_finance_invoice_reviewer_group()

        for move in self:
            if not move._is_review_target_document():
                continue

            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft customer invoices can be returned to Draft.")
                )

            move.write({
                'finance_review_state': 'draft',
            })

    # -------------------------------------------------------------------------
    # Posting restriction
    # -------------------------------------------------------------------------

    def action_post(self):
        """
        Prevent posting customer invoices unless they are approved.
        Vendor bills and other move types are ignored.
        """
        for move in self:
            if move._is_review_target_document() and move.finance_review_state != 'approved':
                raise ValidationError(
                    _("You cannot post this invoice until it is approved.")
                )

        return super().action_post()