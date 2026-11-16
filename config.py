import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


def env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


SECRET_KEY = os.getenv('SECRET_KEY') or os.getenv('SECRET') or 'dev-secret'
DEBUG = env_bool('DEBUG', False)
PORT = int(os.getenv('PORT', '8083'))

SQLALCHEMY_DATABASE_URI = os.getenv(
    'CONNECTION_STRING',
    'postgresql+psycopg2://geekstorage:geekstorage@localhost:5432/geekstorage',
)

APP_URL = os.getenv('APP_URL', 'https://storage.geekclass.ru')
GEEKCLASS_HOST = os.getenv('GEEKCLASS_HOST', 'https://codingprojects.ru')
JWT_SECRET = os.getenv('JWT_SECRET')
AUTH_URL = os.getenv('AUTH_URL', GEEKCLASS_HOST + '/insider/jwt?redirect_url=')
TOKEN_MAX_AGE_SECONDS = int(os.getenv('TOKEN_MAX_AGE_SECONDS', '60'))

STORAGE_BACKEND = os.getenv('STORAGE_BACKEND', 'local').lower()
LOCAL_STORAGE_PATH = os.getenv('LOCAL_STORAGE_PATH', str(BASE_DIR / 'images'))

S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
S3_BUCKET = os.getenv('S3_BUCKET')
S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID')
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
S3_REGION = os.getenv('S3_REGION', 'ru-central1')
S3_PREFIX = os.getenv('S3_PREFIX', 'images').strip('/')
S3_PUBLIC_BASE_URL = os.getenv('S3_PUBLIC_BASE_URL')

LEGACY_OWNER_USER_ID = int(os.getenv('LEGACY_OWNER_USER_ID', '0'))
