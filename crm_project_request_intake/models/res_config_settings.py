from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    crm_general_inquiry_email = fields.Char(
        string='General Inquiry Recipient Email',
        config_parameter='crm_project_request_intake.crm_general_inquiry_email',
    )