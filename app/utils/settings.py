from datetime import timedelta
import os
import environ
import yaml

# Define BASE_DIR to point to the root directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize environment variables
env = environ.Env()

# Reading .env file (ensure this is after BASE_DIR definition)
env_file_path = os.path.join(BASE_DIR, 'secure_keys.env')
if os.path.exists(env_file_path):
    environ.Env.read_env(env_file_path)
else:
    print(f"Expected .env file at {env_file_path} not found, using environment variables set in CI/CD.")

# Read environment variables
try:
    SECRET_KEY = env('DJANGO_SECRET_KEY')
except Exception as e:
    print(f"Error reading environment variables: {e}")
    raise

# cTrader credentials — read from environment, never hardcoded
CTRADER_CLIENT_ID = env('CTRADER_CLIENT_ID', default='')
CTRADER_CLIENT_SECRET = env('CTRADER_CLIENT_SECRET', default='')
CTRADER_ACCOUNT_ID = env('CTRADER_ACCOUNT_ID', default='')

# Path to your YAML config file
config_path = os.path.join(BASE_DIR, 'config.yaml')

# Ensure the YAML file path is correct by checking its existence
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Expected config file at {config_path}")

# Load YAML
with open(config_path, 'r') as config_file:
    config = yaml.safe_load(config_file)

DEBUG = config['DEBUG']
ALLOWED_HOSTS = config['ALLOWED_HOSTS']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'timescale',
] + config['INSTALLED_APPS']

DATABASES = {
    'default': {
        'ENGINE': 'timescale.db.backends.postgresql',
        'NAME': env('DB_NAME', default='tradingbot'),
        'USER': env('DB_USER', default='postgres'),
        'PASSWORD': env('DB_PASSWORD', default=''),
        'HOST': env('DB_HOST', default='timescaledb'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# cTrader host — demo for all non-production environments
DJANGO_ENV = env('ENVIRONMENT', default='development')
if DJANGO_ENV == 'production':
    CTRADER_HOST = 'live.ctraderapi.com'
else:
    CTRADER_HOST = 'demo.ctraderapi.com'
CTRADER_PORT = int(env('CTRADER_PORT', default='5035'))

# JWT Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Celery
CELERY_BROKER_URL = env('REDIS_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://redis:6379/0')

# Middleware configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# TEMPLATES configuration
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

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'test_env/logs/debug.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
