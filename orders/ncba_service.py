"""
NCBA Till STK Push & Dynamic QR Code API Integration Service
"""
import requests
import base64
import logging
import json
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class NCBAService:
    """
    Service class for interacting with NCBA Till API
    Supports: STK Push and Dynamic QR Code generation
    """
    
    def __init__(self):
        self.base_url = "https://c2bapis.ncbagroup.com"
        self.username = getattr(settings, 'NCBA_USERNAME', '')
        self.password = getattr(settings, 'NCBA_PASSWORD', '')
        self.paybill_no = getattr(settings, 'NCBA_PAYBILL_NO', '880100')
        self.till_no = getattr(settings, 'NCBA_TILL_NO', '')
        self.default_transaction_type = getattr(settings, 'NCBA_TRANSACTION_TYPE', 'CustomerPayBillOnline')
        self.use_till_as_account = getattr(settings, 'NCBA_USE_TILL_AS_ACCOUNT', False)
        self.callback_url = getattr(settings, 'NCBA_CALLBACK_URL', '')
        self.timeout = 30 # 30 seconds timeout for API calls

    def get_access_token(self):
        """
        Retrieve an authorization token
        """
        cache_key = 'ncba_access_token'
        token = cache.get(cache_key)
        
        if token:
            logger.info("Using cached NCBA access token")
            return token
            
        try:
            url = f"{self.base_url}/payments/api/v1/auth/token"
            logger.info(f"Fetching NCBA access token from {url}")
            
            # Basic Auth
            auth_string = f"{self.username}:{self.password}"
            auth_bytes = auth_string.encode('ascii')
            auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_base64}'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            logger.info(f"NCBA token response status: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            token = result.get('access_token')
            expires_in = result.get('expires_in', 18000)
            
            if token:
                logger.info("NCBA access token obtained successfully")
                # Cache token, subtracting a small buffer
                cache.set(cache_key, token, expires_in - 60)
                return token
            else:
                logger.error(f"No access token in NCBA response: {result}")
                raise Exception("No access token in NCBA response")
                
        except requests.exceptions.Timeout:
            logger.error("NCBA token request timed out")
            raise Exception("NCBA authentication timed out")
        except Exception as e:
            logger.error(f"Failed to get NCBA access token: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response content: {e.response.text}")
            raise Exception(f"NCBA authentication failed: {str(e)}")

    def initiate_stk_push(self, phone_number, amount, account_no, transaction_type=None, paybill_no=None, network="Safaricom"):
        """
        Initiate a SIM Toolkit (STK) push transaction.
        """
        try:
            logger.info(f"Getting access token for STK push to {phone_number}")
            access_token = self.get_access_token()
            url = f"{self.base_url}/payments/api/v1/stk-push/initiate"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Use provided or default transaction type
            tx_type = transaction_type or self.default_transaction_type
            
            # Use provided or default paybill number
            pb_no = paybill_no or self.paybill_no
            
            # Special handling for Buy Goods: PayBillNo must be the Till No
            if tx_type == "CustomerBuyGoodsOnline" and not paybill_no:
                pb_no = self.till_no
            
            # Special handling for Till as Account (the working configuration)
            acc_no = account_no
            if self.use_till_as_account:
                acc_no = self.till_no
                
            payload = {
                "TelephoneNo": phone_number,
                "Amount": str(amount),
                "PayBillNo": pb_no,
                "AccountNo": acc_no,
                "Network": network,
                "TransactionType": tx_type
            }
            
            # Add CallbackURL if available
            if self.callback_url:
                payload["CallBackURL"] = self.callback_url
            
            logger.info(f"Initiating NCBA STK Push: URL={url}, Type={tx_type}, Phone={phone_number}, Amount={amount}, PayBill={pb_no}, Account={acc_no}")
            logger.info(f"NCBA STK Push Payload: {json.dumps(payload)}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            logger.info(f"NCBA STK Push response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"NCBA STK Push result: {json.dumps(result)}")
            
            # Standardize success flag
            status_code = str(result.get('StatusCode', ''))
            if status_code == '0':
                result['success'] = True
            else:
                result['success'] = False
                result['error'] = result.get('StatusDescription', f'Unknown error (Code: {status_code})')
                
            return result
            
        except requests.exceptions.Timeout:
            logger.error("NCBA STK push request timed out")
            raise Exception("NCBA STK push timed out")
        except Exception as e:
            logger.error(f"NCBA STK Push failed: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response content: {e.response.text}")
            raise Exception(f"Failed to initiate NCBA payment: {str(e)}")

    def stk_query(self, transaction_id):
        """
        Query the status of a previous STK push transaction.
        """
        try:
            access_token = self.get_access_token()
            url = f"{self.base_url}/payments/api/v1/stk-push/query"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "TransactionID": transaction_id
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"NCBA STK Query failed: {str(e)}")
            raise Exception(f"Failed to query NCBA transaction status: {str(e)}")

    def generate_qr(self, amount=None, narration=None):
        """
        Generate a payment base 64 QR code image
        """
        try:
            access_token = self.get_access_token()
            url = f"{self.base_url}/payments/api/v1/qr/generate"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            till_value = self.till_no
            if narration:
                till_value = f"{self.till_no}#{narration}"
                
            payload = {
                "till": till_value
            }
            
            if amount:
                payload["amount"] = float(amount)
                
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"NCBA QR Generation failed: {str(e)}")
            raise Exception(f"Failed to generate NCBA QR code: {str(e)}")
