import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class OrderStatus(models.TextChoices):
    PENDING = 'PENDING', _('Pending')
    PROCESSING = 'PROCESSING', _('Processing')
    PAID = 'PAID', _('Paid')
    FAILED = 'FAILED', _('Failed')
    CANCELLED = 'CANCELLED', _('Cancelled')
    REFUNDED = 'REFUNDED', _('Refunded')

class PaymentStatus(models.TextChoices):
    CREATED = 'CREATED', _('Created')
    WAITING = 'WAITING', _('Waiting')
    SUCCESS = 'SUCCESS', _('Success')
    ERROR = 'ERROR', _('Error')

class ProviderChoice(models.TextChoices):
    PAYME = 'PAYME', _('Payme')
    CLICK = 'CLICK', _('Click')
    UZUM = 'UZUM', _('Uzum')
    VISA = 'VISA', _('Visa')
    MASTERCARD = 'MASTERCARD', _('Mastercard')

class Merchant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=20, choices=ProviderChoice.choices)
    merchant_id = models.CharField(max_length=255, unique=True)
    secret_key = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'merchants'

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='payments')
    provider = models.CharField(max_length=20, choices=ProviderChoice.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.CREATED)
    idempotency_key = models.UUIDField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'apps_payments'

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='transactions', null=True, blank=True)
    transaction_id = models.CharField(max_length=255, unique=True)
    provider_transaction_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    state = models.IntegerField(default=1)
    reason = models.IntegerField(null=True, blank=True)
    create_time = models.DateTimeField(null=True, blank=True)
    perform_time = models.DateTimeField(null=True, blank=True)
    cancel_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['provider_transaction_id']),
        ]

class Refund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='refunds')
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refunds'

class WebhookLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.CharField(max_length=20, choices=ProviderChoice.choices)
    request_headers = models.JSONField()
    request_body = models.JSONField()
    response_body = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'webhook_logs'

class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)

    class Meta:
        db_table = 'categories'

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
