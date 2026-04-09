from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Review workflow status for invoice / vendor bill approval
    finance_review_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Review Status', default='draft', tracking=True, copy=False)

    # Optional helper fields for tracking who did each action
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

    finance_reject_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
    )

    # -------------------------------------------------------------------------
    # Helper
    # -------------------------------------------------------------------------

    def _is_review_target_document(self):
        """Only apply this workflow to customer invoices and vendor bills."""
        self.ensure_one()
        return self.move_type in ('out_invoice', 'in_invoice')

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    def action_submit_finance_review(self):
        """Move document from Draft review state to Submitted."""
        for move in self:
            if not move._is_review_target_document():
                continue

            # Only draft accounting documents should enter review
            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft invoices or vendor bills can be submitted for review.")
                )

            if move.finance_review_state != 'draft':
                raise ValidationError(
                    _("Only documents in Draft review status can be submitted.")
                )

            move.write({
                'finance_review_state': 'submitted',
                'finance_submitted_by': self.env.user.id,
                'finance_submitted_on': fields.Datetime.now(),
                # Clear old rejection reason if resubmitted
                'finance_reject_reason': False,
            })

    def action_approve_finance_review(self):
        """Approve a submitted document."""
        for move in self:
            if not move._is_review_target_document():
                continue

            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft invoices or vendor bills can be approved.")
                )

            if move.finance_review_state != 'submitted':
                raise ValidationError(
                    _("Only submitted documents can be approved.")
                )

            move.write({
                'finance_review_state': 'approved',
                'finance_approved_by': self.env.user.id,
                'finance_approved_on': fields.Datetime.now(),
            })

    def action_reject_finance_review(self):
        """Reject a submitted document."""
        for move in self:
            if not move._is_review_target_document():
                continue

            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft invoices or vendor bills can be rejected.")
                )

            if move.finance_review_state != 'submitted':
                raise ValidationError(
                    _("Only submitted documents can be rejected.")
                )

            move.write({
                'finance_review_state': 'rejected',
                'finance_rejected_by': self.env.user.id,
                'finance_rejected_on': fields.Datetime.now(),
            })

    def action_reset_finance_review_to_draft(self):
        """Return review status back to Draft."""
        for move in self:
            if not move._is_review_target_document():
                continue

            # Keep this safe and simple: only allow reset while still draft
            if move.state != 'draft':
                raise ValidationError(
                    _("Only draft invoices or vendor bills can be returned to Draft.")
                )

            move.write({
                'finance_review_state': 'draft',
            })

    # -------------------------------------------------------------------------
    # Posting control
    # -------------------------------------------------------------------------

    def action_post(self):
        """
        Block posting for invoices and vendor bills until they are approved.
        Other journal entries are not affected.
        """
        for move in self:
            if move._is_review_target_document() and move.finance_review_state != 'approved':
                raise ValidationError(
                    _("You cannot post this document until it is approved.")
                )

        return super().action_post()