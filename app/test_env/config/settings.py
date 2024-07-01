import os 
from pathlib import Path
import environ

#initialise environment variables
env=environ.env()
environ.env.read_env(Path(__file__).resolve().parent / '.env')

BASE_DIR = Path(__file__).resolve.parent.parent.parent

#sandbox API settings

COINBASE_API_KEY = env('1631994271eb0cb395a8370b5291c353')
CONBASE_API_SECRET = env('CSxO+zJJI/MC6p4w/aMvTyR/IB78rq7oDnt8JNPp/hppclngndhjH7VtvwDyy7gh3P24FltngCcWE7dSX07Cxw==')
COINBASE_API_PASSPHRASE = env('7hkkcw4pe4j')
COINBASE_API_URL = 'https://public.sandbox.exchange.coinbase.com/'

#Logging config

LOGGING = {
    'version': 1,
    'disable_existing_;loggers': False,
    'handlers': {
    'file': {
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'logs/debug.log'

        },
    },
    'loggers': {
        'django': {
            'handlers': 'DEBUG', 
            'level': 'DEBUG',
            'propogate': True,

            },
        },
}