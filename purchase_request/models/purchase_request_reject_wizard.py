from odoo import models, fields
from odoo.exceptions import UserError


class PurchaseRequestRejectWizard(models.TransientModel):
    _name = 'purchase.request.reject.wizard'
    _description = 'Purchase Request Reject Wizard'

    purchase_request_id = fields.Many2one(
        'purchase.request',
        string='Purchase Request',
        required=True,
        readonly=True,
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        required=True,
    )

    def action_confirm_reject(self):
        self.ensure_one()

        request = self.purchase_request_id

        if not request.is_current_user_can_reject:
            raise UserError("You are not allowed to reject this request at the current stage.")

        if not self.rejection_reason:
            raise UserError("Please enter the rejection reason.")

        request.write({
            'state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })

        request.message_post(
            body=f"Purchase Request rejected. Reason: {self.rejection_reason}"
        )

        return {'type': 'ir.actions.act_window_close'}