from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # Link each RFQ / PO to the related Purchase Request created in purchase request custom module.
    # This is the base field that allows traceability between request and procurement flow.
    purchase_request_id = fields.Many2one(
        'purchase.request', #later REPLACE with the actual model name of the purchase request in the custom module
        string='Purchase Request',
        tracking=True,
        help='Related purchase request for this quotation or purchase order.'
    )

    # Helper field: counts how many quotations are linked to the same purchase request.
    # This will later help us enforce the "minimum 3 quotations if amount > BD 1000" rule.
    quotation_count_for_request = fields.Integer(
        string='Quotation Count',
        compute='_compute_quotation_count_for_request',
        store=False
    )

    # Helper field: tells us if this RFQ / PO total is above the quotation threshold.
    # We use this later in validation logic before confirming the PO.
    is_request_above_threshold = fields.Boolean(
        string='Above BD 1000',
        compute='_compute_is_request_above_threshold',
        store=False
    )

    @api.depends('purchase_request_id')
    def _compute_quotation_count_for_request(self):
        for order in self:
            if order.purchase_request_id:
                # Count all purchase orders / quotations linked to the same purchase request.
                order.quotation_count_for_request = self.search_count([
                    ('purchase_request_id', '=', order.purchase_request_id.id)
                ])
            else:
                order.quotation_count_for_request = 0

    @api.depends('amount_total')
    def _compute_is_request_above_threshold(self):
        for order in self:
            # Mark True when the total amount is greater than BD 1000.
            order.is_request_above_threshold = order.amount_total > 1000