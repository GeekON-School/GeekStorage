# GeekStorage

Small authenticated file storage service.

## Local assets

Frontend libraries are installed with npm and bundled with Vite:

```bash
npm install
npm run build
```

The Flask app serves the built bundle from `static/dist`.

## Docker

Create `.env` from `.env.example`, set `JWT_SECRET` and `SECRET_KEY`, then run:

```bash
docker compose up --build
```

The compose stack starts PostgreSQL, runs Flask-Migrate migrations, imports legacy files from `LOCAL_STORAGE_PATH`, then starts the web service on port `8083`.

## Storage backends

Local storage is the default:

```env
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=/data/images
```

Yandex Object Storage is S3-compatible:

```env
STORAGE_BACKEND=s3
S3_ENDPOINT_URL=https://storage.yandexcloud.net
S3_BUCKET=geekstorage
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_REGION=ru-central1
S3_PREFIX=images
S3_PUBLIC_BASE_URL=https://storage.yandexcloud.net/geekstorage
```

If `S3_PUBLIC_BASE_URL` is omitted, GeekStorage proxies file reads through Flask.

## HTTP caching

`/file/<public_id>/<filename>` URLs identify immutable files and return
`Cache-Control: public, max-age=31536000, immutable`. Publish a new URL when the
contents change. Registered legacy `/images/<filename>` URLs return
`Cache-Control: no-cache`, so clients validate their cached copy before reuse.

Local files and proxied S3 files use the stored SHA-256 as `ETag` and the blob's
creation time as `Last-Modified`. Matching conditional GET and HEAD requests return
`304` before opening storage. A proxied S3 HEAD request also avoids downloading the
object. Local files retain support for byte-range requests.

Public S3 redirects are revalidated rather than cached permanently. The final
response uses S3's own validators; new objects are uploaded with the immutable
cache policy. Existing public S3 objects keep their current metadata until it is
updated in the bucket.

Run the caching regression tests with `python -m unittest discover -s tests`.

## Legacy files

`scripts/migrate_legacy_files.py` imports files already present in `LOCAL_STORAGE_PATH` into the new database and keeps legacy `/images/<filename>` links working. The Docker migration service runs this script automatically after `flask db upgrade`.
