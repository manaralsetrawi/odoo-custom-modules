from odoo import http
from odoo.http import request


class NcstWebsiteRequestController(http.Controller):

    @http.route('/project-request/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def project_request_submit(self, **post):
        full_name = post.get('full_name', '').strip()
        email = post.get('email', '').strip()
        phone = post.get('phone', '').strip()
        company_name = post.get('company_name', '').strip()
        message_type = post.get('message_type', '').strip()
        message = post.get('message', '').strip()

        project_title = post.get('project_title', '').strip()
        project_type = post.get('project_type', '').strip()
        project_description = post.get('project_description', '').strip()
        requested_features = post.get('requested_features', '').strip()
        estimated_timeline = post.get('estimated_timeline', '').strip()
        estimated_budget = post.get('estimated_budget', '').strip()

        lead_name = project_title if project_title else 'Website Request'

        description_parts = [
            f"Message Type: {message_type or 'N/A'}",
            "",
            "Client Message:",
            message or 'N/A',
        ]

        if message_type == 'project_request':
            description_parts.extend([
                "",
                "Project Request Details:",
                f"Project Title: {project_title or 'N/A'}",
                f"Project Type: {project_type or 'N/A'}",
                f"Project Description: {project_description or 'N/A'}",
                f"Requested Features: {requested_features or 'N/A'}",
                f"Estimated Timeline: {estimated_timeline or 'N/A'}",
                f"Estimated Budget: {estimated_budget or 'N/A'}",
            ])

        description = "\n".join(description_parts)

        request.env['crm.lead'].sudo().create({
            'name': lead_name,
            'contact_name': full_name,
            'email_from': email,
            'phone': phone,
            'partner_name': company_name,
            'description': description,
        })

        return request.redirect('/contactus?submitted=1')