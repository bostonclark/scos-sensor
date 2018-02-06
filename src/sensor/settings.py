"""Django settings for scos-sensor project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/

"""

import os
import sys


# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(BASE_DIR)

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    ('js', os.path.join(STATIC_ROOT, 'js')),
    ('css', os.path.join(STATIC_ROOT, 'css')),
    ('images', os.path.join(STATIC_ROOT, 'images')),
    ('fonts', os.path.join(STATIC_ROOT, 'fonts')),
)

RUNNING_DEVSERVER = 'runserver' in sys.argv

_testcmd = os.path.split(sys.argv[0])[-1]
RUNNING_TESTS = 'test' in _testcmd

# Healthchecks - the existance of any of these indicates an unhealth state
SDR_HEALTHCHECK_FILE = os.path.join(REPO_ROOT, 'sdr_unhealthy')

OPENAPI_FILE = os.path.join(REPO_ROOT, 'docs', 'openapi.json')

# Cleanup any existing healtcheck files
try:
    os.remove(SDR_HEALTHCHECK_FILE)
except OSError:
    pass

# See /env.template
if RUNNING_DEVSERVER or RUNNING_TESTS:
    SECRET_KEY = '!j1&*$wnrkrtc-74cc7_^#n6r3om$6s#!fy=zkd_xp(gkikl+8'
    DEBUG = True
    ALLOWED_HOSTS = []
else:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECRET_KEY = os.environ['SECRET_KEY']
    DEBUG = bool(os.environ['DEBUG'] == "true")
    ALLOWED_HOSTS = os.environ['DOMAINS'].split() + os.environ['IPS'].split()

SESSION_COOKIE_SECURE = not RUNNING_DEVSERVER
CSRF_COOKIE_SECURE = not RUNNING_DEVSERVER


# Application definition

API_TITLE = "SCOS Sensor API"

API_DESCRIPTION = """A RESTful API for controlling a SCOS-compatible sensor.

# Errors

The API uses standard HTTP status codes to indicate the success or failure of
the API call. The body of the response will be JSON in the following format:

## 400 Bad Request (Parse Error)

```json
{
    "field_name": [
        "description of first error",
        "description of second error",
        ...
    ]
}
```

## 400 Bad Request (Protected Error)

```json
{
    "detail": "description of error",
    "protected_objects": [
        "url_to_protected_item_1",
        "url_to_protected_item_2",
        ...
    ]
}
```

## 409 Conflict (DB Integrity Error)

```json
{
    "detail": "description of error"
}
```

"""

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'request',  # django-request
    'rest_framework',
    'rest_framework.authtoken',
    'drf_openapi',
    # project-local apps
    'acquisitions.apps.AcquisitionsConfig',
    'authentication.apps.AuthenticationConfig',
    'results.apps.ResultsConfig',
    'schedule.apps.ScheduleConfig',
    'scheduler.apps.SchedulerConfig',
    'status.apps.StatusConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'request.middleware.RequestMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sensor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'sensor.wsgi.application'


# Django Rest Framework
# http://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'sensor.exceptions.exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    # Versioning
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',  # this should always point to latest stable api
    'ALLOWED_VERSIONS': ('v1',),
}


# Django Rest Swagger
# http://marcgibbons.github.io/django-rest-swagger/
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'token': {
            'type': 'apiKey',
            'description': (
                "Tokens are automatically generated for all users. You can "
                "view yours by going to your User Details view in the "
                "browsable API at `/api/v1/users/me` and looking for the "
                "`auth_token` key. Non-admin user accounts do not initially "
                "have a password and so can not log in to the browsable API. "
                "To set a password for a user (for testing purposes), an "
                "admin can use `manage.py changepassword <username>`, but "
                "only the account's token should be stored and used for "
                "general purpose API access."
            ),
            'name': 'Token',
            'in': 'header'
        }
    }
}


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(REPO_ROOT, 'db.sqlite3'),
        'OPTIONS': {
            'timeout': 20
        }
    }
}


# Ensure not more than this many results are stored in db by removing oldest
MAX_TASK_RESULTS = 10000


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'authentication.User'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


LOGLEVEL = 'DEBUG' if DEBUG else 'INFO'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] [%(levelname)s] %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'actions': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'acquisitions': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'capabilities': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'schedule': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'scheduler': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'sensor': {
            'handlers': ['console'],
            'level': LOGLEVEL
        },
        'status': {
            'handlers': ['console'],
            'level': LOGLEVEL
        }
    }
}
