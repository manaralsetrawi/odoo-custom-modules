from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # -------------------------------------------------------------------------
    # PHASE 5 - VENDOR BILL VERIFICATION AND 3-WAY MATCHING SUPPORT
    # -------------------------------------------------------------------------

    # Link the vendor bill to a purchase order.
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Related Purchase Order',
        tracking=True,
        help='Purchase Order linked to this vendor bill.'
    )

    # Related helper field to complete the traceability chain:
    # Purchase Request -> Purchase Order -> Vendor Bill
    purchase_request_id = fields.Many2one(
        'purchase.request',
        string='Related Purchase Request',
        related='purchase_order_id.purchase_request_id',
        store=True,
        readonly=True,
        help='Purchase Request linked indirectly through the related Purchase Order.'
    )

    # Custom verification state before payment processing.
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

    # Stores who verified the vendor bill.
    invoice_verified_by = fields.Many2one(
        'res.users',
        string='Invoice Verified By',
        readonly=True,
        tracking=True,
        help='User who verified this vendor bill.'
    )

    # Stores when the verification happened.
    invoice_verified_date = fields.Datetime(
        string='Invoice Verified Date',
        readonly=True,
        tracking=True,
        help='Date and time when this vendor bill was verified.'
    )

    # Stores rejection reason if the vendor bill is rejected.
    invoice_rejection_reason = fields.Text(
        string='Invoice Rejection Reason',
        tracking=True,
        help='Reason entered if the vendor bill is rejected during verification.'
    )

    # Technical helper: true when the record is a vendor bill.
    is_vendor_bill = fields.Boolean(
        string='Is Vendor Bill',
        compute='_compute_is_vendor_bill',
        help='Technical helper showing whether this record is a vendor bill.'
    )

    # -------------------------------------------------------------------------
    # PHASE 6 - PAYMENT TRACKING HELPER
    # -------------------------------------------------------------------------

    # Business-friendly payment tracking status derived from Odoo's native payment_state.
    payment_tracking_status = fields.Selection([
        ('not_paid', 'Not Paid'),
        ('partial', 'Partially Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('reversed', 'Reversed'),
        ('unknown', 'Unknown'),
    ],
        string='Payment Tracking Status',
        compute='_compute_payment_tracking_status',
        help='Business-friendly payment status derived from the standard Odoo payment state.'
    )

    @api.depends('move_type')
    def _compute_is_vendor_bill(self):
        for move in self:
            move.is_vendor_bill = move.move_type == 'in_invoice'

    @api.depends('payment_state')
    def _compute_payment_tracking_status(self):
        # Map Odoo's native payment_state into a clear business-facing field.
        for move in self:
            if move.payment_state == 'not_paid':
                move.payment_tracking_status = 'not_paid'
            elif move.payment_state == 'partial':
                move.payment_tracking_status = 'partial'
            elif move.payment_state == 'in_payment':
                move.payment_tracking_status = 'in_payment'
            elif move.payment_state == 'paid':
                move.payment_tracking_status = 'paid'
            elif move.payment_state == 'reversed':
                move.payment_tracking_status = 'reversed'
            else:
                move.payment_tracking_status = 'unknown'

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
        The vendor on the bill must match the linked Purchase Order vendor.
        """
        for move in self:
            if move.purchase_order_id and move.partner_id != move.purchase_order_id.partner_id:
                raise ValidationError(
                    'The vendor on the bill must match the vendor on the linked Purchase Order.'
                )

    def _check_bill_quantities_against_received_quantities(self):
        """
        Basic custom verification layer:
        billed quantity must not exceed received quantity.
        """
        for move in self:
            if not move.purchase_order_id:
                continue

            received_qty_by_product = {}
            for po_line in move.purchase_order_id.order_line:
                if po_line.product_id:
                    received_qty_by_product[po_line.product_id.id] = (
                        received_qty_by_product.get(po_line.product_id.id, 0.0) + po_line.qty_received
                    )

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
        Mark the vendor bill as verified after custom invoice checks.
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
        Reject the vendor bill during verification.
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