from odoo import fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # -------------------------------------------------------------------------
    # Finance review workflow for customer invoices only
    # -------------------------------------------------------------------------

    finance_review_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Review Status', default='draft', tracking=True, copy=False)

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
    # AP / AR exception control fields
    # -------------------------------------------------------------------------

    finance_exception_status = fields.Selection([
        ('valid', 'Valid'),
        ('has_issue', 'Has Issue'),
        ('blocked', 'Blocked'),
    ], string='Exception Status', default='valid', copy=False, tracking=True)

    finance_exception_summary = fields.Text(
        string='Exception Summary',
        readonly=True,
        copy=False,
    )

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
    # Vendor bill completeness fields
    # -------------------------------------------------------------------------

    finance_readiness_status = fields.Selection([
        ('incomplete', 'Needs Completion'),
        ('ready', 'Ready for Review'),
    ], string='Completeness Status', default='incomplete', copy=False, tracking=True)

    finance_readiness_summary = fields.Text(
        string='Check Result',
        readonly=True,
        copy=False,
    )

    finance_missing_bill_reference = fields.Boolean(
        string='Bill Reference Missing',
        readonly=True,
        copy=False,
    )

    finance_missing_bill_tax = fields.Boolean(
        string='Tax Missing',
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
        """Apply finance review workflow only to customer invoices."""
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
        """Apply exception checks only to customer invoices and vendor bills."""
        self.ensure_one()
        return self.move_type in ('out_invoice', 'in_invoice')

    def _is_vendor_bill_readiness_target(self):
        """Apply bill completeness check only to vendor bills."""
        self.ensure_one()
        return self.move_type == 'in_invoice'

    # -------------------------------------------------------------------------
    # Core checks
    # -------------------------------------------------------------------------

    def _run_finance_exception_checks(self):
        """
        Run AP/AR exception checks and update stored result fields.
        """
        for move in self:
            if not move._is_exception_target_document():
                continue

            issues = []
            status = 'valid'

            vals = {
                'finance_missing_due_date': False,
                'finance_missing_tax': False,
                'finance_missing_vendor_ref': False,
                'finance_duplicate_vendor_ref': False,
                'finance_invalid_date_sequence': False,
                'finance_exception_summary': False,
                'finance_exception_status': 'valid',
            }

            # Missing due date
            if not move.invoice_date_due:
                vals['finance_missing_due_date'] = True
                issues.append("Missing due date.")
                status = 'blocked'

            # Missing tax
            real_lines = move.invoice_line_ids.filtered(lambda l: not l.display_type)
            has_tax = any(line.tax_ids for line in real_lines)

            if real_lines and not has_tax:
                vals['finance_missing_tax'] = True
                issues.append("Missing tax on document lines.")
                if status != 'blocked':
                    status = 'has_issue'

            # Missing vendor reference (bills only)
            if move.move_type == 'in_invoice' and not move.ref:
                vals['finance_missing_vendor_ref'] = True
                issues.append("Missing vendor reference.")
                status = 'blocked'

            # Duplicate vendor bill reference (bills only)
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

            # Invalid date sequence
            if move.invoice_date and move.invoice_date_due:
                if move.invoice_date > move.invoice_date_due:
                    vals['finance_invalid_date_sequence'] = True
                    issues.append("Invoice date is later than due date.")
                    status = 'blocked'

            vals['finance_exception_status'] = status
            vals['finance_exception_summary'] = "\n".join(issues) if issues else "No exception found."

            move.write(vals)

    def _run_vendor_bill_readiness_check(self):
        """
        Quick completeness check for vendor bills.
        Required only:
        - vendor bill reference
        - tax
        """
        for move in self:
            if not move._is_vendor_bill_readiness_target():
                continue

            issues = []
            status = 'ready'

            vals = {
                'finance_missing_bill_reference': False,
                'finance_missing_bill_tax': False,
                'finance_missing_payment_term': False,
                'finance_missing_attachment': False,
                'finance_readiness_summary': False,
                'finance_readiness_status': 'ready',
            }

            # Bill reference
            if not move.ref:
                vals['finance_missing_bill_reference'] = True
                issues.append("Vendor bill reference is missing.")
                status = 'incomplete'

            # Tax
            real_lines = move.invoice_line_ids.filtered(lambda l: not l.display_type)
            has_tax = any(line.tax_ids for line in real_lines)

            if real_lines and not has_tax:
                vals['finance_missing_bill_tax'] = True
                issues.append("Tax is missing on vendor bill lines.")
                status = 'incomplete'

            # No longer required for completeness
            vals['finance_missing_payment_term'] = False
            vals['finance_missing_attachment'] = False

            vals['finance_readiness_status'] = status
            vals['finance_readiness_summary'] = (
                "\n".join(issues)
                if issues else
                "Vendor bill includes the main required information for review."
            )

            move.write(vals)

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

    def action_open_finance_reject_wizard(self):
        """Open popup wizard to collect rejection reason."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Invoice',
            'res_model': 'finance.invoice.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
            },
        }

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

            if not move.finance_reject_reason:
                raise ValidationError(
                    _("Please enter the rejection reason before rejecting the invoice.")
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
    # Popup actions
    # -------------------------------------------------------------------------

    def action_check_finance_exceptions(self):
        """
        Run exception checks, store results, then open popup with result.
        """
        self.ensure_one()
        self._run_finance_exception_checks()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Exception Check Result',
            'res_model': 'finance.exception.result.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_finance_exception_status': self.finance_exception_status,
                'default_finance_exception_summary': self.finance_exception_summary,
                'default_finance_missing_due_date': self.finance_missing_due_date,
                'default_finance_missing_tax': self.finance_missing_tax,
                'default_finance_invalid_date_sequence': self.finance_invalid_date_sequence,
                'default_finance_missing_vendor_ref': self.finance_missing_vendor_ref,
                'default_finance_duplicate_vendor_ref': self.finance_duplicate_vendor_ref,
            },
        }

    def action_check_vendor_bill_readiness(self):
        """
        Run bill completeness check, then open popup with result.
        """
        self.ensure_one()
        self._run_vendor_bill_readiness_check()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Bill Completeness Check',
            'res_model': 'finance.bill.completeness.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_id': self.id,
                'default_finance_readiness_status': self.finance_readiness_status,
                'default_finance_readiness_summary': self.finance_readiness_summary,
                'default_finance_missing_bill_reference': self.finance_missing_bill_reference,
                'default_finance_missing_bill_tax': self.finance_missing_bill_tax,
            },
        }

    def action_generate_finance_summary_report(self):
        """Generate the Finance Review Summary Report."""
        self.ensure_one()
        return self.env.ref(
            'finance_review_workflow.action_finance_review_summary_report'
        ).report_action(self)

    # -------------------------------------------------------------------------
    # Posting restriction
    # -------------------------------------------------------------------------

    def action_post(self):
        """
        1) Block customer invoice posting unless finance review is approved.
        2) Block invoice/bill posting if AP/AR exception status is blocked.
        """
        for move in self:
            if move._is_review_target_document() and move.finance_review_state != 'approved':
                raise ValidationError(
                    _("You cannot post this invoice until it is approved.")
                )

            if move._is_exception_target_document():
                move._run_finance_exception_checks()

                if move.finance_exception_status == 'blocked':
                    raise ValidationError(
                        _("You cannot post this document because it has blocked AP/AR exceptions. Please fix them first.")
                    )

        return super().action_post()