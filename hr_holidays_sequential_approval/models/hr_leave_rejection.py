# models/hr_leave_rejection.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrLeaveRejection(models.TransientModel):
    _name = 'hr.leave.rejection'
    _description = 'Leave Rejection Wizard'

    leave_id = fields.Many2one('hr.leave', string='Leave Request', required=True)
    rejection_by = fields.Selection([('supervisor', 'Supervisor'), ('hr', 'HR')], required=True)
    rejection_reason = fields.Text(string='Reason', required=True)

    def action_reject(self):
        self.ensure_one()
        if self.rejection_by == 'supervisor':
            self.leave_id._supervisor_reject(self.rejection_reason)
        else:
            self.leave_id._hr_reject(self.rejection_reason)
        return {'type': 'ir.actions.act_window_close'}