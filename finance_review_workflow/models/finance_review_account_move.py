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
    # Helper
    # -------------------------------------------------------------------------

    def _is_review_target_document(self):
        """
        Apply this workflow only to customer invoices.
        Vendor bills are excluded to avoid conflict with the
        existing vendor bill verification workflow.
        """
        self.ensure_one()
        return self.move_type == 'out_invoice'

    # -------------------------------------------------------------------------
    # Review actions
    # -------------------------------------------------------------------------

    def action_submit_finance_review(self):
        """Submit draft customer invoice for finance review."""
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
                # Clear old reason when invoice is re-submitted
                'finance_reject_reason': False,
            })

    def action_approve_finance_review(self):
        """Approve a submitted customer invoice."""
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
        """Return finance review status to Draft."""
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
        Other accounting entries and vendor bills are not affected.
        """
        for move in self:
            if move._is_review_target_document() and move.finance_review_state != 'approved':
                raise ValidationError(
                    _("You cannot post this invoice until it is approved.")
                )

        return super().action_post()