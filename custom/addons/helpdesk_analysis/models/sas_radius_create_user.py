import json
import requests

from odoo import models, fields, api
from odoo.exceptions import UserError

from .aes_controller import AESController

class ResPartnerSAS(models.Model):
    _inherit = "res.partner"

    sas_radius_id = fields.Integer(string="SAS User ID", readonly=True)
    is_sas_user = fields.Boolean(string="Is SAS User", default=False)

    def _login_to_sas_radius_server(self, base_url, username, password):
        """Login to SAS, return Bearer token."""
        passphrase = "abcdefghijuklmno0123456789012345"
        login_url = f"{base_url}/admin/api/index.php/api/login"

        token_form = {
            "username": username,
            "password": password,
            "language": "en"
        }
        encrypted_data = AESController.encrypt(json.dumps(token_form).encode('utf-8'), passphrase)
        payload = {"payload": encrypted_data}
        headers = {'Content-Type': 'application/json'}

        resp = requests.post(login_url, json=payload, headers=headers, verify=False)
        if resp.status_code != 200:
            raise UserError(f"Login request failed: {resp.status_code} - {resp.text}")
        data = resp.json()
        token = data.get("token")
        if not token:
            raise UserError(f"No token in login response: {data}")
        return token

    def _fetch_sas_user_by_username(self, token, base_url, username):
        """
        Example method to fetch a single user from SAS by username.
        Must adapt to your SAS endpoint.
        Return the user ID or False if not found.
        """

        endpoint = f"{base_url}/admin/api/index.php/api/index/user?page=1"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        # Build a search payload
        search_payload = {
            "payload": AESController.encrypt(
                json.dumps({
                    "count": 1,
                    "sortBy": "created_at",
                    "direction": "desc",
                    "parent_id": None,
                    "profile_id": None,
                    "search": username,
                    "columns": [
                        "id",
                        "username",
                    ]
                }).encode('utf-8'),
                "abcdefghijuklmno0123456789012345"
            )
        }

        resp = requests.post(endpoint, json=search_payload, headers=headers, verify=False)
        if resp.status_code != 200:
            return False

        resp_json = resp.json()
        users_list = resp_json.get('data', [])
        for user in users_list:
            if user.get('username') == username:
                return user.get('id')
        return False

    def action_create_sas_user(self):
        """
        Button method to create user in SAS (if not exists), or link an existing user if SAS says
        "username is already taken". If we succeed or retrieve the ID, we set partner.sas_radius_id
        and create 'sas.radius.user' to avoid duplicates.
        """
        company = self.env.company
        if not company.url or not company.username or not company.password:
            raise UserError("SAS credentials not set on the current company.")

        token = self._login_to_sas_radius_server(company.url, company.username, company.password)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
        }
        passphrase = "abcdefghijuklmno0123456789012345"
        create_user_url = f"{company.url}/admin/api/index.php/api/user"

        for partner in self:
            # ===== Update to handle old records gracefully =====
            if not hasattr(partner, 'sas_radius_id'):
                # Skip if the field does not exist for this partner
                continue

            if partner.sas_radius_id:
                # Already linked, skip
                continue

            # Prepare the payload to create a user in SAS
            username_for_sas = partner.username or partner.email or ""
            user_data = {
                "username": username_for_sas,
                "enabled": 1,
                "password": "1111",
                "confirm_password": "1111",
                "profile_id": 1,
                "parent_id": 1,
                "site_id": 0,
                "mac_auth": 0,
                "allowed_macs": None,
                "firstname": partner.name or "",
                "lastname": "",
                "company": partner.company_name or "",
                "email": partner.email or "",
                "phone": partner.phone or "",
                "city": partner.city or "",
                "address": partner.street2 or "",
                "apartment": None,
                "street": partner.street or "",
                "contract_id": getattr(partner, 'sas_contract_id', None),  # Handle missing field
                "national_id": None,
                "notes": None,
                "expiration": "2030-01-01 00:00:00",
                "simultaneous_sessions": 1,
                "static_ip": None,
                "mikrotik_winbox_group": None,
                "mikrotik_framed_route": None,
                "mikrotik_addresslist": None,
                "mikrotik_ipv6_prefix": None,
                "auto_renew": 0,
                "user_type": "0"
            }

            # Encrypt the JSON
            encrypted_payload = AESController.encrypt(
                json.dumps(user_data).encode("utf-8"),
                passphrase
            )

            # Send creation request to SAS
            resp = requests.post(
                create_user_url,
                json={"payload": encrypted_payload},
                headers=headers,
                verify=False
            )
            if resp.status_code != 200:
                raise UserError(f"Create user request failed: {resp.status_code} - {resp.text}")

            resp_json = resp.json()
            status = resp_json.get("status")
            message = resp_json.get("message", "")
            data_node = resp_json.get("data", {})

            # 1) If SAS says "username is already taken" => status = -2
            if status == -2:
                # fallback: fetch user from SAS by username
                existing_id = self._fetch_sas_user_by_username(token, company.url, username_for_sas)
                if not existing_id:
                    raise UserError(f"Username already taken, but could not fetch ID from SAS. Response: {resp_json}")

                # Link it in Odoo
                partner.sas_radius_id = existing_id
                partner.is_sas_user = True

                self.env['sas.radius.user'].create({
                    'user_sas_radius_id': existing_id,
                    'partner': partner.id,
                    'company_id': company.id,
                })
                continue

            # 2) If SAS returns "status = 200" => success
            if status == 200:
                sas_id = data_node.get("id")  # some SAS systems might put the ID here
                if not sas_id:
                    # If no 'id' => fallback: fetch user by username
                    sas_id = self._fetch_sas_user_by_username(token, company.url, username_for_sas)
                    if not sas_id:
                        raise UserError(f"No user ID returned from SAS: {resp_json}")

                # Now we have an ID
                partner.sas_radius_id = sas_id
                partner.is_sas_user = True

                # Also create in sas.radius.user
                self.env['sas.radius.user'].create({
                    'user_sas_radius_id': sas_id,
                    'partner': partner.id,
                    'company_id': company.id,
                })
                continue

            # 3) Otherwise, handle other statuses
            raise UserError(f"SAS user creation error: {resp_json}")

        return True
