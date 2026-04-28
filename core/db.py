"""
MongoDB Database Layer for Dialogue Summarizer
All CRUD operations go through this module.
"""
import os
import hashlib
import hmac
import secrets
import datetime
import logging
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from django.conf import settings

logger = logging.getLogger('core.security')


def get_db():
    """Get MongoDB database connection."""
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    return client[settings.MONGODB_DATABASE]


def init_db():
    """Initialize database with indexes and admin account."""
    db = get_db()

    # Create indexes
    db.users.create_index('username', unique=True)
    db.users.create_index('email', unique=True)
    db.sessions.create_index('session_key', unique=True)
    db.sessions.create_index('expire_date', expireAfterSeconds=0)
    db.upload_history.create_index([('user_id', ASCENDING), ('created_at', DESCENDING)])
    db.login_attempts.create_index('ip_address')
    db.login_attempts.create_index('expire_at', expireAfterSeconds=0)

    # Create admin if not exists
    admin = db.users.find_one({'role': 'admin'})
    if not admin:
        admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@123!')
        password_hash, salt = hash_password(admin_password)
        db.users.insert_one({
            'username': settings.ADMIN_USERNAME,
            'email': settings.ADMIN_EMAIL,
            'password_hash': password_hash,
            'salt': salt,
            'role': 'admin',
            'is_active': True,
            'created_at': datetime.datetime.utcnow(),
            'last_login': None,
            'profile': {
                'full_name': 'System Administrator',
                'bio': '',
            },
            'stats': {
                'total_uploads': 0,
                'total_summaries': 0,
            }
        })
        logger.info("Admin account created.")
    return db


# ─── Password Hashing (SHA-256 with PBKDF2 + salt) ───────────────────────────

def hash_password(password: str) -> tuple[str, str]:
    """
    Hash password using PBKDF2-HMAC-SHA256 with a random salt.
    Returns (hash_hex, salt_hex).
    """
    salt = secrets.token_hex(32)  # 256-bit random salt
    # Use PBKDF2 with SHA-256, 310,000 iterations (OWASP recommended)
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        310_000
    )
    password_hash = dk.hex()
    return password_hash, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash using constant-time comparison."""
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        310_000
    )
    candidate_hash = dk.hex()
    return hmac.compare_digest(candidate_hash, stored_hash)


def compute_sha256(content: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


# ─── User Operations ──────────────────────────────────────────────────────────

def create_user(username: str, email: str, password: str, full_name: str) -> dict:
    """Create a new user. Returns {'success': bool, 'error': str|None, 'user': dict|None}."""
    db = get_db()

    # Check if admin slot exists (admin already created at init)
    if username.lower() == settings.ADMIN_USERNAME.lower():
        return {'success': False, 'error': 'Username reserved.', 'user': None}

    password_hash, salt = hash_password(password)
    user_doc = {
        'username': username.lower().strip(),
        'email': email.lower().strip(),
        'password_hash': password_hash,
        'salt': salt,
        'role': 'user',
        'is_active': True,
        'created_at': datetime.datetime.utcnow(),
        'last_login': None,
        'profile': {
            'full_name': full_name,
            'bio': '',
            'avatar_color': secrets.choice([
                '#6366f1', '#8b5cf6', '#ec4899', '#14b8a6',
                '#f59e0b', '#10b981', '#3b82f6', '#ef4444'
            ]),
        },
        'stats': {
            'total_uploads': 0,
            'total_summaries': 0,
        }
    }

    try:
        result = db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        return {'success': True, 'error': None, 'user': user_doc}
    except DuplicateKeyError as e:
        error_str = str(e)
        if 'username' in error_str:
            return {'success': False, 'error': 'Username already exists.', 'user': None}
        elif 'email' in error_str:
            return {'success': False, 'error': 'Email already registered.', 'user': None}
        return {'success': False, 'error': 'Account creation failed.', 'user': None}


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate user. Returns user doc or None."""
    db = get_db()
    user = db.users.find_one({
        '$or': [
            {'username': username.lower().strip()},
            {'email': username.lower().strip()}
        ]
    })
    if not user:
        return None
    if not user.get('is_active', False):
        return None
    if verify_password(password, user['password_hash'], user['salt']):
        # Update last login
        db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.datetime.utcnow()}}
        )
        return user
    return None


