from odoo import fields, models, _
from odoo.exceptions import ValidationError


class FinanceInvoiceRejectWizard(models.TransientModel):
    _name = 'finance.invoice.reject.wizard'
    _description = 'Finance Invoice Reject Wizard'

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        readonly=True,
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_reject(self):
        """Save reason, then reject the invoice."""
        self.ensure_one()

        if not self.rejection_reason:
            raise ValidationError(_("Please enter the rejection reason."))

        self.move_id.finance_reject_reason = self.rejection_reason
        self.move_id.action_reject_finance_review()