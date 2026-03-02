from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # New custom fields for sequential approval
    supervisor_state = fields.Selection(
        [
            ('pending', 'Pending Supervisor Approval'),
            ('approved', 'Supervisor Approved'),
            ('rejected', 'Supervisor Rejected'),
        ],
        default='pending',
        string='Supervisor Approval Status',
        tracking=True
    )
    
    hr_state = fields.Selection(
        [
            ('pending', 'Pending HR Approval'),
            ('approved', 'HR Approved'),
            ('rejected', 'HR Rejected'),
        ],
        default='pending',
        string='HR Approval Status',
        tracking=True
    )
    
    supervisor_id = fields.Many2one(
        'res.users',
        string='Supervisor',
        compute='_compute_supervisor_id',
        store=True
    )
    
    rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True
    )

    @api.depends('employee_id')
    def _compute_supervisor_id(self):
        """Automatically assign the employee's manager as supervisor"""
        for leave in self:
            if leave.employee_id and leave.employee_id.parent_id:
                leave.supervisor_id = leave.employee_id.parent_id.user_id
            else:
                leave.supervisor_id = False

    # ============================================
    # SUPERVISOR APPROVAL METHODS
    # ============================================
    
    def action_supervisor_approve(self):
        """Supervisor approves the leave request"""
        for leave in self:
            if not leave.supervisor_id or leave.supervisor_id.id != self.env.user.id:
                raise ValidationError(
                    "Only the supervisor can approve this request."
                )
            
            if leave.supervisor_state != 'pending':
                raise ValidationError(
                    "This request is not pending supervisor approval."
                )
            
            leave.supervisor_state = 'approved'
            self._notify_hr_pending(leave)

    def action_supervisor_reject(self):
        """Supervisor rejects the leave request"""
        if not self.supervisor_id or self.supervisor_id.id != self.env.user.id:
            raise ValidationError(
                "Only the supervisor can reject this request."
            )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.rejection',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_leave_id': self.id, 'rejection_by': 'supervisor'},
        }

    def _supervisor_reject(self, reason):
        """Internal method to process supervisor rejection"""
        for leave in self:
            leave.supervisor_state = 'rejected'
            leave.rejection_reason = reason
            leave.state = 'refuse'
            
            self._notify_employee_rejected(leave, 'supervisor')

    # ============================================
    # HR APPROVAL METHODS
    # ============================================
    
    def action_hr_approve(self):
        """HR approves the leave request"""
        for leave in self:
            if leave.supervisor_state != 'approved':
                raise ValidationError(
                    "Supervisor must approve first before HR can approve."
                )
            
            if leave.hr_state != 'pending':
                raise ValidationError(
                    "This request is not pending HR approval."
                )
            
            leave.hr_state = 'approved'
            leave.state = 'validate'
            
            self._notify_employee_approved(leave)
            self._notify_supervisor_approved(leave)

    def action_hr_reject(self):
        """HR rejects the leave request"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.rejection',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_leave_id': self.id, 'rejection_by': 'hr'},
        }

    def _hr_reject(self, reason):
        """Internal method to process HR rejection"""
        for leave in self:
            if leave.hr_state != 'pending':
                raise ValidationError(
                    "This request is not pending HR rejection."
                )
            
            leave.hr_state = 'rejected'
            leave.rejection_reason = reason
            leave.state = 'refuse'
            
            self._notify_employee_rejected(leave, 'hr')
            self._notify_supervisor_rejected(leave)

    # ============================================
    # NOTIFICATION METHODS
    # ============================================
    
    def _notify_employee_approved(self, leave):
        """Send approval notification to employee"""
        if not leave.employee_id or not leave.employee_id.user_id:
            return
        
        body = "Your leave request has been approved by HR."
        leave.message_post(
            body=body,
            subtype_xmlid='mail.mt_comment',
            partner_ids=[leave.employee_id.user_id.partner_id.id]
        )

    def _notify_employee_rejected(self, leave, rejected_by):
        """Send rejection notification to employee"""
        if not leave.employee_id or not leave.employee_id.user_id:
            return
        
        rejected_by_text = "Supervisor" if rejected_by == 'supervisor' else "HR"
        body = f"Your leave request has been rejected by {rejected_by_text}. Reason: {leave.rejection_reason}"
        leave.message_post(
            body=body,
            subtype_xmlid='mail.mt_comment',
            partner_ids=[leave.employee_id.user_id.partner_id.id]
        )

    def _notify_supervisor_approved(self, leave):
        """Send approval notification to supervisor"""
        if not leave.supervisor_id:
            return
        
        body = "Your approved leave request has been further approved by HR."
        leave.message_post(
            body=body,
            subtype_xmlid='mail.mt_comment',
            partner_ids=[leave.supervisor_id.partner_id.id]
        )

    def _notify_supervisor_rejected(self, leave):
        """Send rejection notification to supervisor"""
        if not leave.supervisor_id:
            return
        
        body = f"A leave request you approved has been rejected by HR. Reason: {leave.rejection_reason}"
        leave.message_post(
            body=body,
            subtype_xmlid='mail.mt_comment',
            partner_ids=[leave.supervisor_id.partner_id.id]
        )

    def _notify_hr_pending(self, leave):
        """Notify HR that supervisor has approved"""
        hr_group = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if not hr_group:
            return
        
        partner_ids = [user.partner_id.id for user in hr_group.users if user.partner_id]
        
        if partner_ids:
            leave.message_post(
                body="Supervisor has approved leave request. Please review and approve.",
                subtype_xmlid='mail.mt_comment',
                partner_ids=partner_ids
            )

    @api.model
    def create(self, vals):
        """Initialize approval states when creating a new leave request"""
        vals['supervisor_state'] = 'pending'
        vals['hr_state'] = 'pending'
        return super().create(vals)

    # ============================================
    # DISABLE DEFAULT APPROVAL METHODS
    # ============================================

    def action_approve(self):
        """Override default approve - disable it"""
        raise ValidationError(
            "Please use 'Approve as Supervisor' or 'Approve as HR' buttons instead."
        )

    def action_refuse(self):
        """Override default refuse - disable it"""
        raise ValidationError(
            "Please use 'Reject as Supervisor' or 'Reject as HR' buttons instead."
        )

    def action_validate(self):
        """Override default validate - disable it"""
        raise ValidationError(
            "Validation must go through the sequential approval workflow."
        )