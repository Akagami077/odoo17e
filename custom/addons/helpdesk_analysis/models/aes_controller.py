from Crypto.Random import get_random_bytes
import base64
from hashlib import md5
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
import json


'''
    This file have been used to encrypt request before sending them to sas radius API
'''
class AESController:

    @staticmethod
    def evpkdf(passphrase, salt):
        salted = b''
        dx = b''
        while len(salted) < 48:
            dx = md5(dx + passphrase.encode('utf-8') + salt).digest()
            salted += dx
        key = salted[:32]
        iv = salted[32:48]
        return key, iv

    @staticmethod
    def encode(ct, salt):
        return base64.b64encode(b"Salted__" + salt + ct).decode('utf-8')

    @staticmethod
    def encrypt(data, passphrase, salt=None):
        padded_data = pad(data, AES.block_size)
        salt = salt or get_random_bytes(8)
        key, iv = AESController.evpkdf(passphrase, salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ct = cipher.encrypt(padded_data)
        return AESController.encode(ct, salt)

