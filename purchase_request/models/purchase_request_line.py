from lxml import etree
from odoo import models, fields, api
from odoo.exceptions import UserError


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
                line.estimated_unit_price = line.product_id.standard_price or 0.0
    

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)

        user_group_ids = self.env.user.groups_id.ids
        can_create = 79 in user_group_ids or 61 in user_group_ids

        if view_type in ['list', 'form']:
            arch = etree.fromstring(res['arch'])
            arch.set('create', 'true' if can_create else 'false')
            res['arch'] = etree.tostring(arch, encoding='unicode')

        return res

    @api.model
    def create(self, vals):
        user_group_ids = self.env.user.groups_id.ids
        if 79 not in user_group_ids and 61 not in user_group_ids:
            raise UserError("Only users in the Teacher or Administrator groups can add request lines.")
        return super().create(vals)

    @api.model
    def check_access_rights(self, operation, raise_exception=True):
        if operation == 'create':
            user_group_ids = self.env.user.groups_id.ids
            if 79 in user_group_ids or 61 in user_group_ids:
                return True
        return super().check_access_rights(operation, raise_exception=raise_exception) 