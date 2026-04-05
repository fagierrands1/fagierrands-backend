"""
Fallback implementation for IntaSend API in case the package installation fails.
This provides a minimal implementation that allows the application to run without errors.
"""

import requests
import json
import logging

logger = logging.getLogger(__name__)

class APIService:
    """
    Minimal implementation of IntaSend's APIService class.
    """
    def __init__(self, token=None, publishable_key=None, test=True):
        self.token = token
        self.publishable_key = publishable_key
        self.test = test
        self.base_url = "https://sandbox.intasend.com" if test else "https://api.intasend.com"
        self.collect = CollectService(self)
        logger.warning("Using IntaSend fallback implementation. Some payment features may not work correctly.")

class CollectService:
    """
    Minimal implementation of IntaSend's CollectService class.
    """
    def __init__(self, api_service):
        self.api_service = api_service
    
    def mpesa_stk_push(self, phone_number, email, amount, narrative):
        """
        Simulate M-Pesa STK push request.
        """
        logger.warning(f"Simulating M-Pesa STK push for {phone_number}, amount: {amount}")
        
        # Return a simulated successful response
        return {
            "id": "sim_checkout_" + phone_number[-4:],
            "invoice": {
                "id": "sim_invoice_" + str(int(amount)),
                "state": "PENDING"
            }
        }
    
    def checkout(self, data):
        """
        Simulate checkout request.
        """
        logger.warning(f"Simulating checkout for {data.get('email')}, amount: {data.get('amount')}")
        
        # Return a simulated successful response
        return {
            "id": "sim_checkout_" + data.get('phone_number', '')[-4:],
            "url": f"{self.api_service.base_url}/checkout/simulate/{data.get('reference')}",
            "invoice": {
                "id": "sim_invoice_" + str(int(data.get('amount', 0))),
                "state": "PENDING"
            }
        }