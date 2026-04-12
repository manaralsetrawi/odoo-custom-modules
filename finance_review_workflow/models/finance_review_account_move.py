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
# AP / AR exception control fields
# -------------------------------------------------------------------------

    # Main exception result shown to the user
    finance_exception_status = fields.Selection([
        ('valid', 'Valid'),
        ('has_issue', 'Has Issue'),
        ('blocked', 'Blocked'),
    ], string='Exception Status', default='valid', copy=False, tracking=True)

    # Human-readable summary of detected issues
    finance_exception_summary = fields.Text(
        string='Exception Summary',
        readonly=True,
        copy=False,
)

    # Helper flags for each validation rule
    finance_missing_due_date = fields.Boolean(
        string='Missing Due Date',
        readonly=True,
        copy=False,
)

    finance_missing_tax = fields.Boolean(
        string='Missing Tax',
        readonly=True,
        copy=False,
)

    finance_missing_vendor_ref = fields.Boolean(
        string='Missing Vendor Reference',
        readonly=True,
        copy=False,
)

    finance_duplicate_vendor_ref = fields.Boolean(
        string='Duplicate Vendor Bill Reference',
        readonly=True,
        copy=False,
)

    finance_invalid_date_sequence = fields.Boolean(
        string='Invoice Date Later Than Due Date',
        readonly=True,
        copy=False,
)
    
