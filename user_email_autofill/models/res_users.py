import re

from odoo import api, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    # Generate email automatically from the user's name
    def _generate_email_from_name(self, name):
        domain = "ncst.edu.bh"
        clean_name = (name or "").strip().lower()

        # Remove any characters except letters and spaces
        clean_name = re.sub(r"[^a-zA-Z\s]", "", clean_name)
        parts = clean_name.split()

        if not parts:
            return False

        # If name has one word use it directly
        if len(parts) == 1:
            local_part = parts[0]
        else:
            # If name has multiple words use first and last name
            local_part = f"{parts[0]}.{parts[-1]}"

        return f"{local_part}@{domain}"

    # Automatically generate login and email when the name changes in the UI
    @api.onchange("name")
    def _onchange_name_generate_email_login(self):
        for record in self:
            if record.name:
                generated_email = record._generate_email_from_name(record.name)
                if generated_email:
                    record.login = generated_email
                    record.email = generated_email

    # Prevent creating two users with the same name
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

    # Override the create method to assign a default password
    @api.model
    def create(self, vals):
        # If login or email were not generated yet, generate them from the name
        if vals.get("name"):
            generated_email = self._generate_email_from_name(vals["name"])
            if generated_email:
                vals.setdefault("login", generated_email)
                vals.setdefault("email", generated_email)

        # Set a default password for every new user
        # Only applies if no password was manually provided
        if not vals.get("password"):
            vals["password"] = "NCST@1234"

        # Create the user with the updated values
        return super(ResUsers, self).create(vals)