from django.contrib import admin
from django.db.models import Sum, Count
from apps.models import Order, Payment, Transaction, WebhookLog, Merchant

@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'merchant_id', 'is_active', 'created_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'provider', 'amount', 'status', 'created_at')
    list_filter = ('provider', 'status', 'created_at')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'provider_transaction_id', 'amount', 'state', 'perform_time')
    search_fields = ('transaction_id', 'provider_transaction_id')
    list_filter = ('state',)

@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'provider', 'status_code', 'ip_address', 'created_at')
    readonly_fields = ('provider', 'request_headers', 'request_body', 'response_body', 'status_code', 'ip_address', 'created_at')

# Dashboard statistika ko'rinishi uchun custom sayt integratsiyasi
admin.site.index_title = "FinTech To'lov Tizimi Monitoringi"