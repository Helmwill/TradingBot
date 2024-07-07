import os 
from pathlib import Path
import environ

#initialise environment variables
env=environ.Env()
environ.Env.read_env(Path(__file__).resolve().parent / '.env')

BASE_DIR = Path(__file__).resolve().parent.parent.parent

#sandbox API settings

COINBASE_API_KEY = env('COINBASE_API_KEY_SANDBOX')
COINBASE_API_SECRET = env('COINBASE_API_SECRET_SANDBOX')
COINBASE_API_PASSPHRASE = env('COINBASE_API_PASSPHRASE_SANDBOX')
COINBASE_API_URL = 'https://public.sandbox.exchange.coinbase.com/'

#Logging config

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
    'file': {
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'logs/debug.log'

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