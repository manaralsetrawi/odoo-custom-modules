from odoo import models, fields, api


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'

    request_id = fields.Many2one(
        'purchase.request',
        string='Purchase Request',
        required=True,
        ondelete='cascade',
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )

    product_description = fields.Char(
        string='Item / Product Description',
    )

    specifications = fields.Text(
        string='Specifications',
    )

    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
    )

    estimated_unit_price = fields.Float(
        string='Estimated Unit Price',
        required=True,
        default=0.0,
    )

    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
    )

    @api.depends('quantity', 'estimated_unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.estimated_unit_price