import logging

from odoo import http, _
from odoo.http import request
from werkzeug.urls import url_encode

_logger = logging.getLogger(__name__)


class CrmProjectRequestController(http.Controller):

    def _validate_submission(self, post):
        errors = []

        request_type = (post.get('request_type') or 'general_inquiry').strip()
        name = (post.get('name') or '').strip()
        email = (post.get('email') or '').strip()
        phone = (post.get('phone') or '').strip()
        message = (post.get('message') or '').strip()

        if not name:
            errors.append(_("Full Name is required."))
        if not email:
            errors.append(_("Email is required."))
        if not phone:
            errors.append(_("Phone Number is required."))
        if not message:
            errors.append(_("Message is required."))

        if request_type == 'project_request':
            company_name = (post.get('intake_company_name') or '').strip()
            project_title = (post.get('intake_project_title') or '').strip()
            project_description = (post.get('intake_project_description') or '').strip()
            requested_budget = (post.get('intake_requested_budget') or '').strip()
            requested_duration = (post.get('intake_requested_duration') or '').strip()
            requested_notes = (post.get('intake_requested_notes') or '').strip()

            if not company_name:
                errors.append(_("Company Name is required."))
            if not project_title:
                errors.append(_("Project Title is required."))
            if not project_description:
                errors.append(_("Project Description is required."))
            if not requested_budget:
                errors.append(_("Expected Budget is required."))
            else:
                try:
                    budget_value = float(requested_budget)
                    if budget_value <= 0:
                        errors.append(_("Expected Budget must be greater than 0."))
                except ValueError:
                    errors.append(_("Expected Budget must be a valid number."))
            if not requested_duration:
                errors.append(_("Expected Duration is required."))
            if not requested_notes:
                errors.append(_("Additional Notes are required."))

        return errors

    def _send_general_inquiry_email(self, post):
        name = (post.get('name') or '').strip()
        email = (post.get('email') or '').strip()
        phone = (post.get('phone') or '').strip()
        message = (post.get('message') or '').strip()

        mail_server = request.env['ir.mail_server'].sudo().search([], limit=1)
        company_email = mail_server.smtp_user if mail_server and mail_server.smtp_user else False

        if not company_email:
            raise ValueError("No outgoing mail server email was found.")

        subject = "New General Inquiry from Website: %s" % (name or "No Name")

        body_html = """
            <p><strong>New general inquiry received from the website.</strong></p>
            <p><strong>Full Name:</strong> %s</p>
            <p><strong>Email:</strong> %s</p>
            <p><strong>Phone Number:</strong> %s</p>
            <p><strong>Message:</strong><br/>%s</p>
        """ % (
            name or '',
            email or '',
            phone or '',
            message or '',
        )

        mail_values = {
            'subject': subject,
            'email_from': company_email,
            'email_to': company_email,
            'reply_to': email or company_email,
            'body_html': body_html,
        }

        mail = request.env['mail.mail'].sudo().create(mail_values)
        mail.send()

        _logger.warning("GENERAL INQUIRY EMAIL SENT TO: %s", company_email)



    @http.route('/project_request/submit', type='http', auth='public', website=True, csrf=True)
    def submit_project_request(self, **post):
        _logger.warning("=== PROJECT REQUEST SUBMIT START ===")
        _logger.warning("POST DATA: %s", post)

        try:
            errors = self._validate_submission(post)
            _logger.warning("VALIDATION ERRORS: %s", errors)

            if errors:
                query = url_encode({'form_error': ' | '.join(errors)})
                return request.redirect('/contactus?%s' % query)

            request_type = (post.get('request_type') or 'general_inquiry').strip()
            _logger.warning("REQUEST TYPE: %s", request_type)

            # Only project request creates a CRM lead
            if request_type == 'project_request':
                lead_vals = {
                    'name': post.get('intake_project_title') or 'Project Request',
                    'contact_name': post.get('name'),
                    'email_from': post.get('email'),
                    'phone': post.get('phone'),
                    'description': post.get('intake_project_description') or post.get('message'),
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
                _logger.warning("PROJECT LEAD VALS: %s", lead_vals)

                lead = request.env['crm.lead'].sudo().create_project_request_lead(lead_vals)
                _logger.warning("PROJECT LEAD CREATED: %s", lead.id)
            else:
                _logger.warning("GENERAL INQUIRY RECEIVED - SENDING EMAIL")
                self._send_general_inquiry_email(post)
            return request.redirect('/contactus?success=1')

        except Exception:
            _logger.exception("PROJECT REQUEST SUBMISSION FAILED")
            query = url_encode({'form_error': 'Submission failed. Please try again.'})
            return request.redirect('/contactus?%s' % query)