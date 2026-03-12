from odoo import fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # Marks whether this receipt should be treated as part of the GRN / procurement receipt flow.
    # This is useful for custom purchasing process and future reporting.
    is_grn_required = fields.Boolean(
        string='GRN Required',
        default=True,
        tracking=True,
        help='Indicates that this incoming receipt requires GRN-related confirmation.'
    )

    # Indicates whether the end user has confirmed the received items.
    # This supports the requirement: "End user confirms receipt and compliance."
    end_user_confirmed = fields.Boolean(
        string='End User Confirmed',
        tracking=True,
        help='Checked when the end user confirms the receipt of the items.'
    )

    # Stores the user who confirmed the receipt.
    end_user_confirmed_by = fields.Many2one(
        'res.users',
        string='Confirmed By',
        readonly=True,
        tracking=True,
        help='User who confirmed the receipt and compliance of the delivered items.'
    )

    # Stores the date and time of end user confirmation.
    end_user_confirmed_date = fields.Datetime(
        string='Confirmation Date',
        readonly=True,
        tracking=True,
        help='Date and time when the end user confirmed the receipt.'
    )

    # Compliance result for the received items.
    # Pending = not checked yet
    # Compliant = items received correctly
    # Non-compliant = issues found during checking
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
    ],
        string='Compliance Status',
        default='pending',
        tracking=True,
        help='Result of the end user compliance check for this receipt.'
    )

    # Notes entered during receipt checking.
    # Example: missing items, damaged goods, accepted with observation, etc.
    compliance_notes = fields.Text(
        string='Compliance Notes',
        help='Notes related to the receipt quality, quantity, or compliance check.'
    )

    def action_confirm_end_user_receipt(self):
        """
        Mark the receipt as confirmed by the current user.

        Main purpose:
        - support end-user confirmation step in the custom procurement workflow
        - store who confirmed and when
        - enforce that compliance status is not left as pending
        """
        for picking in self:
            # Optional safety check:
            # prevent confirmation if compliance result has not been chosen yet.
            if picking.compliance_status == 'pending':
                raise ValidationError(
                    'Please set the compliance status before confirming the receipt.'
                )

            # Mark receipt as confirmed by the current logged-in user.
            picking.end_user_confirmed = True
            picking.end_user_confirmed_by = self.env.user
            picking.end_user_confirmed_date = fields.Datetime.now()