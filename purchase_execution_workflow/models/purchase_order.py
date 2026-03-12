from odoo import api, fields, models
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Link each RFQ / PO to the related Purchase Request.
    # This is the main field that connects purchase request module with my module.
    purchase_request_id = fields.Many2one(
        'purchase.request',
        string='Purchase Request',
        tracking=True,
        help='Related purchase request for this quotation or purchase order.'
    )

    # Helper field: counts how many RFQs / POs are linked to the same purchase request.
    # This supports the requirement:
    # one Purchase Request -> multiple quotations
    quotation_count_for_request = fields.Integer(
        string='Quotation Count',
        compute='_compute_quotation_count_for_request',
        help='Number of quotations linked to the same purchase request.'
    )

    # Helper field: quickly shows whether this RFQ/PO is linked to a purchase request.
    has_purchase_request = fields.Boolean(
        string='Has Purchase Request',
        compute='_compute_has_purchase_request',
        help='Technical helper showing whether this RFQ is linked to a purchase request.'
    )

    # Helper field for later phases.
    # This will later support the business rule:
    # minimum 3 quotations if amount > BD 1000
    is_above_quotation_threshold = fields.Boolean(
        string='Above BD 1000',
        compute='_compute_is_above_quotation_threshold',
        help='True when the RFQ total amount is greater than BD 1000.'
    )

    # Helper field to know whether this purchase request already has multiple quotations.
    # Useful for testing and later validation logic.
    is_multi_quotation_case = fields.Boolean(
        string='Multi Quotation Case',
        compute='_compute_is_multi_quotation_case',
        help='True when more than one quotation exists for the same purchase request.'
    )

    @api.depends('purchase_request_id')
    def _compute_has_purchase_request(self):
        # Mark True when a purchase request is linked to the RFQ / PO.
        for order in self:
            order.has_purchase_request = bool(order.purchase_request_id)

    @api.depends('purchase_request_id')
    def _compute_quotation_count_for_request(self):
        # Count all quotations / purchase orders linked to the same purchase request.
        # This is the core logic for Phase 1.
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
        # This helper will be reused later in Phase 2 validations.
        for order in self:
            order.is_above_quotation_threshold = order.amount_total > 1000

    @api.depends('quotation_count_for_request')
    def _compute_is_multi_quotation_case(self):
        # Mark True when more than one RFQ exists for the same purchase request.
        for order in self:
            order.is_multi_quotation_case = order.quotation_count_for_request > 1


  # -------------------------------------------------------------------------
    #  QUOTATION EVALUATION AND VENDOR RECOMMENDATION
    # -------------------------------------------------------------------------

    # Technical evaluation result entered by procurement.
    # Example: product specifications match, quality acceptable, delivery suitable.
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
    # Example: price competitiveness, payment terms, delivery time, etc.
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

    # General procurement notes about this quotation.
    evaluation_notes = fields.Text(
        string='Evaluation Notes',
        help='Notes related to technical/commercial evaluation of this quotation.'
    )

    # Marks whether this quotation is the recommended vendor quotation.
    # Usually only one RFQ should end up recommended for the same purchase request.
    is_recommended_vendor = fields.Boolean(
        string='Recommended Vendor',
        tracking=True,
        help='Checked when this quotation is selected as the recommended vendor.'
    )

    # Reason for selecting this quotation.
    recommendation_reason = fields.Text(
        string='Recommendation Reason',
        help='Reason for recommending this supplier quotation.'
    )

    # Helper field for testing and later workflow control.
    # True if the RFQ satisfies the minimum quotation rule for its related PR.
    meets_minimum_quotation_rule = fields.Boolean(
        string='Meets Minimum Quotation Rule',
        compute='_compute_meets_minimum_quotation_rule',
        help='True when the required number of quotations is available for this purchase request.'
    )

    @api.depends('purchase_request_id', 'quotation_count_for_request', 'is_above_quotation_threshold')
    def _compute_meets_minimum_quotation_rule(self):
        """
        Rule:
        - If amount <= 1000 -> no minimum 3 quotation requirement
        - If amount > 1000 -> at least 3 quotations must exist for the same purchase request
        """
        for order in self:
            if not order.purchase_request_id:
                # If no PR is linked, keep it False for safety.
                # This protects the process until all procurement records are linked correctly.
                order.meets_minimum_quotation_rule = False
            elif not order.is_above_quotation_threshold:
                order.meets_minimum_quotation_rule = True
            else:
                order.meets_minimum_quotation_rule = order.quotation_count_for_request >= 3

    def _check_minimum_quotation_requirement(self):
        """
        Validate the quotation count rule before confirming the purchase order.

        requirement:
        - minimum 3 quotations for purchases above BD 1000
        """
        for order in self:
            # Safety: every RFQ/PO in this custom flow should be linked to a Purchase Request.
            if not order.purchase_request_id:
                raise ValidationError(
                    'Please link this quotation to a Purchase Request before confirming it.'
                )

            # If total amount is above threshold, require at least 3 quotations.
            if order.is_above_quotation_threshold and order.quotation_count_for_request < 3:
                raise ValidationError(
                    'At least 3 quotations are required for purchase requests above BD 1000.'
                )

    def action_mark_as_recommended(self):
        """
        Mark the current quotation as the recommended vendor quotation.

        Main idea:
        - only one quotation should usually be recommended for the same purchase request
        - when this quotation is marked recommended, remove the recommendation flag
          from other quotations linked to the same purchase request
        """
        for order in self:
            if not order.purchase_request_id:
                raise ValidationError(
                    'Please link this quotation to a Purchase Request before marking it as recommended.'
                )

            # Remove recommendation from other quotations linked to the same PR.
            other_orders = self.search([
                ('purchase_request_id', '=', order.purchase_request_id.id),
                ('id', '!=', order.id)
            ])
            other_orders.write({'is_recommended_vendor': False})

            # Mark the current quotation as recommended.
            order.is_recommended_vendor = True

    def button_confirm(self):
        """
        Override standard PO confirmation.

        For Phase 2, we enforce:
        1) RFQ must be linked to a Purchase Request
        2) minimum 3 quotations rule must be satisfied for requests above BD 1000

        Later phases can extend this same method again for:
        - financial approval
        - vendor acknowledgement
        """
        self._check_minimum_quotation_requirement()
        return super().button_confirm()
