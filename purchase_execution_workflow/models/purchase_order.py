from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # -------------------------------------------------------------------------
    #  LINK PURCHASE REQUEST TO RFQ / PO
    # -------------------------------------------------------------------------

    # Link each RFQ / PO to the related Purchase Request.
    # This connects Person A's module with the procurement execution flow.
    purchase_request_id = fields.Many2one(
        'purchase.request',
        string='Purchase Request',
        tracking=True,
        help='Related purchase request for this quotation or purchase order.'
    )

    # Count how many RFQs / POs are linked to the same Purchase Request.
    # This supports the custom rule:
    # one PR -> multiple quotations
    quotation_count_for_request = fields.Integer(
        string='Quotation Count',
        compute='_compute_quotation_count_for_request',
        help='Number of quotations linked to the same purchase request.'
    )

    # Helper field to know whether the RFQ / PO is linked to a Purchase Request.
    has_purchase_request = fields.Boolean(
        string='Has Purchase Request',
        compute='_compute_has_purchase_request',
        help='Technical helper showing whether this RFQ is linked to a purchase request.'
    )

    # Helper field used for the quotation rule:
    # minimum 3 quotations if total amount > BD 1000
    is_above_quotation_threshold = fields.Boolean(
        string='Above BD 1000',
        compute='_compute_is_above_quotation_threshold',
        help='True when the RFQ total amount is greater than BD 1000.'
    )

    # Helper field showing whether this PR already has multiple quotations.
    is_multi_quotation_case = fields.Boolean(
        string='Multi Quotation Case',
        compute='_compute_is_multi_quotation_case',
        help='True when more than one quotation exists for the same purchase request.'
    )

    @api.depends('purchase_request_id')
    def _compute_has_purchase_request(self):
        # Mark True when the RFQ / PO is linked to a Purchase Request.
        for order in self:
            order.has_purchase_request = bool(order.purchase_request_id)

    @api.depends('purchase_request_id')
    def _compute_quotation_count_for_request(self):
        # Count all RFQs / POs linked to the same Purchase Request.
        for order in self:
            if order.purchase_request_id:
                order.quotation_count_for_request = self.search_count([
                    ('purchase_request_id', '=', order.purchase_request_id.id)
                ])
            else:
                order.quotation_count_for_request = 0

    @api.depends('amount_total')
    def _compute_is_above_quotation_threshold(self):
        # Mark True when total amount is above BD 1000.
        for order in self:
            order.is_above_quotation_threshold = order.amount_total > 1000

    @api.depends('quotation_count_for_request')
    def _compute_is_multi_quotation_case(self):
        # Mark True when more than one RFQ exists for the same Purchase Request.
        for order in self:
            order.is_multi_quotation_case = order.quotation_count_for_request > 1

    # -------------------------------------------------------------------------
    #  QUOTATION EVALUATION AND VENDOR RECOMMENDATION
    # -------------------------------------------------------------------------

    # Technical evaluation result entered by procurement.
    technical_evaluation = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ],
        string='Technical Evaluation',
        default='pending',
        tracking=True,
        help='Technical evaluation result for this supplier quotation.'
    )

    # Commercial evaluation result entered by procurement.
    commercial_evaluation = fields.Selection([
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ],
        string='Commercial Evaluation',
        default='pending',
        tracking=True,
        help='Commercial evaluation result for this supplier quotation.'
    )

    # Notes about the quotation review.
    evaluation_notes = fields.Text(
        string='Evaluation Notes',
        help='Notes related to technical and commercial evaluation of this quotation.'
    )

    # Mark this quotation as the recommended one for the related Purchase Request.
    is_recommended_vendor = fields.Boolean(
        string='Recommended Vendor',
        tracking=True,
        help='Checked when this quotation is selected as the recommended vendor.'
    )

    # Reason for recommending this quotation.
    recommendation_reason = fields.Text(
        string='Recommendation Reason',
        help='Reason for selecting this supplier quotation.'
    )

    # Helper field to show whether the quotation count rule is satisfied.
    meets_minimum_quotation_rule = fields.Boolean(
        string='Meets Minimum Quotation Rule',
        compute='_compute_meets_minimum_quotation_rule',
        help='True when the required number of quotations is available for this Purchase Request.'
    )

    @api.depends('purchase_request_id', 'quotation_count_for_request', 'is_above_quotation_threshold')
    def _compute_meets_minimum_quotation_rule(self):
        """
        Rule:
        - If amount <= 1000 -> no minimum 3 quotation requirement
        - If amount > 1000 -> at least 3 quotations must exist for the same PR
        """
        for order in self:
            if not order.purchase_request_id:
                order.meets_minimum_quotation_rule = False
            elif not order.is_above_quotation_threshold:
                order.meets_minimum_quotation_rule = True
            else:
                order.meets_minimum_quotation_rule = order.quotation_count_for_request >= 3

    def action_mark_as_recommended(self):
        """
        Mark this quotation as the recommended one.

        Logic:
        - quotation must be linked to a Purchase Request
        - technical evaluation must be accepted
        - commercial evaluation must be accepted
        - only one quotation should stay recommended for the same PR
        """
        for order in self:
            if not order.purchase_request_id:
                raise ValidationError(
                    'Please link this quotation to a Purchase Request before marking it as recommended.'
                )

            if order.technical_evaluation != 'accepted':
                raise ValidationError(
                    'Technical evaluation must be accepted before recommending this quotation.'
                )

            if order.commercial_evaluation != 'accepted':
                raise ValidationError(
                    'Commercial evaluation must be accepted before recommending this quotation.'
                )

            # Remove recommendation from other quotations linked to the same PR.
            other_orders = self.search([
                ('purchase_request_id', '=', order.purchase_request_id.id),
                ('id', '!=', order.id)
            ])
            other_orders.write({'is_recommended_vendor': False})

            # Mark current quotation as recommended.
            order.is_recommended_vendor = True

    def _check_minimum_quotation_requirement(self):
        """
        PM rule:
        - minimum 3 quotations for purchases above BD 1000
        """
        for order in self:
            if not order.purchase_request_id:
                raise ValidationError(
                    'Please link this quotation to a Purchase Request before confirming it.'
                )

            if order.is_above_quotation_threshold and order.quotation_count_for_request < 3:
                raise ValidationError(
                    'At least 3 quotations are required for purchase requests above BD 1000.'
                )

    def _check_evaluation_completion(self):
        """
        Make sure procurement review is completed before confirming the PO.
        """
        for order in self:
            if order.technical_evaluation == 'pending':
                raise ValidationError(
                    'Please complete the technical evaluation before confirming this quotation.'
                )

            if order.commercial_evaluation == 'pending':
                raise ValidationError(
                    'Please complete the commercial evaluation before confirming this quotation.'
                )

    def _check_recommended_vendor_selected(self):
        """
        Ensure that one quotation is selected as recommended before PO confirmation.
        """
        for order in self:
            if not order.is_recommended_vendor:
                raise ValidationError(
                    'Only the recommended quotation can be confirmed as a Purchase Order.'
                )

    def button_confirm(self):
        """
        Override standard PO confirmation.

        Before confirming, enforce:
        1) quotation linked to a Purchase Request
        2) minimum quotation rule is satisfied
        3) technical evaluation completed
        4) commercial evaluation completed
        5) quotation is marked as the recommended vendor

        """
        self._check_minimum_quotation_requirement()
        self._check_evaluation_completion()
        self._check_recommended_vendor_selected()
        return super().button_confirm()
    
    from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # -------------------------------------------------------------------------
    # FINANCIAL APPROVAL ROUTING
    # -------------------------------------------------------------------------

    # Current financial approval state for this quotation / purchase order.
    financial_approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('to_approve', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ],
        string='Financial Approval Status',
        default='not_required',
        tracking=True,
        help='Financial approval status based on the total quotation amount.'
    )

    # Stores which approval level is required based on the total amount.
    required_financial_approval_level = fields.Selection([
        ('finance_director', 'Director of Finance'),
        ('deputy_ceo', 'Deputy CEO'),
        ('ceo', 'CEO'),
    ],
        string='Required Financial Approval',
        compute='_compute_required_financial_approval_level',
        store=True,
        tracking=True,
        help='Required financial approver level based on the total amount.'
    )

    # Stores the user who approved the quotation financially.
    financial_approved_by = fields.Many2one(
        'res.users',
        string='Financially Approved By',
        readonly=True,
        tracking=True,
        help='User who approved this quotation in the financial approval step.'
    )

    # Stores the approval date/time.
    financial_approved_date = fields.Datetime(
        string='Financial Approval Date',
        readonly=True,
        tracking=True,
        help='Date and time when financial approval was completed.'
    )

    # Stores rejection reason if the quotation is rejected during financial approval.
    financial_rejection_reason = fields.Text(
        string='Financial Rejection Reason',
        tracking=True,
        help='Reason entered when the quotation is rejected in the financial approval step.'
    )

    @api.depends('amount_total')
    def _compute_required_financial_approval_level(self):
        """
        Determine the required approval level from the PM rules:

        - up to 5,000 -> Director of Finance
        - 5,001 to 9,999 -> Deputy CEO
        - 10,000 and above -> CEO
        """
        for order in self:
            if order.amount_total <= 5000:
                order.required_financial_approval_level = 'finance_director'
            elif order.amount_total <= 9999:
                order.required_financial_approval_level = 'deputy_ceo'
            else:
                order.required_financial_approval_level = 'ceo'

    def action_submit_financial_approval(self):
        """
        Send the quotation to the financial approval stage.

        This should only happen after:
        - PR link exists
        - quotation rule is satisfied
        - evaluations are completed
        - quotation is marked as recommended
        """
        for order in self:
            # Reuse earlier phase checks before financial routing starts.
            order._check_minimum_quotation_requirement()
            order._check_evaluation_completion()
            order._check_recommended_vendor_selected()

            order.financial_approval_state = 'to_approve'
            order.financial_rejection_reason = False

    def action_financial_approve(self):
        """
        Mark the quotation as financially approved.
        """
        for order in self:
            if order.financial_approval_state != 'to_approve':
                raise ValidationError(
                    'Only quotations waiting for financial approval can be approved.'
                )

            order.financial_approval_state = 'approved'
            order.financial_approved_by = self.env.user
            order.financial_approved_date = fields.Datetime.now()
            order.financial_rejection_reason = False

    def action_financial_reject(self):
        """
        Mark the quotation as financially rejected.

        For now, this method requires the rejection reason field
        to be filled before clicking the reject button.
        """
        for order in self:
            if order.financial_approval_state != 'to_approve':
                raise ValidationError(
                    'Only quotations waiting for financial approval can be rejected.'
                )

            if not order.financial_rejection_reason:
                raise ValidationError(
                    'Please enter the financial rejection reason before rejecting this quotation.'
                )

            order.financial_approval_state = 'rejected'
            order.financial_approved_by = False
            order.financial_approved_date = False

    def _check_financial_approval_completed(self):
        """
        Ensure financial approval is completed before confirming the PO.
        """
        for order in self:
            if order.financial_approval_state != 'approved':
                raise ValidationError(
                    'Financial approval must be completed before confirming this Purchase Order.'
                )

    def button_confirm(self):
        """
        Final confirmation gate.

        Enforce:
        - Phase 2 checks
        - Phase 3 financial approval must be approved
        """
        self._check_minimum_quotation_requirement()
        self._check_evaluation_completion()
        self._check_recommended_vendor_selected()
        self._check_financial_approval_completed()
        return super().button_confirm()
    
    from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # -------------------------------------------------------------------------
    # PURCHASE ORDER ISSUANCE AND VENDOR ACKNOWLEDGMENT
    # -------------------------------------------------------------------------

    # Marks whether vendor acknowledgment is required for this PO.
    # Vendor acknowledgment is required after issuing the PO.
    vendor_ack_required = fields.Boolean(
        string='Vendor Acknowledgment Required',
        default=True,
        tracking=True,
        help='Indicates whether vendor acknowledgment is required for this purchase order.'
    )

    # Shows whether the vendor has acknowledged the PO.
    vendor_ack_received = fields.Boolean(
        string='Vendor Acknowledged',
        tracking=True,
        help='Checked when the vendor acknowledges the purchase order.'
    )

    # Stores the user who recorded the vendor acknowledgment.
    vendor_ack_recorded_by = fields.Many2one(
        'res.users',
        string='Acknowledgment Recorded By',
        readonly=True,
        tracking=True,
        help='User who recorded the vendor acknowledgment.'
    )

    # Stores the date/time when acknowledgment was recorded.
    vendor_ack_date = fields.Datetime(
        string='Acknowledgment Date',
        readonly=True,
        tracking=True,
        help='Date and time when vendor acknowledgment was recorded.'
    )

    # Optional notes about the acknowledgment.
    vendor_ack_notes = fields.Text(
        string='Vendor Acknowledgment Notes',
        help='Notes related to vendor acknowledgment of the purchase order.'
    )

    # Helper field for testing and UI visibility.
    # True when the document is already a confirmed Purchase Order.
    is_confirmed_purchase_order = fields.Boolean(
        string='Is Confirmed Purchase Order',
        compute='_compute_is_confirmed_purchase_order',
        help='Technical helper showing whether this record is already a confirmed Purchase Order.'
    )

    @api.depends('state')
    def _compute_is_confirmed_purchase_order(self):
        # In purchase.order, state = "purchase" means confirmed Purchase Order.
        for order in self:
            order.is_confirmed_purchase_order = order.state == 'purchase'

    def action_mark_vendor_acknowledged(self):
        """
        Mark the purchase order as acknowledged by the vendor.

        Logic:
        - the document must already be a confirmed PO
        - acknowledgment should only be recorded once
        """
        for order in self:
            if order.state != 'purchase':
                raise ValidationError(
                    'Vendor acknowledgment can only be recorded after the quotation is confirmed as a Purchase Order.'
                )

            if order.vendor_ack_received:
                raise ValidationError(
                    'Vendor acknowledgment has already been recorded for this Purchase Order.'
                )

            order.vendor_ack_received = True
            order.vendor_ack_recorded_by = self.env.user
            order.vendor_ack_date = fields.Datetime.now()

    def _check_vendor_acknowledgment_if_required(self):
        """
        Future helper for later phases.

        You may use this later if you want to block another step
        until vendor acknowledgment is recorded.
        """
        for order in self:
            if order.vendor_ack_required and not order.vendor_ack_received:
                raise ValidationError(
                    'Vendor acknowledgment is required before continuing this purchase process.'
                )
            
    # -------------------------------------------------------------------------
    # PHASE 5 - PURCHASE ORDER SIDE BILL TRACKING
    # -------------------------------------------------------------------------

    vendor_bill_count = fields.Integer(
        string='Vendor Bill Count',
        compute='_compute_vendor_bill_count',
        help='Number of vendor bills linked to this Purchase Order through the custom field.'
    )

    @api.depends()
    def _compute_vendor_bill_count(self):
        for order in self:
            order.vendor_bill_count = self.env['account.move'].search_count([
                ('purchase_order_id', '=', order.id),
                ('move_type', '=', 'in_invoice')
            ])