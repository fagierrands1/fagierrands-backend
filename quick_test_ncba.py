import requests
import base64
import json
import sys

# NCBA Credentials (from your previous message)
NCBA_USERNAME = "Errand@123"
NCBA_PASSWORD = "9Y7a24B5TNxxKimfnGz9MTbdn960JY57ASC/r6KOCQNnR220v52od6a2ajgEaipL"
NCBA_PAYBILL_NO = "880100"
NCBA_TILL_NO = "852054"
BASE_URL = "https://c2bapis.ncbagroup.com"

def get_access_token():
    print("Step 1: Getting Access Token...")
    url = f"{BASE_URL}/payments/api/v1/auth/token"
    auth_string = f"{NCBA_USERNAME}:{NCBA_PASSWORD}"
    auth_base64 = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    headers = {'Authorization': f'Basic {auth_base64}'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        result = response.json()
        token = result.get('access_token')
        if token:
            print("✓ Token obtained successfully.")
            return token
        else:
            print(f"✗ No token in response: {result}")
            return None
    except Exception as e:
        print(f"✗ Auth Error: {str(e)}")
        if hasattr(e, 'response') and (hasattr(e.response, 'text') if e.response else False):
            print(f"Response: {e.response.text}")
        return None

def initiate_stk_push(token, phone):
    print("\nSelect Transaction Type:")
    print("1. PayBill (Use 880100 with your Till as Account)")
    print("2. Buy Goods (Use your Till 852054 directly)")
    choice = input("Choice (1/2): ").strip()

    url = f"{BASE_URL}/payments/api/v1/stk-push/initiate"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Format phone to 254...
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone

    if choice == '2':
        print(f"Testing Buy Goods with Till: {NCBA_TILL_NO}")
        payload = {
            "TelephoneNo": phone,
            "Amount": "1",
            "PayBillNo": NCBA_TILL_NO,
            "AccountNo": NCBA_TILL_NO, # Often redundant but required by some gateways
            "Network": "Safaricom",
            "TransactionType": "CustomerBuyGoodsOnline"
        }
    else:
        print(f"Testing PayBill with 880100 and Account: {NCBA_TILL_NO}")
        payload = {
            "TelephoneNo": phone,
            "Amount": "1",
            "PayBillNo": NCBA_PAYBILL_NO,
            "AccountNo": NCBA_TILL_NO,
            "Network": "Safaricom",
            "TransactionType": "CustomerPayBillOnline"
        }
    
    print(f"\nStep 2: Initiating STK Push for {phone}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if result.get('StatusCode') == '0':
            print("\n✓ SUCCESS! Check your phone for the STK prompt.")
        else:
            print(f"\n✗ FAILED: {result.get('StatusDescription')}")
    except Exception as e:
        print(f"✗ STK Error: {str(e)}")
        if hasattr(e, 'response') and (hasattr(e.response, 'text') if e.response else False):
            print(f"Response: {e.response.text}")

if __name__ == "__main__":
    print("="*50)
    print("NCBA PRODUCTION STK PUSH TEST (STANDALONE)")
    print("="*50)
    
    token = get_access_token()
    if token:
        phone = input("\nEnter phone number (07...): ").strip()
        if phone:
            initiate_stk_push(token, phone)
        else:
            print("No phone number entered.")
