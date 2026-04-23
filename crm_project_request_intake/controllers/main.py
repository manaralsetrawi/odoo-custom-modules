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
        company = request.env.company
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        logo_url = "https://ncst.edu.bh/wp-content/uploads/2025/05/ncst-logo.png"

        body_html = """
        <div style="margin:0; padding:0; background-color:#f4f6f8;">
            <div style="max-width:700px; margin:0 auto; background-color:#ffffff; padding:30px; font-family:Arial, sans-serif; color:#333333; border:1px solid #dddddd; border-radius:8px;">

                <div style="text-align:center; margin-bottom:20px;">
                    <img src="%s" alt="Company Logo" style="max-height:80px; max-width:220px;"/>
                </div>

                <div style="border-bottom:2px solid #0b2c3d; padding-bottom:15px; margin-bottom:25px;">
                    <h2 style="margin:0; color:#0b2c3d;">New General Inquiry</h2>
                    <p style="margin:8px 0 0 0; font-size:14px; color:#666666;">
                        A new inquiry has been submitted through the website contact form.
                    </p>
                </div>

                <table style="width:100%%; border-collapse:collapse; font-size:14px;">
                    <tr>
                        <td style="padding:10px 0; width:180px; font-weight:bold;">Full Name:</td>
                        <td style="padding:10px 0;">%s</td>
                    </tr>
                    <tr>
                        <td style="padding:10px 0; font-weight:bold;">Email:</td>
                        <td style="padding:10px 0;">%s</td>
                    </tr>
                    <tr>
                        <td style="padding:10px 0; font-weight:bold;">Phone Number:</td>
                        <td style="padding:10px 0;">%s</td>
                    </tr>
                </table>

                <div style="margin-top:25px;">
                    <p style="font-weight:bold; margin-bottom:10px;">Message:</p>
                    <div style="background-color:#f8f9fa; border:1px solid #e0e0e0; padding:15px; border-radius:6px; line-height:1.6;">
                        %s
                    </div>
                </div>

                <div style="margin-top:30px; border-top:1px solid #dddddd; padding-top:15px; font-size:12px; color:#777777;">
                    This email was automatically generated by the NCST website contact form.
                </div>
            </div>
        </div>
        """ % (
            logo_url,
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

        if email:
            client_subject = "We received your inquiry"
            
            client_body_html = """
<div style="margin:0; padding:0; background-color:#f4f6f8;">
    <div style="max-width:700px; margin:0 auto; background-color:#ffffff; padding:30px; font-family:Arial, sans-serif; color:#333333; border:1px solid #dddddd; border-radius:8px;">

        <div style="text-align:center; margin-bottom:20px;">
            <img src="%s" alt="Company Logo" style="max-height:80px; max-width:220px;"/>
        </div>

        <div style="border-bottom:2px solid #0b2c3d; padding-bottom:15px; margin-bottom:25px;">
            <h2 style="margin:0; color:#0b2c3d;">Inquiry Received Successfully</h2>
        </div>

        <p>Dear %s,</p>

        <p>
            Thank you for contacting us. Your inquiry has been received successfully.
        </p>

        <p>
            Our team will review your message and get back to you as soon as possible.
        </p>

        <div style="margin-top:20px;">
            <p style="font-weight:bold; margin-bottom:10px;">Your Message:</p>
            <div style="background-color:#f8f9fa; border:1px solid #e0e0e0; padding:15px; border-radius:6px; line-height:1.6;">
                %s
            </div>
        </div>

        <p style="margin-top:25px;">
            Best regards,<br/>
            NCST Team
        </p>

        <div style="margin-top:30px; border-top:1px solid #dddddd; padding-top:15px; font-size:12px; color:#777777;">
            This is an automated acknowledgement email. Please do not reply directly to this message unless instructed otherwise.
        </div>
    </div>
</div>
""" % (
                logo_url,
                name or 'Client',
                message or '',
            )

            client_mail_values = {
                'subject': client_subject,
                'email_from': company_email,
                'email_to': email,
                'reply_to': company_email,
                'body_html': client_body_html,
            }

            client_mail = request.env['mail.mail'].sudo().create(client_mail_values)
            client_mail.send()

            _logger.warning("GENERAL INQUIRY ACKNOWLEDGEMENT SENT TO CLIENT: %s", email)





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