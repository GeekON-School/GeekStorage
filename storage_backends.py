import os
from pathlib import Path

from config import (
    LOCAL_STORAGE_PATH,
    S3_ACCESS_KEY_ID,
    S3_BUCKET,
    S3_ENDPOINT_URL,
    S3_PREFIX,
    S3_PUBLIC_BASE_URL,
    S3_REGION,
    S3_SECRET_ACCESS_KEY,
    STORAGE_BACKEND,
)


class LocalStorage:
    name = 'local'

    def __init__(self, root_path):
        self.root_path = root_path
        Path(self.root_path).mkdir(parents=True, exist_ok=True)

    def save(self, storage_name, body, content_type):
        path = Path(self.root_path) / storage_name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
        return storage_name

    def public_url(self, storage_key):
        return None


class S3Storage:
    name = 's3'

    def __init__(self):
        import boto3

        if not S3_BUCKET:
            raise RuntimeError('S3_BUCKET is required when STORAGE_BACKEND=s3')
        self.bucket = S3_BUCKET
        self.prefix = S3_PREFIX
        self.client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT_URL,
            region_name=S3_REGION,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        )

    def _key(self, storage_name):
        return f'{self.prefix}/{storage_name}' if self.prefix else storage_name

    def save(self, storage_name, body, content_type):
        key = self._key(storage_name)
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, ContentType=content_type)
        return key

    def public_url(self, storage_key):
        if not S3_PUBLIC_BASE_URL:
            return None
        return f'{S3_PUBLIC_BASE_URL.rstrip("/")}/{storage_key}'

    def open(self, storage_key):
        result = self.client.get_object(Bucket=self.bucket, Key=storage_key)
        return result['Body'], result.get('ContentType')


def get_storage(name=None):
    selected = (name or STORAGE_BACKEND).lower()
    if selected == 'local':
        return LocalStorage(LOCAL_STORAGE_PATH)
    if selected == 's3':
        return S3Storage()
    raise RuntimeError(f'Unsupported storage backend: {selected}')
