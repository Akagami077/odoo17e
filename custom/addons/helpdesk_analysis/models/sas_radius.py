# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

from .aes_controller import AESController

import requests
import urllib3
import json
from datetime import datetime
# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
    Columns doesn't affect anything in the users list form in USERS_LIST_FORM as I've tested previously,
    Because always I'm getting the same response fields (columns)
'''



class SasRadius(models.Model):
    _name = 'sas.radius.user'

    user_sas_radius_id = fields.Integer(string="SAS Radius User ID", required=True)
    mac_added = fields.Boolean(string="Mac Address", default=False)
    partner = fields.Many2one('res.partner', string="Sas Radius Partner", default=False)
    user_sas_updated_at = fields.Datetime(string="Sas Radius Update At Date", default=fields.Datetime.now())
    company_id = fields.Many2one('res.company', string='Company', )
    # TOKEN_FORM = {"username": "husmoh", "password": "G5nJ0y8JbdrR", "language": "en"}

    USERS_LIST_FORM = {
        "count" :  100,
        "sortBy" : "created_at",
        "direction" : "desc",
        "parent_id": None,
        "profile_id": None,
        "search" : "",
        "columns" : [
            "id",
            "username",
            "firstname",
            "lastname",
            "expiration",
            "parent_username",
            "name",
            "traffic"
        ]
    }

    # the following line is the encrypted text for the previous variable USERS_LIST_FORM I've saved it because always using the same variable
    USERS_LIST_PAYLOAD = {
        "payload": "U2FsdGVkX18u4Wc0KakRLpCjcuj/exM+Iq/BUUoujFitfyaeJzMpJGk3iAcTHOQakFUbNAt4XsqJwXsfcPhUmkk7bMRuWNqeDzWNHZ/nYYdruCDFGj6ShXgUmr3To39bh78q1YX7vHYmd6K+3RBAcbSRvOFP3AGw5xw1/qpRRxX5GwJzvCzo3Svtac1nmF9pLqD/zQkmuFCnNTZx87EyA9LRuGCP4+goRsd0utVat4sQLKyZrSVq7uVR7tenW02EX7JnygWRwDMCIQpCQeJ1yJm11cFgmhwhTGTE5ZB3pps="
    }
    @api.model
    def get_companies_with_credentials(self):
        companies = self.env['res.company'].search([("url", "!=", False), ("username", "!=", False),("password", "!=", False)])
        result = []
        for company in companies:
            company_id = company['id']
            company_url = company['url']
            company_username = company['username']
            company_password = company['password']
            result.append((company_id, company_url, company_username, company_password))
        return result

    # BASE_URL = "https://reseller.alsabahtech.net"

    HEADERS = {'Content-Type': 'application/json'}


    @api.model
    def get_fat_fdt_from_nation_id(self, national_id):
        '''
        parameter: national_id:str - This parameter represents the national_id field from the sas-radius response
                    where I saw that the fdt, fat values are stored in it and splitted by delimiter
        return: fat:str, fdt:str - Those Valuse of each user

        - As I checked the FAT is always the firest part and the FDT the second
        '''
        fdt = ""
        fat = ""
        if national_id:
            delimiters = ['.', ',', '/', '-']
            for delimiter in delimiters:
                parts = national_id.split(delimiter)
                if len(parts) == 2:
                    fat, fdt = parts
                    break

        return fat, fdt

    @api.model
    def _login_to_sas_radius_server(self, base_url, username, password):
        '''
        return: Bearer Token:str - a token used for authorization at SAS Radius API
        - encrypt the TOKNE_FORM before sending the data
        - save the token inside ir.config_parameter so it can be used later if it's still valid
        '''
        endpoint_url = "/admin/api/index.php/api/login"
        url = base_url + endpoint_url
        passphrase = "abcdefghijuklmno0123456789012345"
        token_from = {"username": username, "password": password, "language": "en"}

        encrypted_data = AESController.encrypt(json.dumps(token_from).encode('utf-8'), passphrase)
        payload = {
            "payload": encrypted_data
        }

        response = requests.post(url, json=payload, headers=self.HEADERS)
        try:
            token = response.json()['token']
            # the next line isn't used but I'm saving the token anyway
            # the saved token isn't used because I don't know when it expires
            self.env['ir.config_parameter'].sudo().set_param("sas_radius.token", token)
            return token
        except:
            raise UserError("Login to sas radius server failed !")

    def create_partner_obj_from_api_data(self, user_data, fat, fdt, company_id):
        partner_obj = {
            "name": (
                            (user_data.get('firstname', "") or "")
                            + " "
                            + (user_data.get('lastname', "") or "")
                    ).strip()
                    or user_data.get('username', ""),
            "street": user_data.get('street', ""),
            "street2": user_data.get('address', ""),
            "city": user_data.get('city', ""),
            "partner_latitude": user_data.get('gps_lat', 0.0),  # <-- use get(...)
            "partner_longitude": user_data.get('gps_lng', 0.0),  # <-- use get(...)
            "phone": user_data.get('phone', ""),
            "email": user_data.get('email', ""),
            "profile": user_data.get('profile_details', {}).get('name', ""),
            "username": user_data.get('username', ""),
            "owner": user_data.get('parent_username', ""),
            "fat": fat,
            "fdt": fdt,
            "expiration_date": user_data.get('expiration', False),
            "created_on_date": user_data.get('created_at', False),
            "sas_contract_id": user_data.get('contract_id', ""),
            "company_id": company_id,
        }
        return partner_obj

    @api.model
    def get_users_from_sas_radius_server(self, from_page=1, to_page=3):
        '''
        Parameter: from_page:int - this parameter is used to determine from which page to fetch
        Parameter: to_page:int - this parameter is used to determine until which page to fetch

        Retrun: Boolean:True - as a schedule action will return True if it's done successfully

        - in USERS_LIST_PAYLOAD I set the order as 'desc' which means when getting from page=1 to page=3
            we're fetching the latest 300 users which I guess the client won't register more than that each day
        - This function should be applied manually when it is applied on new database (empty) to fetch all users
            then it can work as schedule action
        '''
        companies_credentials = self.get_companies_with_credentials()
        for company_id, company_url, company_username, company_password in companies_credentials:
            # check token existence
            token = self._login_to_sas_radius_server(company_url,company_username, company_password)
            headers = self.HEADERS
            headers['Authorization'] = "Bearer " + token
            endpoint_url = "/admin/api/index.php/api/index/user?page={}"
            for page_num in range(from_page, to_page):
                url = company_url + endpoint_url.format(page_num)
                response = requests.post(url, json=self.USERS_LIST_PAYLOAD, headers=headers)
                print('fetching users response: ', response , company_id)
                users = response.json()['data']
                sas_radius_users = []
                sas_radius_partners = []
                for user in users:
                    print(user['firstname'],' id: ', user['id'])
                    sas_radius_user = self.env['sas.radius.user'].search([('user_sas_radius_id', '=', user['id']), ('company_id', '=', company_id)], limit=1)
                    print(sas_radius_user.partner)
                    if not sas_radius_user:
                        print('not sas')
                        # this should be a function
                        sas_radius_users.append({'user_sas_radius_id': user['id']})
                        national_id = user['national_id']
                        fat, fdt = self.get_fat_fdt_from_nation_id(national_id)
                        partner_obj = self.create_partner_obj_from_api_data(user, fat, fdt, company_id)
                        sas_radius_partners.append(partner_obj)
                partners = self.env['res.partner'].create(sas_radius_partners)
                for i in range(len(partners)):
                    sas_radius_users[i].update({'partner': partners[i].id,
                                                'company_id': company_id})
                self.create(sas_radius_users)
        return True

    @api.model
    # def get_contract_id_for_users(self, from_page=1, to_page=3):
    #     '''
    #     This function is similar to the previous one but use to fetch contract_id for our current users after
    #         we've already fetched them
    #     '''
    #     token = self._login_to_sas_radius_server()
    #     headers = self.HEADERS
    #     headers['Authorization'] = "Bearer " + token
    #     endpoint_url = "/admin/api/index.php/api/index/user?page={}"
    #     for page_num in range(from_page, to_page):
    #         url = self.BASE_URL + endpoint_url.format(page_num)
    #         response = requests.post(url, json=self.USERS_LIST_PAYLOAD, headers=headers)
    #         users = response.json()['data']
    #         for user in users:
    #             sas_radius_user = self.env['sas.radius.user'].search([('user_sas_radius_id', '=', user['id'])], limit=1)
    #             if sas_radius_user:
    #                 # this should be a function
    #                 sas_radius_user.partner.write({'sas_contract_id': user['contract_id'] if user['contract_id'] else ""})
    #     return True

    def _get_mac_for_specific_user(self, token, base_url):
        '''
        This function is used to fetch the mac_address for a specific user from it's sas_radius_id
        '''
        headers = self.HEADERS
        headers['Authorization'] = "Bearer " + token

        endpoint_url = "/admin/api/index.php/api/mac/{}"
        url = base_url + endpoint_url.format(self.user_sas_radius_id)
        try:
            response = requests.get(url, headers=headers)
            if response.json()['data']:
                mac = response.json()['data'][0]['mac']
                partner = self.partner
                partner.write({'mac_address': mac})
                self.write({'mac_added': True})
        except:
            raise UserError("Something Bad Happened!")

    def get_from_to_parameters(self, from_parameter_name, to_parameter_name, from_to_range):
        '''
        Parameter: from_parameter_name:str - the name of the 'from' ir.config_parameter need to get and set
        Parameter: to_paramter_name:str - the name of the 'to' ir.config_parameter need to get and set
        Paramter: from_to_range:int - the range determined between 'from', 'to'

        return: from_user:int - the saved from_user value
        return: to_user:int - the saved to_user value

        - if from_user is 0 so it's the first time
        - if to_user larger than the length of our sas radius users then set the to_user value as
            length of sas radius users
        '''
        all_users = self.search([])
        len_all_users = len(all_users)

        from_user = int(self.env['ir.config_parameter'].sudo().get_param(from_parameter_name, 0))
        to_user = int(self.env['ir.config_parameter'].sudo().get_param(to_parameter_name, from_to_range))

        if from_user == 0:
            self.env['ir.config_parameter'].sudo().set_param(from_parameter_name, 1)
            self.env['ir.config_parameter'].sudo().set_param(to_parameter_name, from_to_range)
        else:
            from_user = to_user
            to_user = from_user + from_to_range
            if to_user > len_all_users:
                to_user = len_all_users
                self.env['ir.config_parameter'].sudo().set_param(from_parameter_name, 0)
                self.env['ir.config_parameter'].sudo().set_param(to_parameter_name, from_to_range)
            else:
                self.env['ir.config_parameter'].sudo().set_param(from_parameter_name, from_user)
                self.env['ir.config_parameter'].sudo().set_param(to_parameter_name, to_user)

        return from_user, to_user
    @api.model
    def get_mac_for_each_user(self):
        '''
        return: Boolean:True - when it's done successfully

        - This function creates from_user_mac & to_user_mac so the function can work as schedule action that will
            fetch 100 users every one hour
        - This function uses _get_mac_for_specific_user where this function calls and Endpoint to get the mac for a user
            and to save mac value
        - As a function time limit this function couldn't be fired with more than 200 range of users on client server
            On Odoosh I managed to set the range as 300 and if the Odoo shell used you can set the range you want
            if you're internet connection is stable
        - If the code causes unkown errors on client server try to reduce the 100 into 50 or 75 user per action
        - On Odoosh server this function took executing around 2 minutes
        '''
        from_user, to_user = self.get_from_to_parameters('sas.radius.user.from_user_mac', 'sas.radius.user.to_user_mac',
                                                         100)
        print('from_user: ', from_user, to_user)
        companies_credentials = self.get_companies_with_credentials()
        for company_id, company_url, company_username, company_password in companies_credentials:
            # check token existence
            token = self._login_to_sas_radius_server(company_url, company_username, company_password)
            users = self.search([], order="id desc")[from_user:to_user]
            print('users: ', users)
            for user in users:
                print(user.id ,'mac_: ', user.mac_added)
                if not user.mac_added:
                    user._get_mac_for_specific_user(token, company_url)
        return True

    def update_user_data(self, token, base_url, company_id):
        '''
        This function is used to update specific user data from SAS Radius API

        - set token parameter to False in case this function has been called from the UI button and not from
            the schedule action
        '''
        headers = self.HEADERS
        headers['Authorization'] = "Bearer " + token
        endpoint_url = "/admin/api/index.php/api/user/{}"
        print('user: ',self.user_sas_radius_id)
        url = base_url + endpoint_url.format(self.user_sas_radius_id)
        try:
            response = requests.get(url, headers=headers)
            print('response: ', response)
            user_data = response.json()['data']
            date_format = "%Y-%m-%d %H:%M:%S"
            datetime_object = datetime.strptime(user_data['updated_at'], date_format)
            if datetime_object > self.user_sas_updated_at:
                fat, fdt = self.get_fat_fdt_from_nation_id(user_data['national_id'])
                partner_obj = self.create_partner_obj_from_api_data(user_data, fat, fdt, company_id)
                # I should fire the mac api endpoint here
                self._get_mac_for_specific_user(token, base_url)
                partner = self.partner
                partner.write(partner_obj)
        except:
            raise UserError("Something Bad Happened!")

    @api.model
    def update_users_data(self):
        '''
        - This function is used as a schedule action to update users data
        - On Odoosh this function took executing around 3 minutes
        '''

        from_user, to_user = self.get_from_to_parameters('sas.radius.user.from_user_update',
                                                         'sas.radius.user.to_user_update', 50)

        companies_credentials = self.get_companies_with_credentials()
        print(companies_credentials)
        for company_id, company_url, company_username, company_password in companies_credentials:
            token = self._login_to_sas_radius_server(company_url, company_username, company_password)
            users = self.search([])[from_user:to_user]
            for user in users:
                try:
                    user.update_user_data(token, company_url, company_id)
                    print('ok')
                except Exception as e:
                    print(f"Error processing user {user.id}: {e}")
                    continue  # Move to the next user
        return True

