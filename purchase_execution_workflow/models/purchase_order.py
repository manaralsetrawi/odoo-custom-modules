from odoo import api, fields, models


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