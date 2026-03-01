from odoo import models, fields, api

class HrLeaveRejection(models.TransientModel):
    _name = 'hr.leave.rejection'
    _description = 'Leave Request Rejection Wizard'

    leave_id = fields.Many2one('hr.leave', string='Leave Request')
    rejection_by = fields.Char()
    rejection_reason = fields.Text(required=True, string='Rejection Reason')

    def action_reject(self):
        """Process the rejection"""
        if self.rejection_by == 'supervisor':
            self.leave_id._supervisor_reject(self.rejection_reason)
        elif self.rejection_by == 'hr':
            self.leave_id._hr_reject(self.rejection_reason)
        
        return {'type': 'ir.actions.act_window_close'}