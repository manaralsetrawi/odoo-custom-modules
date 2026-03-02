# models/hr_leave.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    supervisor_state = fields.Selection(
        [
            ('pending', 'Pending Supervisor Approval'),
            ('approved', 'Supervisor Approved'),
            ('rejected', 'Supervisor Rejected'),
        ],
        default='pending',
        string='Supervisor Approval Status',
        tracking=True,
    )

    hr_state = fields.Selection(
        [
            ('pending', 'Pending HR Approval'),
            ('approved', 'HR Approved'),
            ('rejected', 'HR Rejected'),
        ],
        default='pending',
        string='HR Approval Status',
        tracking=True,
    )

    supervisor_id = fields.Many2one(
        'res.users',
        string='Supervisor',
        compute='_compute_supervisor_id',
        store=True,
        readonly=True,
    )

    rejection_reason = fields.Text(string='Rejection Reason', tracking=True)

    # Optional flags for safer attrs in views
    is_current_user_supervisor = fields.Boolean(compute='_compute_user_flags', store=False)
    is_current_user_employee = fields.Boolean(compute='_compute_user_flags', store=False)
    is_current_user_hr = fields.Boolean(compute='_compute_user_flags', store=False)

    @api.depends('employee_id', 'employee_id.parent_id', 'employee_id.parent_id.user_id')
    def _compute_supervisor_id(self):
        for leave in self:
            # Make sure it’s a res.users object, not employee
            leave.supervisor_id = leave.employee_id.parent_id.user_id if leave.employee_id and leave.employee_id.parent_id else False
            
    @api.depends('employee_id.user_id')
    def _compute_user_flags(self):
        uid = self.env.user.id
        is_hr = self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr.group_hr_user')
        for leave in self:
            leave.is_current_user_employee = bool(leave.employee_id and leave.employee_id.user_id.id == uid)
            leave.is_current_user_supervisor = bool(leave.supervisor_id and leave.supervisor_id.id == uid)
            leave.is_current_user_hr = is_hr

    # ---------- Internal check helpers ----------
    def _check_supervisor(self):
        self.ensure_one()
        if self.supervisor_id.id != self.env.user.id:
            raise AccessError(_("Only the assigned supervisor can perform this action."))

    def _check_hr(self):
        self.ensure_one()
        if not (self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('hr.group_hr_user')):
            raise AccessError(_("Only HR can perform this action."))

    # ============================================
    # SUPERVISOR APPROVAL METHODS
    # ============================================
    def action_supervisor_approve(self):
        for leave in self:
            leave._check_supervisor()
            # Allow from 'pending' or previously 'rejected' by supervisor
            if leave.supervisor_state not in ('pending', 'rejected'):
                raise ValidationError(_("This request cannot be approved at this stage."))

            leave.rejection_reason = False
            leave.supervisor_state = 'approved'

            # Use core logic: first approval (validate1) if double validation
            super(HrLeave, leave).action_approve()

            leave._notify_hr_pending(leave)
            leave._notify_employee_status_change(leave, 'supervisor', 'approved')
        return True

    def action_supervisor_reject(self):
        self.ensure_one()
        self._check_supervisor()
        if self.supervisor_state not in ('pending', 'approved'):
            raise ValidationError(_("This request cannot be rejected at this stage."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.rejection',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_leave_id': self.id, 'rejection_by': 'supervisor'},
        }

    def _supervisor_reject(self, reason):
        for leave in self:
            leave.supervisor_state = 'rejected'
            leave.rejection_reason = reason

            # Core refusal to rollback allocations/resource leaves if needed
            super(HrLeave, leave).action_refuse()

            leave._notify_employee_rejected(leave, 'supervisor')
            leave._notify_employee_status_change(leave, 'supervisor', 'rejected')
        return True

    # ============================================
    # HR APPROVAL METHODS
    # ============================================
    def action_hr_approve(self):
        for leave in self:
            leave._check_hr()
            if leave.supervisor_state != 'approved':
                raise ValidationError(_("Supervisor must approve first before HR can approve."))
            if leave.hr_state not in ('pending', 'rejected'):
                raise ValidationError(_("This request is not pending HR approval."))

            leave.rejection_reason = False
            leave.hr_state = 'approved'

            # Final approval using core method
            super(HrLeave, leave).action_validate()

            leave._notify_employee_approved(leave)
            leave._notify_supervisor_approved(leave)
            leave._notify_employee_status_change(leave, 'hr', 'approved')
        return True

    def action_hr_reject(self):
        self.ensure_one()
        self._check_hr()
        if self.hr_state not in ('pending', 'approved'):
            raise ValidationError(_("This request cannot be rejected at this stage."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.leave.rejection',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_leave_id': self.id, 'rejection_by': 'hr'},
        }

    def _hr_reject(self, reason):
        for leave in self:
            leave._check_hr()
            leave.hr_state = 'rejected'
            leave.rejection_reason = reason

            # Use core refusal
            super(HrLeave, leave).action_refuse()

            leave._notify_employee_rejected(leave, 'hr')
            leave._notify_supervisor_rejected(leave)
            leave._notify_employee_status_change(leave, 'hr', 'rejected')
        return True

    # ============================================
    # NOTIFICATION METHODS (kept as-is)
    # ============================================
    def _notify_employee_approved(self, leave):
        if not leave.employee_id or not leave.employee_id.user_id:
            return
        body = _("Your leave request has been approved by HR.")
        leave.message_post(body=body, subtype_xmlid='mail.mt_comment', partner_ids=[leave.employee_id.user_id.partner_id.id])

    def _notify_employee_rejected(self, leave, rejected_by):
        if not leave.employee_id or not leave.employee_id.user_id:
            return
        rejected_by_text = _("Supervisor") if rejected_by == 'supervisor' else _("HR")
        body = _("Your leave request has been rejected by %s. Reason: %s") % (rejected_by_text, leave.rejection_reason or '')
        leave.message_post(body=body, subtype_xmlid='mail.mt_comment', partner_ids=[leave.employee_id.user_id.partner_id.id])

    def _notify_supervisor_approved(self, leave):
        if not leave.supervisor_id:
            return
        body = _("A leave request you approved has been further approved by HR.")
        leave.message_post(body=body, subtype_xmlid='mail.mt_comment', partner_ids=[leave.supervisor_id.partner_id.id])

    def _notify_supervisor_rejected(self, leave):
        if not leave.supervisor_id:
            return
        body = _("A leave request you approved has been rejected by HR. Reason: %s") % (leave.rejection_reason or '')
        leave.message_post(body=body, subtype_xmlid='mail.mt_comment', partner_ids=[leave.supervisor_id.partner_id.id])

    def _notify_hr_pending(self, leave):
        hr_group = self.env.ref('hr.group_hr_user', raise_if_not_found=False) or self.env.ref('hr_holidays.group_hr_holidays_user', raise_if_not_found=False)
        if not hr_group:
            return
        partner_ids = [u.partner_id.id for u in hr_group.users if u.partner_id]
        if partner_ids:
            leave.message_post(
                body=_("Supervisor has approved a leave request. Please review and approve."),
                subtype_xmlid='mail.mt_comment',
                partner_ids=partner_ids
            )

    def _notify_employee_status_change(self, leave, changed_by, new_status):
        if not leave.employee_id or not leave.employee_id.user_id:
            return
        changed_by_text = _("Supervisor") if changed_by == 'supervisor' else _("HR")
        status_text = _("approved") if new_status == 'approved' else _("rejected")
        body = _("Your leave request status has been changed to %s by %s.") % (status_text, changed_by_text)
        leave.message_post(body=body, subtype_xmlid='mail.mt_comment', partner_ids=[leave.employee_id.user_id.partner_id.id])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('supervisor_state', 'pending')
            vals.setdefault('hr_state', 'pending')
        return super().create(vals_list)

    # (Optional) Reset helpers. Consider using core transitions instead of raw state sets.
    def action_supervisor_reset(self):
        for leave in self:
            leave._check_supervisor()
            # Reset supervisor decision
            leave.supervisor_state = 'pending'
            leave.rejection_reason = False
            # Bring back to "to approve" properly
            if leave.state in ('validate1', 'validate'):
                super(HrLeave, leave).action_refuse()
            # reconfirm (employee's submitted state)
            if leave.state == 'refuse':
                super(HrLeave, leave).action_confirm()
        return True

    def action_hr_reset(self):
        for leave in self:
            leave._check_hr()
            if leave.hr_state not in ('approved', 'rejected'):
                raise ValidationError(_("There is no HR decision to reset."))
            leave.hr_state = 'pending'
            leave.rejection_reason = False
            # If it was fully validated, refuse then confirm to re-queue
            if leave.state == 'validate':
                super(HrLeave, leave).action_refuse()
                super(HrLeave, leave).action_confirm()
        return True
