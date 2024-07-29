from datetime import timedelta
import os
import environ
import yaml
from pathlib import Path
import pymysql

# Install pymysql as MySQLdb
pymysql.install_as_MySQLdb()

# Define BASE_DIR to point to the root directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize environment variables
env = environ.Env()

# Reading .env file (ensure this is after BASE_DIR definition)
env_file_path = os.path.join(BASE_DIR, 'app', 'secure_keys.env')
print("Reading .env file from:", env_file_path)

# Ensure the .env file path is correct by checking its existence
if not os.path.exists(env_file_path):
    raise FileNotFoundError(f"Expected .env file at {env_file_path}")

environ.Env.read_env(env_file_path
# Read environment variables
try:
    SECRET_KEY = env('DJANGO_SECRET_KEY')
    COINBASE_API_KEY_SANDBOX = env('API_KEY_SANDBOX')
    COINBASE_API_SECRET_SANDBOX = env('API_SECRET_SANDBOX')
    COINBASE_API_PASSPHRASE_SANDBOX = env('API_PASSPHRASE_SANDBOX')
except Exception as e:
    print(f"Error reading environment variables: {e}")
    raise

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
    # Add your other apps here
] + config['INSTALLED_APPS']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env('RDS_DB_NAME'),
        'USER': env('RDS_DB_USER'),
        'PASSWORD': env('RDS_DB_PASSWORD'),
        'HOST': env('RDS_DB_HOST'),
        'PORT': env('RDS_DB_PORT', default='3306'),
        'OPTIONS': {
            'connect_timeout': 30,
        }
    }
}

# Determine the environment to use
DJANGO_ENV = env('ENVIRONMENT', default='development')

if DJANGO_ENV == 'development':
    COINBASE_API_URL = 'https://api.pro.coinbase.com'
elif DJANGO_ENV == 'test':
    COINBASE_API_URL = 'https://api-public.sandbox.pro.coinbase.com'
    COINBASE_API_KEY = COINBASE_API_KEY_SANDBOX
    COINBASE_API_SECRET = COINBASE_API_SECRET_SANDBOX
    COINBASE_API_PASSPHRASE = COINBASE_API_PASSPHRASE_SANDBOX

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