def get_user_by_id(user_id: str) -> dict | None:
    """Get user by string ID."""
    from bson import ObjectId
    db = get_db()
    try:
        return db.users.find_one({'_id': ObjectId(user_id)})
    except Exception:
        return None


def get_user_by_username(username: str) -> dict | None:
    db = get_db()
    return db.users.find_one({'username': username.lower().strip()})


def get_all_users(skip=0, limit=20) -> list:
    db = get_db()
    return list(db.users.find({'role': 'user'}, {'password_hash': 0, 'salt': 0})
                .sort('created_at', DESCENDING).skip(skip).limit(limit))


def count_users() -> int:
    db = get_db()
    return db.users.count_documents({'role': 'user'})


def update_user_profile(user_id: str, data: dict) -> bool:
    from bson import ObjectId
    db = get_db()
    allowed_fields = ['profile.full_name', 'profile.bio']
    update = {}
    if 'full_name' in data:
        update['profile.full_name'] = data['full_name']
    if 'bio' in data:
        update['profile.bio'] = data['bio']
    if not update:
        return False
    result = db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update})
    return result.modified_count > 0


def toggle_user_status(user_id: str) -> bool:
    from bson import ObjectId
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user or user.get('role') == 'admin':
        return False
    new_status = not user.get('is_active', True)
    db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'is_active': new_status}})
    return new_status


def delete_user(user_id: str) -> bool:
    from bson import ObjectId
    db = get_db()
    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user or user.get('role') == 'admin':
        return False
    db.users.delete_one({'_id': ObjectId(user_id)})
    db.upload_history.delete_many({'user_id': user_id})
    return True


# ─── Upload / History Operations ──────────────────────────────────────────────

def save_upload_history(user_id: str, filename: str, file_hash: str,
                         file_size: int, action: str, result: str = None) -> dict:
    """Save an upload or fetch action to history."""
    db = get_db()
    doc = {
        'user_id': user_id,
        'filename': filename,
        'file_hash': file_hash,
        'file_size': file_size,
        'action': action,  # 'upload' or 'fetch' or 'summarize'
        'result': result,  # summary text or fetch URL
        'status': 'completed',
        'created_at': datetime.datetime.utcnow(),
    }
    result_ins = db.upload_history.insert_one(doc)
    doc['_id'] = result_ins.inserted_id
    # Update user stats
    db.users.update_one(
        {'_id': __import__('bson').ObjectId(user_id)},
        {'$inc': {
            'stats.total_uploads': 1 if action == 'upload' else 0,
            'stats.total_summaries': 1 if action == 'summarize' else 0,
        }}
    )
    return doc


def get_user_history(user_id: str, skip=0, limit=20) -> list:
    db = get_db()
    return list(db.upload_history.find({'user_id': user_id})
                .sort('created_at', DESCENDING).skip(skip).limit(limit))


def count_user_history(user_id: str) -> int:
    db = get_db()
    return db.upload_history.count_documents({'user_id': user_id})


def get_all_history(skip=0, limit=50) -> list:
    db = get_db()
    return list(db.upload_history.find()
                .sort('created_at', DESCENDING).skip(skip).limit(limit))


def get_system_stats() -> dict:
    db = get_db()
    total_users = db.users.count_documents({'role': 'user'})
    active_users = db.users.count_documents({'role': 'user', 'is_active': True})
    total_uploads = db.upload_history.count_documents({'action': 'upload'})
    total_summaries = db.upload_history.count_documents({'action': 'summarize'})
    today = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_uploads = db.upload_history.count_documents({'created_at': {'$gte': today}})
    return {
        'total_users': total_users,
        'active_users': active_users,
        'total_uploads': total_uploads,
        'total_summaries': total_summaries,
        'today_uploads': today_uploads,
    }


