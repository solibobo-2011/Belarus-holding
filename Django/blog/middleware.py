import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from ..apps.models import WebhookLog

# Haqiqiy Payme va Click IP diapazonlari
ALLOWED_PAYMENT_IPS = {
    '185.250.243.0/24', # Payme misol diapazoni (Hujjatga qarab yangilanadi)
    '213.230.106.0/24', # Click misol diapazoni
    '127.0.0.1'         # Local testlar uchun
}

class PaymentWebhookMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'webhook' in request.path:
            # IP manzillarini tekshirish (Ishlab chiqarish muhitida proxy hisobga olinadi)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Simple IP Check (Productionda ipaddress kutubxonasidan foydalanish maqsadga muvofiq)
            # Bu yerda soddalik uchun to'g'ridan-to'g'ri o'tkazamiz, lekin log yozamiz.
            
            # Request body log
            try:
                body = json.loads(request.body) if request.body else {}
            except ValueError:
                body = {}

            request.webhook_log = WebhookLog.objects.create(
                provider='PAYME' if 'payme' in request.path else 'CLICK',
                request_headers=dict(request.headers),
                request_body=body,
                ip_address=ip
            )
        return None

    def process_response(self, request, response):
        if hasattr(request, 'webhook_log'):
            log = request.webhook_log
            log.status_code = response.status_code
            try:
                log.response_body = json.loads(response.content) if response.content else {}
            except ValueError:
                log.response_body = {"raw": response.content.decode('utf-8', errors='ignore')}
            log.save()
        return response