# -------------------------------------------------------------------------
# Vendor bill readiness check fields
# -------------------------------------------------------------------------

    # Final readiness result for vendor bills
    finance_readiness_status = fields.Selection([
        ('incomplete', 'Incomplete'),
        ('ready', 'Ready for Review'),
    ], string='Readiness Status', default='incomplete', copy=False, tracking=True)

    # User-friendly summary of missing required information
    finance_readiness_summary = fields.Text(
        string='Readiness Summary',
        readonly=True,
        copy=False,
)

    # Helper flags for each readiness rule
    finance_missing_bill_reference = fields.Boolean(
        string='Missing Vendor Bill Reference',
        readonly=True,
        copy=False,
)

    finance_missing_bill_tax = fields.Boolean(
        string='Missing Tax',
        readonly=True,
        copy=False,
)

    finance_missing_payment_term = fields.Boolean(
        string='Missing Payment Term',
        readonly=True,
        copy=False,
)

    finance_missing_attachment = fields.Boolean(
        string='Missing Attachment',
        readonly=True,
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
        
    def _is_exception_target_document(self):
        """
        Apply exception checks only to customer invoices and vendor bills.
        This keeps the logic away from journal entries and other move types.
        """
        self.ensure_one()
        return self.move_type in ('out_invoice', 'in_invoice')
    
    def _run_finance_exception_checks(self):
        """
        Run AP/AR exception checks and update the exception fields.
        This method is intentionally independent from procurement verification
        logic to avoid conflicts with the existing purchase workflow.
        """
        for move in self:
        # Skip non-target documents safely
            if not move._is_exception_target_document():
                continue

        issues = []
        status = 'valid'

        # Reset all helper flags before checking again
        vals = {
            'finance_missing_due_date': False,
            'finance_missing_tax': False,
            'finance_missing_vendor_ref': False,
            'finance_duplicate_vendor_ref': False,
            'finance_invalid_date_sequence': False,
            'finance_exception_summary': False,
            'finance_exception_status': 'valid',
        }

        # -------------------------------------------------------------
        # 1) Missing due date
        # -------------------------------------------------------------
        if not move.invoice_date_due:
            vals['finance_missing_due_date'] = True
            issues.append("Missing due date.")
            status = 'blocked'

        # -------------------------------------------------------------
        # 2) Missing tax on invoice/bill lines
        # -------------------------------------------------------------
        real_lines = move.invoice_line_ids.filtered(lambda l: not l.display_type)

        has_tax = any(line.tax_ids for line in real_lines)

        if real_lines and not has_tax:
            vals['finance_missing_tax'] = True
            issues.append("Missing tax on document lines.")
            if status != 'blocked':
                status = 'has_issue'

        # -------------------------------------------------------------
        # 3) Missing vendor reference (vendor bills only)
        # -------------------------------------------------------------
        if move.move_type == 'in_invoice' and not move.ref:
            vals['finance_missing_vendor_ref'] = True
            issues.append("Missing vendor reference.")
            status = 'blocked'

        # -------------------------------------------------------------
        # 4) Duplicate vendor bill reference (vendor bills only)
        # -------------------------------------------------------------
        if move.move_type == 'in_invoice' and move.ref and move.partner_id:
            duplicate_bill = self.search([
                ('id', '!=', move.id),
                ('move_type', '=', 'in_invoice'),
                ('partner_id', '=', move.partner_id.id),
                ('ref', '=', move.ref),
                ('state', '!=', 'cancel'),
            ], limit=1)

            if duplicate_bill:
                vals['finance_duplicate_vendor_ref'] = True
                issues.append("Duplicate vendor bill reference found.")
                status = 'blocked'

        # -------------------------------------------------------------
        # 5) Invoice date later than due date
        # -------------------------------------------------------------
        if move.invoice_date and move.invoice_date_due:
            if move.invoice_date > move.invoice_date_due:
                vals['finance_invalid_date_sequence'] = True
                issues.append("Invoice date is later than due date.")
                status = 'blocked'

        # Final result
        vals['finance_exception_status'] = status
        vals['finance_exception_summary'] = "\n".join(issues) if issues else "No exception found."

        move.write(vals)
    # Added a helper method to determine if the document is a vendor bill for readiness checks    
    def _is_vendor_bill_readiness_target(self):
        """
        Apply readiness check only to vendor bills.
        This keeps the feature separate from customer invoice review logic.
        """
        self.ensure_one()
        return self.move_type == 'in_invoice'
    

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

    def action_check_finance_exceptions(self):
        """
        Manual button to run AP/AR exception checks.
        Useful for user review before posting.
        """
        self._run_finance_exception_checks()

    def _run_vendor_bill_readiness_check(self):
        """
        Check whether the vendor bill is complete enough for review.

        This logic is separate from the existing procurement invoice verification
        workflow, so it does not replace or modify that logic.
        """
        Attachment = self.env['ir.attachment']

        for move in self:
            # Ignore non-vendor-bill records safely
            if not move._is_vendor_bill_readiness_target():
                continue

        issues = []
        status = 'ready'

        # Reset readiness fields before rechecking
        vals = {
            'finance_missing_bill_reference': False,
            'finance_missing_bill_tax': False,
            'finance_missing_payment_term': False,
            'finance_missing_attachment': False,
            'finance_readiness_summary': False,
            'finance_readiness_status': 'ready',
        }

        # -------------------------------------------------------------
        # 1) Vendor bill reference
        # -------------------------------------------------------------
        if not move.ref:
            vals['finance_missing_bill_reference'] = True
            issues.append("Vendor bill reference is missing.")
            status = 'incomplete'

        # -------------------------------------------------------------
        # 2) Tax on real vendor bill lines
        # -------------------------------------------------------------
        real_lines = move.invoice_line_ids.filtered(lambda l: not l.display_type)
        has_tax = any(line.tax_ids for line in real_lines)

        if real_lines and not has_tax:
            vals['finance_missing_bill_tax'] = True
            issues.append("Tax is missing on vendor bill lines.")
            status = 'incomplete'

        # -------------------------------------------------------------
        # 3) Payment term
        # -------------------------------------------------------------
        if not move.invoice_payment_term_id:
            vals['finance_missing_payment_term'] = True
            issues.append("Payment term is missing.")
            status = 'incomplete'

        # -------------------------------------------------------------
        # 4) Attachment
        # -------------------------------------------------------------
        attachment_count = Attachment.search_count([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', move.id),
        ])

        if attachment_count == 0:
            vals['finance_missing_attachment'] = True
            issues.append("Required attachment is missing.")
            status = 'incomplete'

        # Final readiness result
        vals['finance_readiness_status'] = status
        vals['finance_readiness_summary'] = (
            "\n".join(issues) if issues else "Vendor bill is ready for review."
        )

        move.write(vals)

    # -------------------------------------------------------------------------
    # Posting restriction
    # -------------------------------------------------------------------------

    def action_post(self):
        """
        1) Block customer invoice posting unless finance review is approved.
        2) Block invoice/bill posting if AP/AR exception status is blocked.

        This keeps the finance review workflow and exception control separate.
        """
        for move in self:
        # -------------------------------------------------------------
        # Feature 1: invoice review workflow
        # Only for customer invoices
        # -------------------------------------------------------------
            if move._is_review_target_document() and move.finance_review_state != 'approved':
                raise ValidationError(
                _("You cannot post this invoice until it is approved.")
            )

        # -------------------------------------------------------------
        # Feature 2: AP/AR exception control
        # Applies to customer invoices and vendor bills
        # -------------------------------------------------------------
        if move._is_exception_target_document():
            # Re-run checks before posting to ensure latest values
            move._run_finance_exception_checks()

            if move.finance_exception_status == 'blocked':
                raise ValidationError(
                    _("You cannot post this document because it has blocked AP/AR exceptions. Please fix them first.")
                )

        return super().action_post()
    
    def action_check_vendor_bill_readiness(self):
        """
        Manual button to check whether the vendor bill is complete enough
        for review.
        """
        self._run_vendor_bill_readiness_check()