import re

from odoo import api, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    def _generate_email_from_name(self, name):
        """Generate email/login in the format first.last@ncst.edu.bh"""
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            name = vals.get("name", "").strip()

            if name:
                existing_user = self.search([("name", "=", name)], limit=1)
                if existing_user:
                    raise ValidationError(
                        f"A user with the name '{name}' already exists."
                    )

                generated_email = self._generate_email_from_name(name)

                if generated_email:
                    if not vals.get("login"):
                        vals["login"] = generated_email
                    if not vals.get("email"):
                        vals["email"] = generated_email

        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            new_name = vals.get("name", record.name or "").strip()

            if "name" in vals and new_name:
                existing_user = self.search(
                    [("name", "=", new_name), ("id", "!=", record.id)],
                    limit=1,
                )
                if existing_user:
                    raise ValidationError(
                        f"A user with the name '{new_name}' already exists."
                    )

                generated_email = self._generate_email_from_name(new_name)

                if generated_email:
                    if "login" not in vals or not vals.get("login"):
                        vals["login"] = generated_email
                    if "email" not in vals or not vals.get("email"):
                        vals["email"] = generated_email

        return super().write(vals)