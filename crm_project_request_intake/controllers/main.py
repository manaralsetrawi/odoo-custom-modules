from odoo import http
from odoo.http import request


class CrmProjectRequestController(http.Controller):

    @http.route('/project_request/submit', type='http', auth='public', website=True, csrf=True)
    def submit_project_request(self, **post):
        request_type = post.get('request_type', 'general_inquiry')

        # Keep the normal Contact Us behavior simple for now
        # If it is not a project request, create a basic lead as inquiry
        if request_type != 'project_request':
            lead_vals = {
                'name': post.get('subject') or post.get('name') or 'General Inquiry',
                'contact_name': post.get('name'),
                'email_from': post.get('email'),
                'phone': post.get('phone'),
                'description': post.get('description') or post.get('message'),
                'request_type': 'general_inquiry',
                'type': 'lead',
            }
            request.env['crm.lead'].sudo().create(lead_vals)
            return request.redirect('/contactus-thank-you')

        # Project Request flow
        lead_vals = {
            'name': post.get('intake_project_title') or post.get('subject') or 'Project Request',
            'contact_name': post.get('name'),
            'email_from': post.get('email'),
            'phone': post.get('phone'),
            'description': post.get('intake_project_description') or post.get('message'),

            # Your custom intake fields
            'request_type': 'project_request',
            'intake_client_name': post.get('name'),
            'intake_client_email': post.get('email'),
            'intake_client_phone': post.get('phone'),
            'intake_company_name': post.get('intake_company_name'),
            'intake_project_title': post.get('intake_project_title'),
            'intake_project_description': post.get('intake_project_description'),
            'intake_requested_budget': float(post.get('intake_requested_budget') or 0.0),
            'intake_requested_duration': post.get('intake_requested_duration'),
            'intake_requested_notes': post.get('intake_requested_notes'),
        }

        request.env['crm.lead'].sudo().create_project_request_lead(lead_vals)

        return request.redirect('/contactus-thank-you')