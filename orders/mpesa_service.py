"""
M-Pesa Daraja API Integration Service
Handles all M-Pesa payment operations including STK Push, C2B, B2C, and B2B
"""
import requests
import base64
import json
import logging
from datetime import datetime
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class MpesaDarajaService:
    """
    Service class for interacting with Safaricom Daraja API
    Supports: STK Push, C2B, B2C, B2B transactions
    """
    
    def __init__(self):
        # API Credentials
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.shortcode = getattr(settings, 'MPESA_SHORTCODE', '')
        self.passkey = getattr(settings, 'MPESA_PASSKEY', '')
        self.partyb_shortcode = getattr(settings, 'MPESA_PARTYB_SHORTCODE', '')
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
        
        # B2C Configuration
        self.b2c_shortcode = getattr(settings, 'MPESA_B2C_SHORTCODE', '')
        self.b2c_initiator_name = getattr(settings, 'MPESA_B2C_INITIATOR_NAME', '')
        self.b2c_security_credential = getattr(settings, 'MPESA_B2C_SECURITY_CREDENTIAL', '')
        
        # API URLs
        if self.environment == 'sandbox':
            self.base_url = 'https://sandbox.safaricom.co.ke'
        else:
            self.base_url = 'https://api.safaricom.co.ke'
        
        # Callback URLs
        self.stk_callback_url = getattr(settings, 'MPESA_STK_CALLBACK_URL', '')
        self.c2b_validation_url = getattr(settings, 'MPESA_C2B_VALIDATION_URL', '')
        self.c2b_confirmation_url = getattr(settings, 'MPESA_C2B_CONFIRMATION_URL', '')
        self.b2c_result_url = getattr(settings, 'MPESA_B2C_RESULT_URL', '')
        self.b2c_timeout_url = getattr(settings, 'MPESA_B2C_TIMEOUT_URL', '')
        # Optional preflight validation of callback URLs (enabled by default)
        self.validate_callback_url = getattr(settings, 'MPESA_VALIDATE_CALLBACK_URL', True)
    
    def get_access_token(self):
        """
        Generate OAuth access token for Daraja API
        Token is cached for 55 minutes (expires in 60 minutes)
        """
        cache_key = 'mpesa_access_token'
        token = cache.get(cache_key)
        
        if token:
            logger.info("Using cached M-Pesa access token")
            return token
        
        try:
            url = f'{self.base_url}/oauth/v1/generate?grant_type=client_credentials'
            
            # Create basic auth header
            auth_string = f'{self.consumer_key}:{self.consumer_secret}'
            auth_bytes = auth_string.encode('ascii')
            auth_base64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_base64}'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            token = result.get('access_token')
            
            if token:
                # Cache token for 55 minutes (expires in 60)
                cache.set(cache_key, token, 3300)
                logger.info("Generated new M-Pesa access token")
                return token
            else:
                raise Exception("No access token in response")
                
        except Exception as e:
            logger.error(f"Failed to get M-Pesa access token: {str(e)}")
            raise Exception(f"M-Pesa authentication failed: {str(e)}")
    
    def generate_password(self, timestamp):
        """
        Generate password for STK Push
        Password = Base64(Shortcode + Passkey + Timestamp)
        """
        data_to_encode = f'{self.shortcode}{self.passkey}{timestamp}'
        encoded = base64.b64encode(data_to_encode.encode()).decode('utf-8')
        return encoded
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url=None):
        """
        Initiate STK Push (Lipa Na M-Pesa Online)
        
        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge
            account_reference: Reference for the transaction (e.g., Order ID)
            transaction_desc: Description of the transaction
            callback_url: Optional callback URL override for this request
            
        Returns:
            dict: Response from Daraja API
        """
        try:
            # Format phone number
            phone_number = self.format_phone_number(phone_number)
            
            # Generate timestamp and password
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            
            # Get access token
            access_token = self.get_access_token()
            
            # Prepare request
            url = f'{self.base_url}/mpesa/stkpush/v1/processrequest'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerBuyGoodsOnline',
                'Amount': int(amount),
                'PartyA': phone_number,
                'PartyB': self.partyb_shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': callback_url or self.stk_callback_url,
                'AccountReference': account_reference,
                'TransactionDesc': transaction_desc
            }

            # Optional preflight: validate callback URL is reachable and returns 2xx
            if self.validate_callback_url:
                cb = callback_url or self.stk_callback_url
                try:
                    # Use HEAD first to avoid creating side-effects; fallback to POST if HEAD not allowed
                    resp = requests.head(cb, allow_redirects=True, timeout=6)
                    status = resp.status_code
                    # Some endpoints may not allow HEAD; if status code indicates method not allowed, try POST ping
                    if status >= 400 and status != 405:
                        # try a lightweight POST ping
                        resp = requests.post(cb, json={"ping": 1}, timeout=6)
                        status = resp.status_code
                    if status < 200 or status >= 300:
                        logger.error(f"Callback URL preflight failed: {cb} status={status} body={getattr(resp, 'text', '')}")
                        raise Exception(f"Callback URL validation failed: {cb} returned status {status}")
                except requests.exceptions.SSLError as ssl_err:
                    logger.error(f"TLS/SSL error validating callback URL {cb}: {ssl_err}")
                    raise Exception(f"Callback URL TLS/SSL validation failed: {ssl_err}")
                except requests.exceptions.RequestException as req_err:
                    logger.error(f"Connection error validating callback URL {cb}: {req_err}")
                    raise Exception(f"Callback URL connection failed: {req_err}")
            
            logger.info(
                f"Initiating STK Push: Phone={phone_number}, Amount={amount}, Ref={account_reference}, Callback={payload['CallBackURL']}"
            )
            
            response = requests.post(url, json=payload, headers=headers)
            # Ensure HTTP errors surface and capture non-JSON responses
            try:
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.HTTPError as http_err:
                body = getattr(response, 'text', '<no body>')
                logger.error(f"HTTP error during STK Push: {http_err} - status={response.status_code} body={body}")
                raise Exception(f"M-Pesa STK Push HTTP error: {http_err} - {body}")
            except ValueError:
                # JSON decoding failed
                body = getattr(response, 'text', '<no body>')
                logger.error(f"Non-JSON response during STK Push - status={response.status_code} body={body}")
                raise Exception(f"M-Pesa STK Push returned non-JSON response: status={response.status_code} body={body}")

            logger.info(f"STK Push response: {json.dumps(result, indent=2)}")
            
            # Add success flag based on ResponseCode
            if result.get('ResponseCode') == '0':
                result['success'] = True
            else:
                result['success'] = False
                result['error'] = result.get('ResponseDescription', 'Unknown error')
            
            return result
            
        except Exception as e:
            logger.error(f"STK Push failed: {str(e)}")
            raise Exception(f"Failed to initiate M-Pesa payment: {str(e)}")
    
    def stk_query(self, checkout_request_id):
        """
        Query STK Push transaction status
        
        Args:
            checkout_request_id: CheckoutRequestID from STK Push response
            
        Returns:
            dict: Transaction status
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = self.generate_password(timestamp)
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/stkpushquery/v1/query'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'BusinessShortCode': self.shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': checkout_request_id
            }
            
            response = requests.post(url, json=payload, headers=headers)
            # Ensure HTTP errors surface and capture non-JSON responses
            try:
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.HTTPError as http_err:
                body = getattr(response, 'text', '<no body>')
                logger.error(f"HTTP error during STK Query: {http_err} - status={response.status_code} body={body}")
                raise Exception(f"M-Pesa STK Query HTTP error: {http_err} - {body}")
            except ValueError:
                body = getattr(response, 'text', '<no body>')
                logger.error(f"Non-JSON response during STK Query - status={response.status_code} body={body}")
                raise Exception(f"M-Pesa STK Query returned non-JSON response: status={response.status_code} body={body}")

            logger.info(f"STK Query response: {json.dumps(result, indent=2)}")

            return result
            
        except Exception as e:
            logger.error(f"STK Query failed: {str(e)}")
            raise Exception(f"Failed to query transaction status: {str(e)}")
    
    def register_c2b_urls(self):
        """
        Register C2B validation and confirmation URLs
        This should be called once during setup
        """
        try:
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/c2b/v1/registerurl'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'ShortCode': self.shortcode,
                'ResponseType': 'Completed',  # or 'Cancelled'
                'ConfirmationURL': self.c2b_confirmation_url,
                'ValidationURL': self.c2b_validation_url
            }
            
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(f"C2B URL registration response: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"C2B URL registration failed: {str(e)}")
            raise Exception(f"Failed to register C2B URLs: {str(e)}")
    
    def b2c_payment(self, phone_number, amount, occasion, remarks):
        """
        Initiate B2C payment (Business to Customer)
        Used for payouts to assistants/handlers
        
        Args:
            phone_number: Recipient phone number (format: 254XXXXXXXXX)
            amount: Amount to send
            occasion: Occasion for the payment
            remarks: Additional remarks
            
        Returns:
            dict: Response from Daraja API
        """
        try:
            phone_number = self.format_phone_number(phone_number)
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/b2c/v1/paymentrequest'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'InitiatorName': self.b2c_initiator_name,
                'SecurityCredential': self.b2c_security_credential,
                'CommandID': 'BusinessPayment',  # or 'SalaryPayment', 'PromotionPayment'
                'Amount': int(amount),
                'PartyA': self.b2c_shortcode,
                'PartyB': phone_number,
                'Remarks': remarks,
                'QueueTimeOutURL': self.b2c_timeout_url,
                'ResultURL': self.b2c_result_url,
                'Occasion': occasion
            }
            
            logger.info(f"Initiating B2C payment: Phone={phone_number}, Amount={amount}")
            
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(f"B2C payment response: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"B2C payment failed: {str(e)}")
            raise Exception(f"Failed to initiate B2C payment: {str(e)}")
    
    def transaction_status(self, transaction_id):
        """
        Query transaction status
        
        Args:
            transaction_id: M-Pesa transaction ID
            
        Returns:
            dict: Transaction status
        """
        try:
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/transactionstatus/v1/query'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'Initiator': self.b2c_initiator_name,
                'SecurityCredential': self.b2c_security_credential,
                'CommandID': 'TransactionStatusQuery',
                'TransactionID': transaction_id,
                'PartyA': self.shortcode,
                'IdentifierType': '4',  # 4 for shortcode
                'ResultURL': self.b2c_result_url,
                'QueueTimeOutURL': self.b2c_timeout_url,
                'Remarks': 'Transaction status query',
                'Occasion': 'Status check'
            }
            
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(f"Transaction status response: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Transaction status query failed: {str(e)}")
            raise Exception(f"Failed to query transaction status: {str(e)}")
    
    def account_balance(self):
        """
        Query account balance
        
        Returns:
            dict: Account balance information
        """
        try:
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/accountbalance/v1/query'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'Initiator': self.b2c_initiator_name,
                'SecurityCredential': self.b2c_security_credential,
                'CommandID': 'AccountBalance',
                'PartyA': self.shortcode,
                'IdentifierType': '4',  # 4 for shortcode
                'Remarks': 'Account balance query',
                'QueueTimeOutURL': self.b2c_timeout_url,
                'ResultURL': self.b2c_result_url
            }
            
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(f"Account balance response: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Account balance query failed: {str(e)}")
            raise Exception(f"Failed to query account balance: {str(e)}")
    
    def reversal(self, transaction_id, amount, remarks):
        """
        Reverse a transaction
        
        Args:
            transaction_id: M-Pesa transaction ID to reverse
            amount: Amount to reverse
            remarks: Reason for reversal
            
        Returns:
            dict: Response from Daraja API
        """
        try:
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/reversal/v1/request'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'Initiator': self.b2c_initiator_name,
                'SecurityCredential': self.b2c_security_credential,
                'CommandID': 'TransactionReversal',
                'TransactionID': transaction_id,
                'Amount': int(amount),
                'ReceiverParty': self.shortcode,
                'RecieverIdentifierType': '4',  # 4 for shortcode
                'Remarks': remarks,
                'QueueTimeOutURL': self.b2c_timeout_url,
                'ResultURL': self.b2c_result_url
            }
            
            logger.info(f"Initiating reversal for transaction: {transaction_id}, Amount: {amount}")
            
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(f"Reversal response: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Reversal failed: {str(e)}")
            raise Exception(f"Failed to reverse transaction: {str(e)}")
    
    def generate_dynamic_qr(self, amount, ref_no, merchant_name):
        """
        Generate Dynamic QR Code for M-Pesa payment
        
        Args:
            amount: Amount to be paid
            ref_no: Reference number
            merchant_name: Name of the merchant
            
        Returns:
            dict: Response with QR code
        """
        try:
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/dynamicqrcode/v1/generate'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'Amount': int(amount),
                'CurrCode': 'KES',
                'MerchantName': merchant_name,
                'RefNo': ref_no,
                'TrxCode': 'BG'  # Buy Goods
            }
            
            logger.info(f"Generating dynamic QR code: Amount={amount}, Ref={ref_no}")
            
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(f"Dynamic QR code response: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Dynamic QR code generation failed: {str(e)}")
            raise Exception(f"Failed to generate Dynamic QR code: {str(e)}")
    
    def b2b_payment(self, receiver_shortcode, amount, account_reference, remarks, identifier_type='4'):
        """
        Initiate B2B payment (Business to Business)
        
        Args:
            receiver_shortcode: Receiver business shortcode
            amount: Amount to send
            account_reference: Account reference for the transaction
            remarks: Transaction remarks
            identifier_type: Identifier type (4=shortcode, 2=till, 1=MSISDN)
            
        Returns:
            dict: Response from Daraja API
        """
        try:
            access_token = self.get_access_token()
            
            url = f'{self.base_url}/mpesa/b2b/v1/paymentrequest'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'Initiator': self.b2c_initiator_name,
                'SecurityCredential': self.b2c_security_credential,
                'CommandID': 'BusinessPayBill',  # or 'MerchantToMerchantTransfer'
                'SenderIdentifierType': '4',  # 4 for shortcode
                'RecieverIdentifierType': identifier_type,
                'Amount': int(amount),
                'PartyA': self.shortcode,
                'PartyB': receiver_shortcode,
                'AccountReference': account_reference,
                'Remarks': remarks,
                'QueueTimeOutURL': self.b2c_timeout_url,
                'ResultURL': self.b2c_result_url
            }
            
            logger.info(f"Initiating B2B payment: To={receiver_shortcode}, Amount={amount}, Ref={account_reference}")
            
            response = requests.post(url, json=payload, headers=headers)
            result = response.json()
            
            logger.info(f"B2B payment response: {json.dumps(result, indent=2)}")
            
            return result
            
        except Exception as e:
            logger.error(f"B2B payment failed: {str(e)}")
            raise Exception(f"Failed to initiate B2B payment: {str(e)}")
    
    @staticmethod
    def format_phone_number(phone_number):
        """
        Format phone number to 254XXXXXXXXX format
        
        Args:
            phone_number: Phone number in various formats
            
        Returns:
            str: Formatted phone number
        """
        # Remove any spaces, dashes, or plus signs
        phone_number = str(phone_number).replace(' ', '').replace('-', '').replace('+', '')
        
        # Remove leading zero if present
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        # Add 254 if not present
        if not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        return phone_number
    
    @staticmethod
    def validate_phone_number(phone_number):
        """
        Validate Kenyan phone number
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        formatted = MpesaDarajaService.format_phone_number(phone_number)
        
        # Check if it's 12 digits starting with 254
        if len(formatted) != 12 or not formatted.startswith('254'):
            return False
        
        # Check if all characters are digits
        if not formatted.isdigit():
            return False
        
        # Check if it's a valid Kenyan mobile number (starts with 2547 or 2541)
        if not (formatted.startswith('2547') or formatted.startswith('2541')):
            return False
        
        return True


# Create singleton instance
mpesa_service = MpesaDarajaService()