from odoo import http
from odoo.http import request


class NcstWebsiteRequestController(http.Controller):

    @http.route('/project-request', type='http', auth='public', website=True)
    def project_request_page(self, **kwargs):
        """Render the public website request form page."""
        return request.render('ncst_website_request.project_request_page')

    @http.route('/project-request/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def project_request_submit(self, **post):
        """
        Handle website form submission and create a CRM lead.
        This creates only an initial CRM request/lead.
        It does NOT create a project and does NOT start the full internal flow.
        """

        # Always visible fields
        full_name = post.get('full_name', '').strip()
        email = post.get('email', '').strip()
        phone = post.get('phone', '').strip()
        company_name = post.get('company_name', '').strip()
        message_type = post.get('message_type', '').strip()
        message = post.get('message', '').strip()

        # Project request fields (shown only when message_type = project_request)
        project_title = post.get('project_title', '').strip()
        project_type = post.get('project_type', '').strip()
        project_description = post.get('project_description', '').strip()
        requested_features = post.get('requested_features', '').strip()
        estimated_timeline = post.get('estimated_timeline', '').strip()
        estimated_budget = post.get('estimated_budget', '').strip()

        # Lead title
        lead_name = project_title if project_title else 'Website Request'

        # Build description nicely
        description_parts = [
            f"Message Type: {message_type or 'N/A'}",
            f"Client Message: {message or 'N/A'}",
        ]

        if message_type == 'project_request':
            description_parts.extend([
                "",
                "Project Request Details:",
                f"Project Type: {project_type or 'N/A'}",
                f"Project Description: {project_description or 'N/A'}",
                f"Requested Features: {requested_features or 'N/A'}",
                f"Estimated Timeline: {estimated_timeline or 'N/A'}",
                f"Estimated Budget: {estimated_budget or 'N/A'}",
            ])

        description = "\n".join(description_parts)

        # Create CRM lead
        request.env['crm.lead'].sudo().create({
            'name': lead_name,
            'contact_name': full_name,
            'email_from': email,
            'phone': phone,
            'partner_name': company_name,
            'description': description,
        })

        # Show thank-you page
        return request.render('ncst_website_request.project_request_thank_you', {
            'full_name': full_name,
        })