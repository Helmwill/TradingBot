import os
import environ
import yaml

# Define BASE_DIR to point to the 'app' directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize environment variables
env = environ.Env()

# Reading .env file (ensure this is after BASE_DIR definition)
env_file_path = os.path.join(BASE_DIR, '..', 'secure_keys.env')
print("Reading .env file from:", env_file_path)

# Ensure the .env file path is correct by checking its existence
if not os.path.exists(env_file_path):
    raise FileNotFoundError(f"Expected .env file at {env_file_path}")

environ.Env.read_env(env_file_path)

# Check if DJANGO_SECRET_KEY is correctly read
try:
    secret_key = env('DJANGO_SECRET_KEY')
    print("DJANGO_SECRET_KEY:", secret_key)
except Exception as e:
    print(f"Error reading DJANGO_SECRET_KEY: {e}")
    raise

# Path to your YAML config file
config_path = os.path.join(BASE_DIR, 'config.yaml')

# Ensure the YAML file path is correct by checking its existence
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Expected config file at {config_path}")

# Load YAML
with open(config_path, 'r') as config_file:
    config = yaml.safe_load(config_file)

# Extract settings from YAML
DEBUG = config['DEBUG']
ALLOWED_HOSTS = config['ALLOWED_HOSTS']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
] + config['INSTALLED_APPS']

# Extract settings from environment variables
SECRET_KEY = secret_key

# Database settings from YAML
DATABASES = {
    'default': {
        'ENGINE': config['DATABASES']['default']['ENGINE'],
        'NAME': os.path.join(BASE_DIR, config['DATABASES']['default']['NAME']),
    }
}

# Application definition
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

ROOT_URLCONF = 'healthCheck.urls'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
