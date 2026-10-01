"""
Django settings for blog project.
Optimized for production and security.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .env faylidagi o'zgaruvchilarni yuklash
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# --- XAVFSIZLIK SOZLAMALARI (PRODUCTION) ---

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-__w0y+m^@1pw8tc=fr@kza2%uvwyja&qe@fl0%+qkrig6=!w17')

# SECURITY WARNING: don't run with debug turned on in production!
# settings.py
DEBUG = True  # Buni True holatiga keltiring

# Haqiqiy sayt manzillarini shu yerga yozasiz
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,127.0.0.2').split(',')


# --- LOCALHOST UCHUN HTTPS MAJBURLASHNI O'CHIRISH ---
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# django-allauth uchun faqat HTTP protokolidan foydalanishni buyuramiz
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"


if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True            # Brauzerning XSS filtrini yoqish
    SECURE_CONTENT_TYPE_NOSNIFF = True          # MIME-turi hujumlaridan himoya
    X_FRAME_OPTIONS = 'DENY'                    # Clickjacking hujumidan himoya


# --- TIZIMGA KIRISH/CHIQISH YO'LLARI ---
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SITE_ID = 1  # django.contrib.sites uchun zarur bo'lgan defolt ID


# --- GOOGLE AUTHENTICATION SOZLAMALARI ---
# Google oynasi qotib qolmasligi va avtomatik ro'yxatdan o'tkazishi uchun
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
SOCIALACCOUNT_AUTO_SIGNUP = True


# --- AUTHENTICATION BACKENDS (GOOGLE UCHUN MAJBURIY) ---
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',             # Standart Django login
    'allauth.account.auth_backends.AuthenticationBackend',   # Google login (allauth)
]


# Application definition
INSTALLED_APPS = [
    'jazzmin',  # Chiroyli admin panel paneli uchun (Har doim eng tepada turishi shart)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  

    # Allauth ilovalari
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    'apps',            # Bu asosiy konfiguratsiya papkangiz sifatida qoladi
    'rest_framework',
    
    # MANA SHU YERINI TO'G'RILANG:
    'blog',            # 'apps.blog' emas, shunchaki 'blog'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Allauth middleware
]

ROOT_URLCONF = 'apps.urls'
WSGI_APPLICATION = 'apps.wsgi.application'

# MANA SHU YERDAGI BITTA T HARFINI O'CHIRING:
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'uz-uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- SESSINGIZNI BRAUZERDA SAQLASH SOZLAMALARI ---
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Brauzer yopilganda chiqib ketmaydi
SESSION_COOKIE_AGE = 1209600             # Sessiya muddati 2 hafta
SESSION_SAVE_EVERY_REQUEST = True
