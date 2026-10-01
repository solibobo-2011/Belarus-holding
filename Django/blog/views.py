import base64
import hashlib
import rest_framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.db.models import Q
from django.apps import apps

# Modellarni xavfsiz yuklash
User = get_user_model()
Post = apps.get_model('apps', 'Post')
Category = apps.get_model('apps', 'Category')
Order = apps.get_model('apps', 'Order')
Payment = apps.get_model('apps', 'Payment')
Merchant = apps.get_model('apps', 'Merchant')

from blog.serializers import CreatePaymentSerializer, PaymentStatusSerializer
from blog.services import PaymeService, ClickService

# URL generatsiya qilish uchun umumiy yordamchi funksiya
def generate_pay_url(provider, merchant_id, order):
    pay_url = ""
    if provider == 'PAYME':
        amount_in_tiyin = int(float(order.amount) * 100)
        formatted_params = f"m={merchant_id};ac.order_id={order.id};a={amount_in_tiyin}"
        encoded_params = base64.b64encode(formatted_params.encode()).decode()
        pay_url = f"https://checkout.paycom.uz/{encoded_params}"
        
    elif provider == 'CLICK':
        service_id = getattr(settings, 'CLICK_SERVICE_ID', merchant_id)
        pay_url = (
            f"https://my.click.uz/services/pay?"
            f"service_id={service_id}&"
            f"merchant_id={merchant_id}&"
            f"amount={order.amount}&"
            f"transaction_param={order.id}"
        )
    return pay_url


class AnonymousOrderPaymentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 1. Frontenddan kelayotgan ma'lumotlarni olish
        product_name = request.data.get('product_name')
        amount = request.data.get('amount')
        provider = request.data.get('provider', 'PAYME').upper()

        if not amount or not product_name:
            return Response(
                {"detail": "Mahsulot nomi va narxi yuborilishi shart."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Avtomatik tarzda Order (Buyurtma) yaratish
        user = request.user if request.user.is_authenticated else User.objects.get_or_create(username='guest_user')[0]
        
        order = Order.objects.create(
            user=user,
            amount=amount,
            status='PENDING'
        )

        # 3. To'lov (Payment) obyektini yaratish
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            amount=order.amount,
            status='CREATED'
        )

        # 4. Merchant sozlamalarini tekshirish
        merchant = Merchant.objects.filter(provider=provider, is_active=True).first()
        if not merchant:
            return Response(
                {"detail": f"{provider} to'lov tizimi sozlamalari topilmadi."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        pay_url = generate_pay_url(provider, merchant.merchant_id, order)

        return Response({
            "payment_id": payment.id, 
            "order_id": order.id, 
            "pay_url": pay_url
        }, status=status.HTTP_201_CREATED)


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.all().order_by('-created_at')
        query = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category', '').strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            )
        if category:
            queryset = queryset.filter(category_id=category)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')

        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['query_string'] = query_params.urlencode()

        return context


class ProductListView(ListView):
    template_name = 'blog/product_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        return Post.objects.none()


def index(request):
    return render(request, 'blog/index.html')

def register(request):
    return render(request, 'register.html')

def user_login(request):
    return render(request, 'login.html')

def user_logout(request):
    auth_logout(request)
    return redirect('index')


class CreatePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # UUID xatoliklarini oldini olish uchun tekshiruv bilan olish
        try:
            order = get_object_or_404(Order, pk=serializer.validated_data['order_id'], user=request.user)
        except ValueError:
            return Response({"detail": "Noto'g'ri buyurtma ID formati."}, status=status.HTTP_400_BAD_REQUEST)
            
        provider = serializer.validated_data['provider']
        
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            amount=order.amount,
            status='CREATED'
        )
        
        merchant = Merchant.objects.filter(provider=provider, is_active=True).first()
        if not merchant:
            return Response(
                {"detail": f"{provider} merchant sozlamalari topilmadi."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pay_url = generate_pay_url(provider, merchant.merchant_id, order)

        return Response({"payment_id": payment.id, "pay_url": pay_url}, status=status.HTTP_201_CREATED)


class PaymeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def _authenticate(self, request):
        auth_header = request.headers.get('Authorization', request.headers.get('HTTP_AUTHORIZATION', ''))
        if not auth_header.startswith('Basic '):
            return False
        
        try:
            encoded_credentials = auth_header.split(' ')[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            username, password = decoded_credentials.split(':', 1)
            
            merchant = Merchant.objects.filter(provider='PAYME', is_active=True).first()
            if merchant and password == merchant.secret_key:
                return True
        except Exception:
            return False
        return False

    def post(self, request):
        if not self._authenticate(request):
            return Response({"error": {"code": -32504, "message": "Access denied"}}, status=status.HTTP_200_OK)

        method = request.data.get('method')
        params = request.data.get('params', {})
        rpc_id = request.data.get('id')

        methods_map = {
            'CheckPerformTransaction': PaymeService.check_perform_transaction,
            'CreateTransaction': PaymeService.create_transaction,
            'PerformTransaction': PaymeService.perform_transaction,
            'CancelTransaction': PaymeService.cancel_transaction,
            'CheckTransaction': PaymeService.check_transaction,
        }

        if method not in methods_map:
            return Response({"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32601, "message": "Method not found"}})

        response_data = methods_map[method](params)
        if "jsonrpc" not in response_data:
            response_data["jsonrpc"] = "2.0"
            response_data["id"] = rpc_id

        return Response(response_data, status=status.HTTP_200_OK)


class ClickWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    def _verify_signature(self, data):
        merchant = Merchant.objects.filter(provider='CLICK', is_active=True).first()
        if not merchant: 
            return False
        
        secret_key = merchant.secret_key
        action = str(data.get('action'))
        prepare_id = str(data.get('merchant_prepare_id', '')) if action == '1' else ''

        sign_string = (
            f"{data.get('click_trans_id', '')}"
            f"{data.get('service_id', '')}"
            f"{secret_key}"
            f"{data.get('merchant_trans_id', '')}"
            f"{prepare_id}"
            f"{data.get('amount', '')}"
            f"{action}"
            f"{data.get('sign_time', '')}"
        )
        hashed = hashlib.md5(sign_string.encode()).hexdigest()
        return hashed == data.get('sign_string')

    def post(self, request):
        data = request.data
        if not self._verify_signature(data):
            return Response({"error": "-1", "error_note": "Signature verification failed"})

        action = str(data.get('action'))
        if action == '0':
            res = ClickService.prepare(data)
        elif action == '1':
            res = ClickService.complete(data)
        else:
            res = {"error": "-3", "error_note": "Action not found"}

        return Response(res, status=status.HTTP_200_OK)


class PaymentStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payment_id = request.query_params.get('payment_id')
        if not payment_id:
            return Response({"detail": "payment_id parametri majburiy"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            payment = Payment.objects.get(id=payment_id, order__user=request.user)
            return Response(PaymentStatusSerializer(payment).data)
        except (Payment.DoesNotExist, ValueError):
            return Response({"detail": "To'lov topilmadi"}, status=status.HTTP_404_NOT_FOUND)
