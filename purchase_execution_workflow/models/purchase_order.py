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