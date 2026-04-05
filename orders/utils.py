from django.conf import settings
from intasend import APIService

def get_intasend_api():
    """Get an instance of the IntaSend API service"""
    return APIService(
        settings.INTASEND_SECRET_KEY,
        settings.INTASEND_PUBLISHABLE_KEY,
        settings.INTASEND_TEST_MODE
    )