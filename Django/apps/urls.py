from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from blog import views
from blog.views import CreatePaymentView, AnonymousOrderPaymentView

def index(request):
    return render(request, 'index.html')

def payment(request):
    return render(request, 'payment.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('payment/', payment, name='payment'),

    # Avtorizatsiyadan o'tgan userlar uchun
    path('api/create-payment/', CreatePaymentView.as_view(), name='create_payment'),
    
    # Anonim/Guest userlar uchun buyurtma va to'lov yaratish
    path('api/anonymous-payment/', AnonymousOrderPaymentView.as_view(), name='anonymous_payment'),

    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]
