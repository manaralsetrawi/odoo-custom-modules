from odoo import fields, models
from odoo.exceptions import ValidationError


class FinancialRejectWizard(models.TransientModel):
    _name = 'financial.reject.wizard'
    _description = 'Financial Reject Wizard'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='RFQ / Purchase Order',
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

        self.purchase_order_id.write({
            'financial_rejection_reason': self.rejection_reason,
        })

        self.purchase_order_id.action_financial_reject()