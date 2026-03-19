import base64
import hmac
import hashlib
import requests
import json
import random
from datetime import datetime, timedelta
from urllib3.exceptions import InsecureRequestWarning

# Disable insecure request warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def create_paytr_link(
        merchant_id,
        merchant_key,
        merchant_salt,
        name,
        price,
        callback_link,
        callback_id,
        link_type='product',
        currency='TL',
        max_installment='12',
        lang='tr',
        get_qr=1,
        debug_on=1,
        proxy=None,
        expiry_hours=24
):
    # Prepare required fields
    required = name + price + currency + max_installment + link_type + lang

    # Handle link type specific fields
    if link_type == 'product':
        min_count = '1'
        email = ''
        required += min_count
    elif link_type == 'collection':
        min_count = ''
        email = f'{random.randint(1, 9999999)}@example.com'
        required += email
    else:
        return {
            'success': False,
            'error': 'Invalid link_type. Must be "product" or "collection"'
        }

    # Prepare expiry date
    expiry_date = (datetime.now() + timedelta(hours=expiry_hours)).strftime('%Y-%m-%d %H:%M:%S')
    max_count = '1'

    # Generate token
    hash_str = required + merchant_salt
    paytr_token = base64.b64encode(
        hmac.new(merchant_key.encode('utf-8'), hash_str.encode('utf-8'), hashlib.sha256).digest()
    ).decode('utf-8')

    # Prepare request params
    params = {
        'merchant_id': merchant_id,
        'name': name,
        'price': price,
        'currency': currency,
        'max_installment': max_installment,
        'link_type': link_type,
        'lang': lang,
        'min_count': min_count,
        'email': email,
        'expiry_date': expiry_date,
        'max_count': max_count,
        'callback_link': callback_link,
        'callback_id': callback_id,
        'debug_on': debug_on,
        'get_qr': get_qr,
        'paytr_token': paytr_token,
    }

    # Configure session
    session = requests.Session()
    if proxy:
        session.proxies = proxy
    session.verify = False

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9',
    }

    try:
        response = session.post(
            'https://www.paytr.com/odeme/api/link/create',
            data=params,
            headers=headers,
            timeout=30
        )

        # Check for access restrictions
        if "Access Restricted" in response.text:
            return {
                'success': False,
                'error': 'Access restricted. Check proxy or merchant credentials.',
                'response': response.text
            }

        try:
            res = response.json()
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid JSON response from server',
                'response': response.text
            }

        if res.get('status') == 'error':
            return {
                'success': False,
                'error': res.get('err_msg', 'Unknown error'),
                'response': res
            }
        elif res.get('status') == 'failed':
            return {
                'success': False,
                'error': res.get('reason', 'Unknown failure reason'),
                'response': res
            }
        elif res.get('status') == 'success':
            return {
                'success': True,
                'link': res.get('link'),
                'response': res
            }

        return {
            'success': False,
            'error': 'Unknown response status',
            'response': res
        }

    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}',
            'exception': e
        }


# Example usage
if __name__ == "__main__":
    # Proxy configuration (optional)
    PROXY = {
        'http': 'http://9Nk2C1:PpTaMN@200.10.40.102:9720',
        'https': 'http://9Nk2C1:PpTaMN@200.10.40.102:9720'
    }

    # Create payment link
    result = create_paytr_link(
        merchant_id="581361",
        merchant_key="jAJ5fSA1ZjA4pK8p",
        merchant_salt="BK69wSxFiLjnUgq8",
        name="Test Product",
        price="1000",  # 10.00 TL
        callback_link="https://yourdomain.com/paytr/callback",
        callback_id="order123",
        link_type="product",
        proxy=PROXY
    )

    if result['success']:
        print("Payment link created successfully:")
        print(result['link'])
    else:
        print("Error creating payment link:")
        print(result['error'])
        if 'response' in result:
            print("Full response:")
            print(json.dumps(result['response'], indent=2))