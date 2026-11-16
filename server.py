import hashlib
import mimetypes
import time
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import quote
from uuid import uuid4

import jwt
from flask import Flask, Response, abort, jsonify, redirect, render_template, request, send_from_directory, session
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from config import (
    APP_URL,
    AUTH_URL,
    DEBUG,
    JWT_SECRET,
    LOCAL_STORAGE_PATH,
    PORT,
    SECRET_KEY,
    SQLALCHEMY_DATABASE_URI,
    TOKEN_MAX_AGE_SECONDS,
)
from models import FileAlias, FileBlob, User, UserFile, db
from storage_backends import get_storage


app = Flask(__name__, template_folder='.')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

db.init_app(app)
migrate = Migrate(app, db)


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _app_url():
    return (APP_URL or request.host_url.rstrip('/')).rstrip('/')


def _public_request_url():
    path = request.full_path
    if path.endswith('?'):
        path = path[:-1]
    return _app_url() + path


def _safe_filename(filename):
    safe = secure_filename(filename or '')
    return safe or 'file'


def _extension(filename):
    return secure_filename(filename or '').rsplit('.', 1)[-1].lower() if '.' in secure_filename(filename or '') else ''


def _process_jwt(token):
    if not JWT_SECRET:
        abort(500, description='JWT_SECRET is not configured')

    data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    if time.time() - int(data.get('iat', 0)) > TOKEN_MAX_AGE_SECONDS:
        abort(403)

    user = db.session.get(User, data['id'])
    if user is None:
        user = User(id=data['id'], name=data.get('name') or str(data['id']), role=data.get('role') or 'user')
        db.session.add(user)
    else:
        user.name = data.get('name') or user.name
        user.role = data.get('role') or user.role
        user.last_login = _utcnow()

    db.session.commit()
    session['user_id'] = user.id
    session['role'] = user.role
    session['name'] = user.name


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.args.get('token')
        if token:
            try:
                _process_jwt(token)
            except Exception:
                abort(403)
            args_without_token = {k: v for k, v in request.args.items() if k != 'token'}
            suffix = '?' + '&'.join(f'{k}={quote(v)}' for k, v in args_without_token.items()) if args_without_token else ''
            return redirect(request.path + suffix)

        if 'user_id' not in session:
            if request.method != 'GET':
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(AUTH_URL + quote(_public_request_url(), safe=''))

        return func(*args, **kwargs)

    return wrapper


def api_login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return func(*args, **kwargs)

    return wrapper


def _links_for(user_file):
    quoted_name = quote(user_file.safe_filename)
    direct_url = f'{_app_url()}/file/{user_file.public_id}/{quoted_name}'
    return {
        'id': user_file.public_id,
        'direct': direct_url,
        'markdown': f'![]({direct_url})',
        'html': f'<img src="{direct_url}" alt="{user_file.original_filename}"/>',
        'filename': user_file.original_filename,
        'size': user_file.size,
        'sha256': user_file.checksum_sha256,
        'created_at': user_file.created_at.isoformat() if user_file.created_at else None,
    }


def _content_type(filename, fallback=None):
    return fallback or mimetypes.guess_type(filename or '')[0] or 'application/octet-stream'


@app.route('/', methods=['GET'])
@login_required
def index():
    return render_template('home.html')


@app.route('/', methods=['POST'])
@login_required
def upload():
    uploaded = request.files.get('file')
    if uploaded is None or not uploaded.filename:
        return jsonify({'error': 'No file uploaded'}), 400

    body = uploaded.read()
    if not body:
        return jsonify({'error': 'Empty files are not accepted'}), 400

    original_filename = uploaded.filename
    safe_filename = _safe_filename(original_filename)
    checksum = hashlib.sha256(body).hexdigest()
    user_id = session['user_id']

    existing_by_name = (
        UserFile.query
        .filter_by(owner_user_id=user_id, original_filename=original_filename)
        .first()
    )
    if existing_by_name:
        payload = _links_for(existing_by_name)
        payload['deduplicated'] = True
        payload['deduplicated_by'] = 'filename'
        return jsonify(payload)

    storage = get_storage()
    blob = FileBlob.query.filter_by(checksum_sha256=checksum).first()
    deduplicated_by_hash = blob is not None
    if blob is None:
        ext = _extension(safe_filename)
        storage_name = checksum + (f'.{ext}' if ext else '')
        content_type = _content_type(original_filename, uploaded.content_type)
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

    user_file = UserFile(
        public_id=uuid4().hex,
        owner_user_id=user_id,
        blob_id=blob.id,
        original_filename=original_filename,
        safe_filename=safe_filename,
        checksum_sha256=checksum,
        size=len(body),
        content_type=blob.content_type or _content_type(original_filename, uploaded.content_type),
    )
    db.session.add(user_file)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        user_file = (
            UserFile.query
            .filter_by(owner_user_id=user_id, original_filename=original_filename)
            .first()
        )
        if user_file is None:
            raise

    payload = _links_for(user_file)
    payload['deduplicated'] = deduplicated_by_hash
    if deduplicated_by_hash:
        payload['deduplicated_by'] = 'hash'
    return jsonify(payload)


@app.route('/api/files')
@api_login_required
def list_files():
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 25, type=int), 1), 100)
    query = (
        UserFile.query
        .filter_by(owner_user_id=session['user_id'])
        .order_by(UserFile.created_at.desc())
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'files': [_links_for(item) for item in pagination.items],
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
        'total': pagination.total,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
    })


@app.route('/api/me')
def me():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'id': session['user_id'], 'role': session.get('role'), 'name': session.get('name')})


@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/file/<public_id>/<path:filename>')
def public_file(public_id, filename):
    user_file = UserFile.query.filter_by(public_id=public_id).first_or_404()
    user_file.last_accessed_at = _utcnow()
    db.session.commit()
    return _send_blob(user_file.blob, download_name=user_file.original_filename)


@app.route('/images/<path:storage_name>')
def legacy_image(storage_name):
    alias = FileAlias.query.filter_by(public_path=storage_name).first()
    if alias is not None:
        return _send_blob(alias.blob, download_name=alias.original_filename)

    blob = FileBlob.query.filter_by(storage_name=storage_name).first()
    if blob is not None:
        return _send_blob(blob)

    try:
        return send_from_directory(LOCAL_STORAGE_PATH, storage_name)
    except FileNotFoundError:
        abort(404)


def _send_blob(blob, download_name=None):
    storage = get_storage(blob.storage_backend)
    if storage.name == 'local':
        return send_from_directory(
            storage.root_path,
            blob.storage_key,
            mimetype=blob.content_type,
            download_name=download_name,
            as_attachment=False,
        )

    public_url = storage.public_url(blob.storage_key)
    if public_url:
        return redirect(public_url)

    stream, content_type = storage.open(blob.storage_key)
    return Response(stream, mimetype=content_type or blob.content_type or 'application/octet-stream')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
