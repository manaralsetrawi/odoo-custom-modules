import re

from odoo import api, models
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