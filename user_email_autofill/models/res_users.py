"""Auto-generate user email/login and tighten default group access.

This extension:
- Builds a default email/login from the user's name
- Enforces unique names
- Strips extra groups on create, leaving only minimum internal access
"""

import re

from odoo import api, models, Command
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    def _generate_email_from_name(self, name):
        """Build a standardized email from a user's name."""
        domain = "ncst.edu.bh"
        clean_name = (name or "").strip().lower()
        clean_name = re.sub(r"[^a-zA-Z\s]", "", clean_name)
        parts = clean_name.split()

        if not parts:
            return False

        if len(parts) == 1:
            local_part = parts[0]
        else:
            local_part = f"{parts[0]}.{parts[-1]}"

        return f"{local_part}@{domain}"

    @api.onchange("name")
    def _onchange_name_generate_email_login(self):
        """Auto-fill login/email when the name changes in the form."""
        for record in self:
            if record.name:
                generated_email = record._generate_email_from_name(record.name)
                if generated_email:
                    record.login = generated_email
                    record.email = generated_email

    @api.constrains("name")
    def _check_unique_name(self):
        """Prevent duplicate user display names (simple uniqueness rule)."""
        for record in self:
            if record.name:
                existing_user = self.search([
                    ("name", "=", record.name),
                    ("id", "!=", record.id),
                ], limit=1)

                if existing_user:
                    raise ValidationError(
                        f"A user with the name '{record.name}' already exists."
                    )

    def _get_minimum_default_groups_to_remove(self):
        """
        Remove default admin / extra access groups from new users.
        Any group not installed will be skipped safely.
        """
        xml_ids = [
            # Accounting / Invoicing
            "account.group_account_user",
            "account.group_account_manager",
            "account.group_account_readonly",
            "account.group_account_invoice",

            # Inventory
            "stock.group_stock_user",
            "stock.group_stock_manager",

            # Website
            "website.group_website_designer",
            "website.group_multi_website",

            # HR
            "hr.group_hr_user",
            "hr.group_hr_manager",
            "hr_holidays.group_hr_holidays_user",
            "hr_holidays.group_hr_holidays_manager",

            # Recruitment
            "hr_recruitment.group_hr_recruitment_user",
            "hr_recruitment.group_hr_recruitment_manager",
            "hr_recruitment.group_hr_recruitment_interviewer",

            # Attendances
            "hr_attendance.group_hr_attendance_user",
            "hr_attendance.group_hr_attendance_manager",
            "hr_attendance.group_hr_attendance_officer",

            # Purchase standard groups
            "purchase.group_purchase_user",
            "purchase.group_purchase_manager",

            # Sales
            "sales_team.group_sale_salesman",
            "sales_team.group_sale_salesman_all_leads",
            "sales_team.group_sale_manager",

            # Technical section extras
            "base.group_allow_export",
            "uom.group_uom",

            # Custom Purchase Execution Workflow groups
            "purchase_execution_workflow.group_procurement_officer",
            "purchase_execution_workflow.group_finance_director",
            "purchase_execution_workflow.group_deputy_ceo",
            "purchase_execution_workflow.group_ceo",
            "purchase_execution_workflow.group_end_user_receiver",
            "purchase_execution_workflow.group_invoice_verifier",
        ]

        groups = self.env["res.groups"]

        # Remove by XML ID
        for xml_id in xml_ids:
            group = self.env.ref(xml_id, raise_if_not_found=False)
            if group:
                groups |= group

        # Backup removal by visible name
        extra_groups_by_name = self.env["res.groups"].search([
            ("name", "in", [
                "Officer: Manage attendances",
                "Time Off Responsible",
                "Interviewer",
                "Billing",
            ])
        ])
        groups |= extra_groups_by_name

        # Strong cleanup by category name
        category_groups = self.env["res.groups"].search([
            ("category_id.name", "in", [
                "Recruitment",
                "Invoicing",
            ])
        ])
        groups |= category_groups

        return groups

    def _apply_minimum_default_access(self):
        """
        Keep only minimum internal user access for newly created users.
        """
        internal_user_group = self.env.ref("base.group_user", raise_if_not_found=False)
        portal_group = self.env.ref("base.group_portal", raise_if_not_found=False)
        public_group = self.env.ref("base.group_public", raise_if_not_found=False)

        groups_to_remove = self._get_minimum_default_groups_to_remove()

        for user in self:
            commands = []

            # Keep Internal User
            if internal_user_group:
                commands.append(Command.link(internal_user_group.id))

            # Remove Portal / Public if assigned
            if portal_group:
                commands.append(Command.unlink(portal_group.id))
            if public_group:
                commands.append(Command.unlink(public_group.id))

            # Remove unwanted groups
            for group in groups_to_remove:
                commands.append(Command.unlink(group.id))

            if commands:
                user.sudo().write({"groups_id": commands})

    @api.model_create_multi
    def create(self, vals_list):
        """Create users with auto email/login and minimal access groups."""
        for vals in vals_list:
            # Auto-generate email/login on create too
            if vals.get("name"):
                generated_email = self._generate_email_from_name(vals["name"])
                if generated_email:
                    if not vals.get("login"):
                        vals["login"] = generated_email
                    if not vals.get("email"):
                        vals["email"] = generated_email

            # Auto-set default password if none was provided
            if not vals.get("password"):
                vals["password"] = "NCST@1234"

        users = super().create(vals_list)
        users._apply_minimum_default_access()
        return users