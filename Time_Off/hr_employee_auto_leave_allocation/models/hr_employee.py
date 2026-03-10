from odoo import models, api
from datetime import date


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)

        for employee in employees:
            employee._create_auto_leave_allocations()

        return employees

    def _create_auto_leave_allocations(self):
        self.ensure_one()

        LeaveType = self.env['hr.leave.type']
        LeaveAllocation = self.env['hr.leave.allocation']
        AccrualPlan = self.env['hr.leave.accrual.plan']

        sick_leave_type = LeaveType.search([('name', '=', 'Sick Leave')], limit=1)
        annual_leave_type = LeaveType.search([('name', '=', 'Annual Leave')], limit=1)

        sick_leave_plan = AccrualPlan.search([('name', '=', 'Monthly Sick Leave')], limit=1)
        annual_leave_plan = AccrualPlan.search([('name', '=', 'Annual Leave Plan')], limit=1)

        if sick_leave_type and sick_leave_plan:
            existing_sick = LeaveAllocation.search([
                ('employee_id', '=', self.id),
                ('holiday_status_id', '=', sick_leave_type.id),
                ('allocation_type', '=', 'accrual'),
            ], limit=1)

            if not existing_sick:
                sick_allocation = LeaveAllocation.create({
                    'name': f'Automatic Sick Leave Allocation - {self.name}',
                    'holiday_status_id': sick_leave_type.id,
                    'holiday_type': 'employee',
                    'employee_id': self.id,
                    'allocation_type': 'accrual',
                    'accrual_plan_id': sick_leave_plan.id,
                    'date_from': date.today(),
                })
                sick_allocation.action_approve()

        if annual_leave_type and annual_leave_plan:
            existing_annual = LeaveAllocation.search([
                ('employee_id', '=', self.id),
                ('holiday_status_id', '=', annual_leave_type.id),
                ('allocation_type', '=', 'accrual'),
            ], limit=1)

            if not existing_annual:
                annual_allocation = LeaveAllocation.create({
                    'name': f'Automatic Annual Leave Allocation - {self.name}',
                    'holiday_status_id': annual_leave_type.id,
                    'holiday_type': 'employee',
                    'employee_id': self.id,
                    'allocation_type': 'accrual',
                    'accrual_plan_id': annual_leave_plan.id,
                    'date_from': date.today(),
                })
                annual_allocation.action_approve()