from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # -------------------------------------------------------------------------
    # VENDOR BILL VERIFICATION AND 3-WAY MATCHING SUPPORT
    # -------------------------------------------------------------------------

    # Link the vendor bill to a purchase order.
    # In Odoo, vendor bills are stored in account.move, while the purchasing
    # document is purchase.order. This field gives direct traceability.
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Related Purchase Order',
        tracking=True,
        help='Purchase Order linked to this vendor bill.'
    )

    # Related helper field to show the Purchase Request through the linked PO.
    # This completes the traceability chain:
    # Purchase Request -> Purchase Order -> Vendor Bill
    purchase_request_id = fields.Many2one(
        'purchase.request',
        string='Related Purchase Request',
        related='purchase_order_id.purchase_request_id',
        store=True,
        readonly=True,
        help='Purchase Request linked indirectly through the related Purchase Order.'
    )

    # Tracks the custom verification state of the vendor bill.
    invoice_verification_status = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    ],
        string='Invoice Verification Status',
        default='pending',
        tracking=True,
        help='Custom verification status for the vendor bill before payment processing.'
    )

    # Stores who verified the invoice.
    invoice_verified_by = fields.Many2one(
        'res.users',
        string='Invoice Verified By',
        readonly=True,
        tracking=True,
        help='User who verified this vendor bill.'
    )

    # Stores when the invoice was verified.
    invoice_verified_date = fields.Datetime(
        string='Invoice Verified Date',
        readonly=True,
        tracking=True,
        help='Date and time when this vendor bill was verified.'
    )

    # Stores rejection reason if invoice verification fails.
    invoice_rejection_reason = fields.Text(
        string='Invoice Rejection Reason',
        tracking=True,
        help='Reason entered if the vendor bill is rejected during verification.'
    )

    # Helper field for UI and testing.
    # True when this account.move is a vendor bill.
    is_vendor_bill = fields.Boolean(
        string='Is Vendor Bill',
        compute='_compute_is_vendor_bill',
        help='Technical helper showing whether this record is a vendor bill.'
    )

    @api.depends('move_type')
    def _compute_is_vendor_bill(self):
        for move in self:
            move.is_vendor_bill = move.move_type == 'in_invoice'

    def _check_vendor_bill_link(self):
        """
        Make sure the record is a vendor bill and is linked to a Purchase Order.
        """
        for move in self:
            if move.move_type != 'in_invoice':
                raise ValidationError(
                    'This action is only allowed for vendor bills.'
                )

            if not move.purchase_order_id:
                raise ValidationError(
                    'Please link this vendor bill to a Purchase Order before verifying it.'
                )

    def _check_vendor_matches_po(self):
        """
        Simple consistency check:
        the vendor bill vendor should match the linked Purchase Order vendor.
        """
        for move in self:
            if move.purchase_order_id and move.partner_id != move.purchase_order_id.partner_id:
                raise ValidationError(
                    'The vendor on the bill must match the vendor on the linked Purchase Order.'
                )

    def _check_bill_quantities_against_received_quantities(self):
        """
        Basic custom verification for Phase 5.

        Rule:
        The total billed quantity for products should not exceed the total
        received quantity on the linked Purchase Order.

        Notes:
        - This is a simplified custom verification layer.
        - Odoo 18 already provides native 3-way matching support, so this method
          should be treated as an additional business validation, not a replacement.
        """
        for move in self:
            if not move.purchase_order_id:
                continue

            # Build a map of received quantities from purchase order lines.
            received_qty_by_product = {}
            for po_line in move.purchase_order_id.order_line:
                if po_line.product_id:
                    received_qty_by_product[po_line.product_id.id] = (
                        received_qty_by_product.get(po_line.product_id.id, 0.0) + po_line.qty_received
                    )

            # Compare vendor bill lines against received quantities.
            billed_qty_by_product = {}
            for line in move.invoice_line_ids:
                if line.product_id:
                    billed_qty_by_product[line.product_id.id] = (
                        billed_qty_by_product.get(line.product_id.id, 0.0) + line.quantity
                    )

            for product_id, billed_qty in billed_qty_by_product.items():
                received_qty = received_qty_by_product.get(product_id, 0.0)
                if billed_qty > received_qty:
                    raise ValidationError(
                        'The billed quantity cannot be greater than the received quantity for one or more products.'
                    )

    def action_verify_vendor_bill(self):
        """
        Mark the vendor bill as verified.

        Verification checks:
        - must be a vendor bill
        - must be linked to a Purchase Order
        - vendor must match the PO vendor
        - billed quantities must not exceed received quantities
        """
        for move in self:
            move._check_vendor_bill_link()
            move._check_vendor_matches_po()
            move._check_bill_quantities_against_received_quantities()

            move.invoice_verification_status = 'verified'
            move.invoice_verified_by = self.env.user
            move.invoice_verified_date = fields.Datetime.now()
            move.invoice_rejection_reason = False

    def action_reject_vendor_bill(self):
        """
        Reject the vendor bill during custom verification.
        """
        for move in self:
            move._check_vendor_bill_link()

            if not move.invoice_rejection_reason:
                raise ValidationError(
                    'Please enter the invoice rejection reason before rejecting this vendor bill.'
                )

            move.invoice_verification_status = 'rejected'
            move.invoice_verified_by = False
            move.invoice_verified_date = False