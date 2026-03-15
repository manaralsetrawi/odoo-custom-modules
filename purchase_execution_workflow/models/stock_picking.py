from odoo import fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Marks whether this receipt is part of the GRN / procurement confirmation flow.
    # Useful for future reporting and for identifying receipts that need end-user confirmation.
    is_grn_required = fields.Boolean(
        string='GRN Required',
        default=True,
        tracking=True,
        help='Indicates that this receipt requires GRN-related confirmation.'
    )

    # Shows whether the end user has confirmed the received items.
    # This supports the PM requirement: "End user confirms receipt and compliance."
    end_user_confirmed = fields.Boolean(
        string='End User Confirmed',
        tracking=True,
        help='Checked when the end user confirms the receipt of the items.'
    )

    # Stores which user confirmed the receipt.
    end_user_confirmed_by = fields.Many2one(
        'res.users',
        string='Confirmed By',
        readonly=True,
        tracking=True,
        help='User who confirmed the receipt and compliance of the delivered items.'
    )

    # Stores the confirmation date and time.
    end_user_confirmed_date = fields.Datetime(
        string='Confirmation Date',
        readonly=True,
        tracking=True,
        help='Date and time when the end user confirmed the receipt.'
    )

    # Result of the compliance check after items are received.
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
    ],
        string='Compliance Status',
        default='pending',
        tracking=True,
        help='Result of the compliance check for the received items.'
    )

    # Notes entered by the user during compliance checking.
    compliance_notes = fields.Text(
        string='Compliance Notes',
        help='Notes about item condition, missing quantity, damage, or other receipt remarks.'
    )

    def action_confirm_end_user_receipt(self):
        """
        Confirm the receipt from the end-user side.

        Logic:
        - receipt must already be completed in Odoo (state = done)
        - compliance status must not stay pending
        - once confirmed, store the current user and current date/time
        """
        for picking in self:
            if picking.state != 'done':
                raise ValidationError(
                    'The receipt must be in Done state before end-user confirmation.'
                )

            if picking.compliance_status == 'pending':
                raise ValidationError(
                    'Please set the compliance status before confirming the receipt.'
                )

            picking.end_user_confirmed = True
            picking.end_user_confirmed_by = self.env.user
            picking.end_user_confirmed_date = fields.Datetime.now()