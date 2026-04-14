import re

from odoo import api, models, Command
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    def _generate_email_from_name(self, name):
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
        for record in self:
            if record.name:
                generated_email = record._generate_email_from_name(record.name)
                if generated_email:
                    record.login = generated_email
                    record.email = generated_email

    @api.constrains("name")
    def _check_unique_name(self):
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

            # Inventory
            "stock.group_stock_user",
            "stock.group_stock_manager",

            # Website
            "website.group_website_designer",
            "website.group_multi_website",

            # HR
            "hr.group_hr_user",
            "hr.group_hr_manager",
            "hr_holidays.group_hr_holidays_user",       # Time Off Responsible / user-side access
            "hr_holidays.group_hr_holidays_manager",    # Time Off Administrator
            "hr_recruitment.group_hr_recruitment_user",
            "hr_recruitment.group_hr_recruitment_manager",
            "hr_attendance.group_hr_attendance_user",   # Officer: Manage attendances
            "hr_attendance.group_hr_attendance_manager",

            # Purchase standard groups
            "purchase.group_purchase_user",
            "purchase.group_purchase_manager",

            # Technical section extras from your screenshot
            "base.group_allow_export",
            "uom.group_uom",

            # Add your custom purchase groups here
            # Replace these XML IDs with the real ones from your custom module
            "your_module_name.group_purchase_academic_principal",
            "your_module_name.group_purchase_coordinator",
            "your_module_name.group_purchase_user",
            "your_module_name.group_purchase_administrator",
            "your_module_name.group_purchase_teacher",
        ]

        groups = self.env["res.groups"]
        for xml_id in xml_ids:
            group = self.env.ref(xml_id, raise_if_not_found=False)
            if group:
                groups |= group

        return groups

    def _apply_minimum_default_access(self):
        """
        Keep only minimum internal-user style access for newly created users.
        """
        internal_user_group = self.env.ref("base.group_user", raise_if_not_found=False)
        portal_group = self.env.ref("base.group_portal", raise_if_not_found=False)
        public_group = self.env.ref("base.group_public", raise_if_not_found=False)

        groups_to_remove = self._get_minimum_default_groups_to_remove()

        for user in self:
            commands = []

            # Ensure Internal User
            if internal_user_group:
                commands.append(Command.link(internal_user_group.id))

            # Remove portal/public just in case
            if portal_group:
                commands.append(Command.unlink(portal_group.id))
            if public_group:
                commands.append(Command.unlink(public_group.id))

            # Remove unwanted default/admin groups
            for group in groups_to_remove:
                commands.append(Command.unlink(group.id))

            if commands:
                user.sudo().write({"groups_id": commands})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Auto-generate email/login on create
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

        # Apply minimum access defaults after create
        users._apply_minimum_default_access()

        return users