import hashlib
import io
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Import the real application with an isolated database, never a configured DB.
with patch.dict(os.environ, {'CONNECTION_STRING': 'sqlite://', 'SECRET_KEY': 'cache-tests'}):
    import server
    import storage_backends

from models import FileAlias, FileBlob, User, UserFile, db


class FileCacheTests(unittest.TestCase):
    body = b'unchanged file contents\n'
    public_id = 'a' * 32
    public_path = f'/file/{public_id}/sample.txt'
    legacy_path = '/images/legacy.txt'

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.context = server.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        db.create_all()
        self.addCleanup(db.drop_all)
        self.addCleanup(db.session.remove)

        self.checksum = hashlib.sha256(self.body).hexdigest()
        self.etag = f'"{self.checksum}"'
        self.blob = FileBlob(
            checksum_sha256=self.checksum,
            storage_backend='local',
            storage_key=self.checksum + '.txt',
            storage_name=self.checksum + '.txt',
            size=len(self.body),
            content_type='text/plain',
            created_at=datetime(2026, 1, 1, 12, 0, 0),
        )
        db.session.add(User(id=1, name='Test', role='user'))
        db.session.add(self.blob)
        db.session.flush()
        db.session.add(UserFile(
            public_id=self.public_id,
            owner_user_id=1,
            blob_id=self.blob.id,
            original_filename='sample.txt',
            safe_filename='sample.txt',
            checksum_sha256=self.checksum,
            size=len(self.body),
            content_type='text/plain',
        ))
        db.session.add(FileAlias(
            public_path='legacy.txt',
            blob_id=self.blob.id,
            original_filename='legacy.txt',
            checksum_sha256=self.checksum,
            size=len(self.body),
            content_type='text/plain',
        ))
        db.session.commit()
        Path(self.directory.name, self.blob.storage_key).write_bytes(self.body)
        self.local = SimpleNamespace(name='local', root_path=self.directory.name)
        self.storage_patch = patch.object(server, 'get_storage', return_value=self.local)
        self.get_storage = self.storage_patch.start()
        self.addCleanup(self.storage_patch.stop)
        self.client = server.app.test_client()

    def use_s3(self, public_url=None):
        self.blob.storage_backend = 's3'
        db.session.commit()
        storage = Mock()
        storage.name = 's3'
        storage.public_url.return_value = public_url
        storage.open.side_effect = lambda key: (io.BytesIO(self.body), 'text/plain')
        self.get_storage.return_value = storage
        return storage

    def assert_immutable_headers(self, response):
        self.assertEqual(response.headers['ETag'], self.etag)
        self.assertEqual(response.headers['Last-Modified'], 'Thu, 01 Jan 2026 12:00:00 GMT')
        self.assertEqual(response.headers['Cache-Control'], 'public, max-age=31536000, immutable')

    def test_local_file_headers_and_body(self):
        with self.client.get(self.public_path) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, self.body)
            self.assert_immutable_headers(response)

    def test_conditional_get_and_head_skip_storage(self):
        for backend in ('local', 's3'):
            self.blob.storage_backend = backend
            db.session.commit()
            for method in ('GET', 'HEAD'):
                for header in (self.etag, 'W/' + self.etag, '"old", ' + self.etag, '*'):
                    with self.subTest(backend=backend, method=method, etag=header):
                        self.get_storage.reset_mock()
                        response = self.client.open(
                            self.public_path, method=method,
                            headers={'If-None-Match': header},
                        )
                        self.assertEqual(response.status_code, 304)
                        self.assertEqual(response.data, b'')
                        self.assertEqual(response.headers['ETag'], self.etag)
                        self.assertIn('immutable', response.headers['Cache-Control'])
                        self.get_storage.assert_not_called()

    def test_modified_since_returns_304_before_storage(self):
        for method in ('GET', 'HEAD'):
            with self.subTest(method=method):
                response = self.client.open(
                    self.public_path, method=method,
                    headers={'If-Modified-Since': 'Thu, 01 Jan 2026 12:00:00 GMT'},
                )
                self.assertEqual(response.status_code, 304)
                self.assertEqual(response.data, b'')
                self.get_storage.assert_not_called()

    def test_stale_etag_takes_precedence_over_modified_since(self):
        with self.client.get(self.public_path, headers={
            'If-None-Match': '"old-checksum"',
            'If-Modified-Since': 'Fri, 01 Jan 2027 12:00:00 GMT',
        }) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, self.body)

    def test_failed_if_match_returns_412_without_storage(self):
        response = self.client.get(self.public_path, headers={'If-Match': '"old-checksum"'})
        self.assertEqual(response.status_code, 412)
        self.get_storage.assert_not_called()

    def test_legacy_alias_revalidates_instead_of_caching_permanently(self):
        with self.client.get(self.legacy_path) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers['Cache-Control'], 'no-cache')
            self.assertEqual(response.headers['ETag'], self.etag)
        response = self.client.get(self.legacy_path, headers={'If-None-Match': self.etag})
        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.headers['Cache-Control'], 'no-cache')

    def test_changed_legacy_alias_returns_new_contents_and_etag(self):
        body = b'updated file contents\n'
        checksum = hashlib.sha256(body).hexdigest()
        blob = FileBlob(
            checksum_sha256=checksum, storage_backend='local',
            storage_key=checksum + '.txt', storage_name=checksum + '.txt',
            size=len(body), content_type='text/plain',
        )
        db.session.add(blob)
        db.session.flush()
        FileAlias.query.filter_by(public_path='legacy.txt').one().blob_id = blob.id
        db.session.commit()
        Path(self.directory.name, blob.storage_key).write_bytes(body)
        with self.client.get(self.legacy_path, headers={'If-None-Match': self.etag}) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, body)
            self.assertEqual(response.headers['ETag'], f'"{checksum}"')
            self.assertEqual(response.headers['Cache-Control'], 'no-cache')

    def test_unregistered_legacy_file_keeps_conditional_serving(self):
        Path(self.directory.name, 'unregistered.txt').write_bytes(self.body)
        with patch.object(server, 'LOCAL_STORAGE_PATH', self.directory.name):
            with self.client.get('/images/unregistered.txt') as response:
                self.assertEqual(response.status_code, 200)
                etag = response.headers['ETag']
                self.assertEqual(response.headers['Cache-Control'], 'no-cache')
            with self.client.get('/images/unregistered.txt', headers={'If-None-Match': etag}) as response:
                self.assertEqual(response.status_code, 304)

    def test_local_range_and_if_range_keep_sha256_validator(self):
        with self.client.get(self.public_path, headers={
            'Range': 'bytes=0-8', 'If-Range': self.etag,
        }) as response:
            self.assertEqual(response.status_code, 206)
            self.assertEqual(response.data, self.body[:9])
            self.assertEqual(response.headers['Content-Range'], f'bytes 0-8/{len(self.body)}')
            self.assert_immutable_headers(response)
        with self.client.get(self.public_path, headers={
            'Range': 'bytes=0-8', 'If-Range': '"old-checksum"',
        }) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, self.body)

    def test_s3_proxy_returns_cache_headers_and_closes_stream(self):
        storage = self.use_s3()
        stream = io.BytesIO(self.body)
        storage.open.side_effect = None
        storage.open.return_value = (stream, 'text/plain')
        with self.client.get(self.public_path) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, self.body)
            self.assertEqual(response.content_length, len(self.body))
            self.assert_immutable_headers(response)
        self.assertTrue(stream.closed)
        storage.open.assert_called_once_with(self.blob.storage_key)

    def test_s3_head_uses_database_metadata_without_get_object(self):
        storage = self.use_s3()
        response = self.client.head(self.public_path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b'')
        self.assertEqual(response.content_length, len(self.body))
        self.assert_immutable_headers(response)
        storage.open.assert_not_called()

    def test_s3_public_redirect_is_not_cached_permanently(self):
        url = 'https://example.invalid/bucket/' + self.blob.storage_key
        storage = self.use_s3(public_url=url)
        response = self.client.get(self.public_path)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], url)
        self.assertEqual(response.headers['Cache-Control'], 'no-cache')
        storage.open.assert_not_called()

    def test_unknown_file_is_not_immutable(self):
        response = self.client.get('/file/missing/sample.txt')
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('immutable', response.headers.get('Cache-Control', ''))


class S3UploadCacheTests(unittest.TestCase):
    def test_new_objects_publish_immutable_cache_metadata(self):
        storage = object.__new__(storage_backends.S3Storage)
        storage.bucket = 'test-bucket'
        storage.prefix = 'images'
        storage.client = Mock()
        key = storage.save('sha256.txt', b'contents', 'text/plain')
        self.assertEqual(key, 'images/sha256.txt')
        storage.client.put_object.assert_called_once_with(
            Bucket='test-bucket', Key=key, Body=b'contents', ContentType='text/plain',
            CacheControl='public, max-age=31536000, immutable',
        )


if __name__ == '__main__':
    unittest.main()
