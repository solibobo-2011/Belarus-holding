import time
from django.utils import timezone
from django.db import transaction as db_transaction
from apps.models import Payment, Transaction, Order, OrderStatus, PaymentStatus
from datetime import datetime

class PaymeService:
    @staticmethod
    def ms_to_datetime(ms):
        if not ms: return None
        return timezone.make_aware(datetime.fromtimestamp(int(ms) / 1000.0))

    @staticmethod
    def datetime_to_ms(dt):
        if not dt: return 0
        return int(time.mktime(dt.timetuple()) * 1000)

    @classmethod
    @db_transaction.atomic
    def check_perform_transaction(cls, params):
        account = params.get('account', {})
        order_id = account.get('order_id')
        amount = params.get('amount')

        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except (Order.DoesNotExist, ValueError):
            return {"error": {"code": -31050, "message": "Order not found"}}

        if int(order.amount * 100) != int(amount):
            return {"error": {"code": -31001, "message": "Incorrect amount"}}

        if order.status != OrderStatus.PENDING:
            return {"error": {"code": -31051, "message": "Order already processed"}}

        return {"result": {"allow": True}}

    @classmethod
    @db_transaction.atomic
    def create_transaction(cls, params):
        tx_id = params.get('id')
        amount = params.get('amount')
        account = params.get('account', {})
        order_id = account.get('order_id')
        tx_time = params.get('time')

        # Avval mavjud tranzaksiyani tekshirish
        try:
            tx = Transaction.objects.select_for_update().get(transaction_id=tx_id)
            if tx.state == 1:
                return {
                    "result": {
                        "create_time": cls.datetime_to_ms(tx.create_time),
                        "transaction": tx.id.hex,
                        "state": 1
                    }
                }
            else:
                return {"error": {"code": -31008, "message": "Transaction in wrong state"}}
        except Transaction.DoesNotExist:
            pass

        # Validatsiya
        check_res = cls.check_perform_transaction(params)
        if "error" in check_res:
            return check_res

        order = Order.objects.get(pk=order_id)
        
        # Payment va Transaction yaratish
        payment = Payment.objects.create(
            order=order, provider='PAYME', amount=float(amount)/100, status=PaymentStatus.WAITING
        )
        
        tx = Transaction.objects.create(
            payment=payment,
            transaction_id=tx_id,
            amount=float(amount)/100,
            state=1,
            create_time=cls.ms_to_datetime(tx_time)
        )
        
        order.status = OrderStatus.PROCESSING
        order.save()

        return {
            "result": {
                "create_time": tx_time,
                "transaction": tx.id.hex,
                "state": 1
            }
        }

    @classmethod
    @db_transaction.atomic
    def perform_transaction(cls, params):
        tx_id = params.get('id')
        try:
            tx = Transaction.objects.select_for_update().get(transaction_id=tx_id)
        except Transaction.DoesNotExist:
            return {"error": {"code": -31003, "message": "Transaction not found"}}

        if tx.state == 1:
            tx.state = 2
            tx.perform_time = timezone.now()
            tx.save()

            payment = tx.payment
            payment.status = PaymentStatus.SUCCESS
            payment.save()

            order = payment.order
            order.status = OrderStatus.PAID
            order.save()

        if tx.state == 2:
            return {
                "result": {
                    "transaction": tx.id.hex,
                    "perform_time": cls.datetime_to_ms(tx.perform_time),
                    "state": 2
                }
            }
        
        return {"error": {"code": -31008, "message": "Transaction cancelled or incorrect"}}

    @classmethod
    @db_transaction.atomic
    def cancel_transaction(cls, params):
        tx_id = params.get('id')
        reason = params.get('reason')
        try:
            tx = Transaction.objects.select_for_update().get(transaction_id=tx_id)
        except Transaction.DoesNotExist:
            return {"error": {"code": -31003, "message": "Transaction not found"}}

        if tx.state == 1:
            tx.state = -1
            tx.cancel_time = timezone.now()
            tx.reason = reason
            tx.save()

            payment = tx.payment
            payment.status = PaymentStatus.ERROR
            payment.save()

            order = payment.order
            order.status = OrderStatus.CANCELLED
            order.save()

        elif tx.state == 2:
            # Refund holati
            tx.state = -2
            tx.cancel_time = timezone.now()
            tx.reason = reason
            tx.save()

            payment = tx.payment
            payment.status = PaymentStatus.ERROR
            payment.save()

            order = payment.order
            order.status = OrderStatus.REFUNDED
            order.save()

        return {
            "result": {
                "transaction": tx.id.hex,
                "cancel_time": cls.datetime_to_ms(tx.cancel_time),
                "state": tx.state
            }
        }

    @classmethod
    def check_transaction(cls, params):
        tx_id = params.get('id')
        try:
            tx = Transaction.objects.get(transaction_id=tx_id)
            return {
                "result": {
                    "create_time": cls.datetime_to_ms(tx.create_time),
                    "perform_time": cls.datetime_to_ms(tx.perform_time),
                    "cancel_time": cls.datetime_to_ms(tx.cancel_time),
                    "transaction": tx.id.hex,
                    "state": tx.state,
                    "reason": tx.reason
                }
            }
        except Transaction.DoesNotExist:
            return {"error": {"code": -31003, "message": "Transaction not found"}}


class ClickService:
    @classmethod
    @db_transaction.atomic
    def prepare(cls, data):
        click_trans_id = data.get('click_trans_id')
        merchant_trans_id = data.get('merchant_trans_id') # Bizning Order ID
        amount = float(data.get('amount', 0))

        try:
            order = Order.objects.select_for_update().get(pk=merchant_trans_id)
        except (Order.DoesNotExist, ValueError):
            return {"error": "-5", "error_note": "Order does not exist"}

        if float(order.amount) != amount:
            return {"error": "-2", "error_note": "Incorrect amount"}

        if order.status != OrderStatus.PENDING:
            return {"error": "-4", "error_note": "Already paid or processed"}

        # Tranzaksiya yaratish yoki tekshirish
        tx, created = Transaction.objects.get_or_create(
            transaction_id=click_trans_id,
            defaults={
                'amount': amount,
                'state': 1,
                'create_time': timezone.now()
            }
        )
        
        if not created and tx.state == -1:
            return {"error": "-9", "error_note": "Transaction cancelled"}

        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": tx.id.hex,
            "error": "0",
            "error_note": "Success"
        }

    @classmethod
    @db_transaction.atomic
    def complete(cls, data):
        click_trans_id = data.get('click_trans_id')
        merchant_prepare_id = data.get('merchant_prepare_id')
        error = data.get('error')

        try:
            tx = Transaction.objects.select_for_update().get(id=merchant_prepare_id)
        except (Transaction.DoesNotExist, ValueError):
            return {"error": "-6", "error_note": "Transaction prepare not found"}

        if int(error) < 0:
            tx.state = -1
            tx.cancel_time = timezone.now()
            tx.save()
            return {"error": "0", "error_note": "Cancelled stored"}

        if tx.state == 2:
            return {"click_trans_id": click_trans_id, "merchant_trans_id": tx.id.hex, "error": "0", "error_note": "Already done"}

        # To'lovni yakunlash
        tx.state = 2
        tx.perform_time = timezone.now()
        tx.provider_transaction_id = click_trans_id
        tx.save()

        # Bog'liq modellar yangilanishi
        order = Order.objects.get(payments__transactions=tx)
        order.status = OrderStatus.PAID
        order.save()
        
        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": order.id.hex,
            "merchant_confirm_id": tx.id.hex,
            "error": "0",
            "error_note": "Success"
        }