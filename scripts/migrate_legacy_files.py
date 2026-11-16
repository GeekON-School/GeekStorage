import hashlib
import mimetypes
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import LEGACY_OWNER_USER_ID, LOCAL_STORAGE_PATH
from models import FileAlias, FileBlob, User, UserFile, db
from server import app
from storage_backends import get_storage


def _ensure_legacy_user():
    user = db.session.get(User, LEGACY_OWNER_USER_ID)
    if user is None:
        user = User(id=LEGACY_OWNER_USER_ID, name='Legacy uploads', role='legacy')
        db.session.add(user)
        db.session.flush()
    return user


def _safe_filename(filename):
    return secure_filename(filename) or 'file'


def _storage_name(path, checksum):
    ext = path.suffix.lower()
    return checksum + ext


def migrate_one(path, storage):
    body = path.read_bytes()
    checksum = hashlib.sha256(body).hexdigest()
    original_filename = path.name
    content_type = mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'

    blob = FileBlob.query.filter_by(checksum_sha256=checksum).first()
    if blob is None:
        storage_name = _storage_name(path, checksum)
        storage_key = storage.save(storage_name, body, content_type)
        blob = FileBlob(
            checksum_sha256=checksum,
            storage_backend=storage.name,
            storage_key=storage_key,
            storage_name=storage_name,
            size=len(body),
            content_type=content_type,
        )
        db.session.add(blob)
        db.session.flush()

    alias = FileAlias.query.filter_by(public_path=original_filename).first()
    if alias is None:
        db.session.add(FileAlias(
            public_path=original_filename,
            blob_id=blob.id,
            original_filename=original_filename,
            checksum_sha256=checksum,
            size=len(body),
            content_type=content_type,
        ))

    existing = (
        UserFile.query
        .filter_by(owner_user_id=LEGACY_OWNER_USER_ID, original_filename=original_filename)
        .first()
    )
    if existing:
        return False

    db.session.add(UserFile(
        public_id=uuid4().hex,
        owner_user_id=LEGACY_OWNER_USER_ID,
        blob_id=blob.id,
        original_filename=original_filename,
        safe_filename=_safe_filename(original_filename),
        checksum_sha256=checksum,
        size=len(body),
        content_type=content_type,
    ))
    return True


def main():
    legacy_dir = Path(LOCAL_STORAGE_PATH)
    if not legacy_dir.exists():
        print(f'legacy_migration skipped: {legacy_dir} does not exist')
        return

    with app.app_context():
        _ensure_legacy_user()
        storage = get_storage()
        migrated = 0
        processed = 0
        for path in sorted(legacy_dir.iterdir()):
            if not path.is_file():
                continue
            try:
                processed += 1
                if migrate_one(path, storage):
                    migrated += 1
                db.session.commit()
                if processed % 100 == 0:
                    print(f'legacy_migration processed={processed} imported={migrated}', flush=True)
            except IntegrityError:
                db.session.rollback()
        print(f'legacy_migration processed={processed} imported={migrated}', flush=True)


if __name__ == '__main__':
    main()
