from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    last_login = db.Column(db.DateTime, default=utcnow)


class FileBlob(db.Model):
    __tablename__ = 'file_blobs'

    id = db.Column(db.Integer, primary_key=True)
    checksum_sha256 = db.Column(db.String(64), nullable=False, unique=True, index=True)
    storage_backend = db.Column(db.String(20), nullable=False)
    storage_key = db.Column(db.String(512), nullable=False)
    storage_name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    size = db.Column(db.BigInteger, nullable=False)
    content_type = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class UserFile(db.Model):
    __tablename__ = 'user_files'
    __table_args__ = (
        db.UniqueConstraint('owner_user_id', 'original_filename', name='uq_user_files_owner_filename'),
    )

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(32), nullable=False, unique=True, index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    blob_id = db.Column(db.Integer, db.ForeignKey('file_blobs.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(512), nullable=False)
    safe_filename = db.Column(db.String(512), nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=False, index=True)
    size = db.Column(db.BigInteger, nullable=False)
    content_type = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_accessed_at = db.Column(db.DateTime, nullable=True)

    owner = db.relationship('User', backref=db.backref('files', lazy='dynamic'))
    blob = db.relationship('FileBlob', backref=db.backref('user_files', lazy='dynamic'))


class FileAlias(db.Model):
    __tablename__ = 'file_aliases'

    id = db.Column(db.Integer, primary_key=True)
    public_path = db.Column(db.String(512), nullable=False, unique=True, index=True)
    blob_id = db.Column(db.Integer, db.ForeignKey('file_blobs.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(512), nullable=False)
    checksum_sha256 = db.Column(db.String(64), nullable=False, index=True)
    size = db.Column(db.BigInteger, nullable=False)
    content_type = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    blob = db.relationship('FileBlob', backref=db.backref('aliases', lazy='dynamic'))
