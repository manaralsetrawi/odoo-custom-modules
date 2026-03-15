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

    # product_description = fields.Char(
    #     string='Item / Product Description',
    # )

    specifications = fields.Text(
        string='Specifications',
    )

    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
    )

    estimated_unit_price = fields.Float(
        string='Unit Price',
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
    

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.product_description = line.product_id.display_name
                line.estimated_unit_price = line.product_id.standard_price or 0.0