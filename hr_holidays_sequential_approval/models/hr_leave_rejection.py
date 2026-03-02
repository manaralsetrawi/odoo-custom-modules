# wizards/hr_leave_rejection.py
from odoo import models, fields

class HrLeaveRejection(models.TransientModel):
    _name = 'hr.leave.rejection'
    _description = 'Leave Request Rejection Wizard'

    leave_id = fields.Many2one('hr.leave', string='Leave Request', required=True)
    rejection_by = fields.Selection([('supervisor', 'Supervisor'), ('hr', 'HR')], required=True)
    rejection_reason = fields.Text(required=True, string='Rejection Reason')

    def action_reject(self):
        for wiz in self:
            if wiz.rejection_by == 'supervisor':
                wiz.leave_id._supervisor_reject(wiz.rejection_reason)
            elif wiz.rejection_by == 'hr':
                wiz.leave_id._hr_reject(wiz.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}