# ─── Login Attempt Tracking (Brute Force Protection) ─────────────────────────

def record_login_attempt(ip_address: str, username: str, success: bool):
    db = get_db()
    db.login_attempts.insert_one({
        'ip_address': ip_address,
        'username': username,
        'success': success,
        'timestamp': datetime.datetime.utcnow(),
        'expire_at': datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.LOCKOUT_DURATION),
    })
    if not success:
        logger.warning(f"Failed login attempt for user '{username}' from IP {ip_address}")


def is_ip_locked(ip_address: str) -> bool:
    db = get_db()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=settings.LOCKOUT_DURATION)
    fail_count = db.login_attempts.count_documents({
        'ip_address': ip_address,
        'success': False,
        'timestamp': {'$gte': cutoff},
    })
    return fail_count >= settings.MAX_LOGIN_ATTEMPTS


# ─── Audit Log (permanent, never deleted) ────────────────────────────────────

def save_audit_log(user_id: str, username: str, email: str, action: str, detail: str = ''):
    """
    Permanent audit log — survives history deletion and account deletion.
    Admin can always see what users did.
    """
    db = get_db()
    db.audit_logs.insert_one({
        'user_id': user_id,
        'username': username,
        'email': email,
        'action': action,
        'detail': detail,
        'timestamp': datetime.datetime.utcnow(),
    })


def get_all_audit_logs(skip=0, limit=50) -> list:
    db = get_db()
    return list(db.audit_logs.find().sort('timestamp', DESCENDING).skip(skip).limit(limit))


def count_audit_logs() -> int:
    db = get_db()
    return db.audit_logs.count_documents({})


# ─── User History Delete Operations ──────────────────────────────────────────

def delete_history_item(user_id: str, item_id: str) -> bool:
    """Delete a single history item belonging to the user."""
    from bson import ObjectId
    db = get_db()
    try:
        result = db.upload_history.delete_one({
            '_id': ObjectId(item_id),
            'user_id': user_id,
        })
        return result.deleted_count > 0
    except Exception:
        return False


def clear_user_history(user_id: str) -> int:
    """Delete ALL history items for a user. Returns count deleted."""
    from bson import ObjectId
    db = get_db()
    result = db.upload_history.delete_many({'user_id': user_id})
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'stats.total_uploads': 0, 'stats.total_summaries': 0}}
    )
    return result.deleted_count


def delete_own_account(user_id: str) -> bool:
    """
    User deletes their own account.
    - User document removed from 'users'
    - Upload history removed
    - Permanent audit snapshot saved to 'audit_logs' (admin can always see it)
    """
    from bson import ObjectId
    db = get_db()
    try:
        user = db.users.find_one({'_id': ObjectId(user_id)})
        if not user or user.get('role') == 'admin':
            return False

        # Save permanent audit snapshot BEFORE deleting
        db.audit_logs.insert_one({
            'user_id': user_id,
            'username': user['username'],
            'email': user['email'],
            'action': 'account_deleted_by_user',
            'detail': (
                f"Account self-deleted. "
                f"Full name: {user['profile'].get('full_name', '')}. "
                f"Member since: {user['created_at']}. "
                f"Uploads: {user['stats'].get('total_uploads', 0)}. "
                f"Summaries: {user['stats'].get('total_summaries', 0)}."
            ),
            'timestamp': datetime.datetime.utcnow(),
            'account_snapshot': {
                'username': user['username'],
                'email': user['email'],
                'full_name': user['profile'].get('full_name', ''),
                'created_at': user['created_at'],
                'last_login': user.get('last_login'),
                'stats': user.get('stats', {}),
            }
        })

        # Delete upload history
        db.upload_history.delete_many({'user_id': user_id})

        # Delete account
        db.users.delete_one({'_id': ObjectId(user_id)})

        logger.warning(f"Account self-deleted: {user['username']} ({user['email']})")
        return True
    except Exception as e:
        logger.error(f"Error deleting account {user_id}: {e}")
        return False
