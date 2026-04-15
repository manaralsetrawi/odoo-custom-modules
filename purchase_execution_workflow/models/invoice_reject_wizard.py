from odoo import fields, models
from odoo.exceptions import ValidationError


class InvoiceRejectWizard(models.TransientModel):
    _name = 'invoice.reject.wizard'
    _description = 'Invoice Reject Wizard'

    account_move_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        required=True,
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_rejection(self):
        self.ensure_one()

        if not self.rejection_reason:
            raise ValidationError('Please enter the rejection reason.')

        self.account_move_id.write({
            'invoice_rejection_reason': self.rejection_reason,
        })

        self.account_move_id.action_reject_vendor_bill()