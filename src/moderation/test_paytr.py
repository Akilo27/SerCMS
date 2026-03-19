# Python 3.6+
import base64
import hmac
import hashlib
import requests
import json
import random

# API entegrasyon bilgileri
merchant_id = '581361'
merchant_key = b'jAJ5fSA1ZjA4pK8p'
merchant_salt = 'BK69wSxFiLjnUgq8'

# Ürün / hizmet bilgileri
name = 'Örnek Ürün / Hizmet Adı'
price = '1445'  # 14.45 TL
currency = 'TL'
max_installment = '12'
link_type = 'product'  # veya 'collection'
lang = 'tr'
get_qr = '1'

# Opsiyonel
expiry_date = '2025-12-31 23:59:00'
max_count = '1'
callback_link = ''
callback_id = ''
debug_on = '1'

# user_name и flex_max_price добавляем корректно
user_name = 'John Doe'
flex_max_price = '2000'

# email и min_count подставляются в зависимости от link_type
email = ''
min_count = ''
required = name + price + currency + max_installment + link_type + lang

if link_type == 'product':
    min_count = '1'
    required += min_count
elif link_type == 'collection':
    email = f"{random.randint(1,9999999)}@example.com"
    required += email

# Hash oluşturma
hash_str = required + merchant_salt
paytr_token = base64.b64encode(
    hmac.new(merchant_key, hash_str.encode(), hashlib.sha256).digest()
).decode()  # decode обязательно!

# Tüm parametreler
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
    'user_name': user_name,
    'flex_max_price': flex_max_price
}

# İsteği gönder
result = requests.post('https://www.paytr.com/odeme/api/link/create', data=params)
res = result.json()

# Yanıtı yazdır
if res['status'] == 'error':
    print('Error: ' + res.get('err_msg', 'Bilinmeyen hata'))
elif res['status'] == 'failed':
    print('Failed:', json.dumps(res, indent=4, ensure_ascii=False))
else:
    print('Success:', json.dumps(res, indent=4, ensure_ascii=False))
