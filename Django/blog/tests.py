import base64
import hashlib
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..apps.models import Order, Merchant, Transaction

User = get_user_model()

class PaymentWebhookTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123', phone_number='+998901234567')
        self.order = Order.objects.create(user=self.user, amount=15000.00) # 15,000 so'm
        
        # Provayder sozlamalari
        self.payme_merchant = Merchant.objects.create(
            name='Payme Test', provider='PAYME', merchant_id='m_123', secret_key='supersecret_payme', is_active=True
        )
        self.click_merchant = Merchant.objects.create(
            name='Click Test', provider='CLICK', merchant_id='c_123', secret_key='supersecret_click', is_active=True
        )

    def test_payme_check_perform_transaction(self):
        auth_str = base64.b64encode(b"Paycom:supersecret_payme").decode('utf-8')
        payload = {
            "method": "CheckPerformTransaction",
            "params": {
                "amount": 1500000, # tiyinda
                "account": {"order_id": str(self.order.id)}
            }
        }
        response = self.client.post(
            '/api/payment/webhook/payme/', 
            data=payload, 
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Basic {auth_str}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', response.json())
        self.assertTrue(response.json()['result']['allow'])

    def test_click_prepare_webhook(self):
        # click_trans_id + service_id + secret_key + merchant_trans_id + amount + action + sign_time
        click_trans_id = "9999"
        service_id = "5555"
        secret_key = "supersecret_click"
        merchant_trans_id = str(self.order.id)
        amount = "15000.0"
        action = "0"
        sign_time = "2026-01-01 12:00:00"
        
        sign_str = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
        signature = hashlib.md5(sign_str.encode()).hexdigest()

        payload = {
            "click_trans_id": click_trans_id,
            "service_id": service_id,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "action": action,
            "sign_time": sign_time,
            "sign_string": signature
        }

        response = self.client.post(
            '/api/payment/webhook/click/',
            data=payload,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['error'], "0")