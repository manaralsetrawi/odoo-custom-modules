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
                _logger.warning("GENERAL INQUIRY RECEIVED - NO CRM LEAD CREATED")

            return request.redirect('/contactus?success=1')

        except Exception:
            _logger.exception("PROJECT REQUEST SUBMISSION FAILED")
            query = url_encode({'form_error': 'Submission failed. Please try again.'})
            return request.redirect('/contactus?%s' % query)