import json
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import boto3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '(i#*06f#keydy_fh17bf=$0f6v)^wr^l7*u4gq42m*sztu#2_m'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'captcha',

    'student_management_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'student_management_app.LoginCheckMiddleWare.LoginCheckMiddleWare',
    'student_management_system.middleware.CustomMiddleware',
]

ROOT_URLCONF = 'student_management_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'student_management_system.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DB_CONFIG = json.load(
    open(os.path.join(BASE_DIR, 'resources', 'virtual_study_center', 'config', "db_config.json"), "r+"))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_CONFIG['mysql']['db_name'],
        'USER': DB_CONFIG['mysql']['user'],
        'PASSWORD': DB_CONFIG['mysql']['pass'],
        'HOST': DB_CONFIG['mysql']['host'],
        'PORT': DB_CONFIG['mysql']['port'],
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
# STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# For Custom USER
AUTH_USER_MODEL = "student_management_app.CustomUser"

# Registering Custom Backend "EmailBackEnd"
AUTHENTICATION_BACKENDS = ['student_management_app.EmailBackEnd.EmailBackEnd']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
BASE_EMAIL_ID = ""

os.environ["AWS_CONFIG_FILE"] = "resources\\virtual_study_center\\config\\config.ini"
S3_BUCKET = "ignouresources"
session = boto3.Session(profile_name="study_cent")
S3_CLIENT = session.client('s3')

with open('resources/virtual_study_center/lang_config.json') as lang_config_file:
    LANG_CONFIG_FILE = json.load(lang_config_file)

"""
----- DJANGO LOGGER -----
"""

LOGS_DIR = BASE_DIR + "/logs"

if os.path.exists(LOGS_DIR) and os.path.isdir(LOGS_DIR):
    print("LOGS_DIR: ", LOGS_DIR)
else:
    os.mkdir(LOGS_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOGS_DIR + '/server.log',
            'formatter': 'verbose',
        },
        'mail_admin': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file', 'mail_admin'],
            'propagate': True,
        },
    },
}
