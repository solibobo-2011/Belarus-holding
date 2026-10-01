from rest_framework import serializers
from apps.models import Payment, Order, Transaction

class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    provider = serializers.ChoiceField(choices=['PAYME', 'CLICK', 'UZUM', 'VISA', 'MASTERCARD'])

    def validate_order_id(self, value):
        if not Order.objects.filter(pk=value, status='PENDING').exists():
            raise serializers.ValidationError("Order topilmadi yoki faol holatda emas.")
        return value

class PaymentStatusSerializer(serializers.ModelSerializer):
    order_status = serializers.CharField(source='order.status', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'order', 'provider', 'amount', 'status', 'order_status', 'created_at']