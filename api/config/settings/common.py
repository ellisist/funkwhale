# -*- coding: utf-8 -*-
"""
Django settings for funkwhale_api project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
from __future__ import absolute_import, unicode_literals

import os
import environ
from funkwhale_api import __version__

ROOT_DIR = environ.Path(__file__) - 3  # (/a/b/myfile.py - 3 = /)
APPS_DIR = ROOT_DIR.path('funkwhale_api')

env = environ.Env()

try:
    env.read_env(ROOT_DIR.file('.env'))
except FileNotFoundError:
    pass

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS')


# APP CONFIGURATION
# ------------------------------------------------------------------------------
DJANGO_APPS = (
    # Default Django apps:
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Useful template tags:
    # 'django.contrib.humanize',

    # Admin
    'django.contrib.admin',
)
THIRD_PARTY_APPS = (
    # 'crispy_forms',  # Form layouts
    'allauth',  # registration
    'allauth.account',  # registration
    'allauth.socialaccount',  # registration
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'taggit',
    'cachalot',
    'rest_auth',
    'rest_auth.registration',
    'mptt',
    'dynamic_preferences',
    'django_filters',
)


# Sentry
RAVEN_ENABLED = env.bool("RAVEN_ENABLED", default=False)
RAVEN_DSN = env("RAVEN_DSN", default='')

if RAVEN_ENABLED:
    RAVEN_CONFIG = {
        'dsn': RAVEN_DSN,
        # If you are using git, you can also automatically configure the
        # release based on the git info.
        'release': __version__,
    }
    THIRD_PARTY_APPS += (
        'raven.contrib.django.raven_compat',
    )


# Apps specific for this project go here.
LOCAL_APPS = (
    'funkwhale_api.common',
    'funkwhale_api.users',  # custom users app
    # Your stuff: custom apps go here
    'funkwhale_api.instance',
    'funkwhale_api.music',
    'funkwhale_api.requests',
    'funkwhale_api.favorites',
    'funkwhale_api.radios',
    'funkwhale_api.history',
    'funkwhale_api.playlists',
    'funkwhale_api.providers.audiofile',
    'funkwhale_api.providers.youtube',
    'funkwhale_api.providers.acoustid',
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIDDLEWARE CONFIGURATION
# ------------------------------------------------------------------------------
MIDDLEWARE = (
    # Make sure djangosecure.middleware.SecurityMiddleware is listed first
    'django.contrib.sessions.middleware.SessionMiddleware',
    'funkwhale_api.users.middleware.AnonymousSessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# MIGRATIONS CONFIGURATION
# ------------------------------------------------------------------------------
MIGRATION_MODULES = {
    'sites': 'funkwhale_api.contrib.sites.migrations'
}

# DEBUG
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)

# FIXTURE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-FIXTURE_DIRS
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)

# EMAIL CONFIGURATION
# ------------------------------------------------------------------------------
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')

# MANAGER CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = (
    ("""Eliot Berriot""", 'contact@eliotberriot.om'),
)

# See: https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    # Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
    'default': env.db("DATABASE_URL"),
}
DATABASES['default']['ATOMIC_REQUESTS'] = True
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': 'db.sqlite3',
#     }
# }
# GENERAL CONFIGURATION
# ------------------------------------------------------------------------------
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'UTC'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True

# See: https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = True

# TEMPLATE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # Your stuff: custom template context processors go here
            ],
        },
    },
]

# See: http://django-crispy-forms.readthedocs.org/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap3'

# STATIC FILE CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = env("STATIC_ROOT", default=str(ROOT_DIR('staticfiles')))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = env("STATIC_URL", default='/staticfiles/')

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = (
    str(APPS_DIR.path('static')),
)

# See: https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# MEDIA CONFIGURATION
# ------------------------------------------------------------------------------
# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = env("MEDIA_ROOT", default=str(APPS_DIR('media')))

# See: https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = env("MEDIA_URL", default='/media/')

# URL Configuration
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'config.urls'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# AUTHENTICATION CONFIGURATION
# ------------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# Some really nice defaults
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# Custom user app defaults
# Select the correct user model
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = 'users:redirect'
LOGIN_URL = 'account_login'

# SLUGLIFIER
AUTOSLUG_SLUGIFY_FUNCTION = 'slugify.slugify'

CACHE_DEFAULT = "redis://127.0.0.1:6379/0"
CACHES = {
    "default": env.cache_url('CACHE_URL', default=CACHE_DEFAULT)
}

CACHES["default"]["BACKEND"] = "django_redis.cache.RedisCache"
CACHES["default"]["OPTIONS"] = {
    "CLIENT_CLASS": "django_redis.client.DefaultClient",
    "IGNORE_EXCEPTIONS": True,  # mimics memcache behavior.
                                # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
}


########## CELERY
INSTALLED_APPS += ('funkwhale_api.taskapp.celery.CeleryConfig',)
CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL", default=env('CACHE_URL', default=CACHE_DEFAULT))
########## END CELERY
# Location of root django.contrib.admin URL, use {% url 'admin:index' %}
ADMIN_URL = r'^admin/'
# Your common stuff: Below this line define 3rd party library settings
CELERY_TASK_DEFAULT_RATE_LIMIT = 1
CELERY_TASK_TIME_LIMIT = 300
import datetime
JWT_AUTH = {
    'JWT_ALLOW_REFRESH': True,
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=7),
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=30),
    'JWT_AUTH_HEADER_PREFIX': 'JWT',
    'JWT_GET_USER_SECRET_KEY': lambda user: user.secret_key
}
OLD_PASSWORD_FIELD_ENABLED = True
ACCOUNT_ADAPTER = 'funkwhale_api.users.adapters.FunkwhaleAccountAdapter'
CORS_ORIGIN_ALLOW_ALL = True
# CORS_ORIGIN_WHITELIST = (
#     'localhost',
#     'funkwhale.localhost',
# )
CORS_ALLOW_CREDENTIALS = True
API_AUTHENTICATION_REQUIRED = env.bool("API_AUTHENTICATION_REQUIRED", True)
REGISTRATION_MODE = env('REGISTRATION_MODE', default='disabled')
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'funkwhale_api.common.pagination.FunkwhalePagination',
    'PAGE_SIZE': 25,

    'DEFAULT_AUTHENTICATION_CLASSES': (
        'funkwhale_api.common.authentication.JSONWebTokenAuthenticationQS',
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.OrderingFilter',
        'django_filters.rest_framework.DjangoFilterBackend',
    )
}

ATOMIC_REQUESTS = False
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
# Wether we should check user permission before serving audio files (meaning
# return an obfuscated url)
# This require a special configuration on the reverse proxy side
# See https://wellfire.co/learn/nginx-django-x-accel-redirects/ for example
PROTECT_AUDIO_FILES = env.bool('PROTECT_AUDIO_FILES', default=True)

# Which path will be used to process the internal redirection
# **DO NOT** put a slash at the end
PROTECT_FILES_PATH = env('PROTECT_FILES_PATH', default='/_protected')


# use this setting to tweak for how long you want to cache
# musicbrainz results. (value is in seconds)
MUSICBRAINZ_CACHE_DURATION = env.int(
    'MUSICBRAINZ_CACHE_DURATION',
    default=300
)

CACHALOT_ENABLED = env.bool('CACHALOT_ENABLED', default=True)


# Custom Admin URL, use {% url 'admin:index' %}
ADMIN_URL = env('DJANGO_ADMIN_URL', default='^api/admin/')
CSRF_USE_SESSIONS = True
