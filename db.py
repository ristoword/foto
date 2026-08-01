import os
import hashlib
from urllib.parse import urlparse
from datetime import datetime

try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None
    PSYCOPG2_AVAILABLE = False

SCHEMA = "appfoto"


def _get_url():
    return os.environ.get("DATABASE_URL", "")


def _parse(url):
    r = urlparse(url)
    return {
        "dbname": r.path[1:] if r.path else "",
        "user": r.username or "",
        "password": r.password or "",
        "host": r.hostname or "",
        "port": r.port or 5432,
    }


def get_connection():
    if not PSYCOPG2_AVAILABLE:
        return None
    url = _get_url()
    if not url:
        return None
    cfg = _parse(url)
    return psycopg2.connect(**cfg)


def init_db():
    conn = get_connection()
    if not conn:
        return False
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(128) NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.uploads (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
                filename VARCHAR(255),
                saved_path TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA}.jobs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES {SCHEMA}.users(id) ON DELETE CASCADE,
                job_type VARCHAR(50),
                input_summary TEXT,
                output_path TEXT,
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
    conn.close()
    return True


def _hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username, password):
    conn = get_connection()
    if not conn:
        return None
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT id, password_hash FROM {SCHEMA}.users WHERE username = %s",
            (username,),
        )
        row = cur.fetchone()
    conn.close()
    if not row:
        return None
    user_id, pwd_hash = row
    if pwd_hash == _hash_password(password):
        return user_id
    return None


def user_exists(username):
    conn = get_connection()
    if not conn:
        return False
    with conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM {SCHEMA}.users WHERE username = %s", (username,))
        exists = cur.fetchone() is not None
    conn.close()
    return exists


def has_users():
    conn = get_connection()
    if not conn:
        return False
    with conn.cursor() as cur:
        cur.execute(f"SELECT 1 FROM {SCHEMA}.users LIMIT 1")
        exists = cur.fetchone() is not None
    conn.close()
    return exists


def create_user(username, password, is_admin=False):
    conn = get_connection()
    if not conn:
        return False
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {SCHEMA}.users (username, password_hash, is_admin) VALUES (%s, %s, %s)",
            (username, _hash_password(password), is_admin),
        )
        conn.commit()
    conn.close()
    return True


def is_admin(user_id):
    conn = get_connection()
    if not conn or not user_id:
        return False
    with conn.cursor() as cur:
        cur.execute(f"SELECT is_admin FROM {SCHEMA}.users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    conn.close()
    return bool(row and row[0])


def list_users():
    conn = get_connection()
    if not conn:
        return []
    with conn.cursor() as cur:
        cur.execute(f"SELECT id, username, is_admin, created_at FROM {SCHEMA}.users ORDER BY created_at DESC")
        rows = cur.fetchall()
    conn.close()
    return rows


def delete_user(user_id):
    conn = get_connection()
    if not conn:
        return False
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {SCHEMA}.users WHERE id = %s", (user_id,))
        conn.commit()
    conn.close()
    return True


def list_jobs(user_id=None):
    conn = get_connection()
    if not conn:
        return []
    with conn.cursor() as cur:
        if user_id:
            cur.execute(
                f"SELECT id, job_type, input_summary, output_path, status, created_at FROM {SCHEMA}.jobs WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
        else:
            cur.execute(f"""
                SELECT j.id, u.username, j.job_type, j.input_summary, j.output_path, j.status, j.created_at
                FROM {SCHEMA}.jobs j
                JOIN {SCHEMA}.users u ON j.user_id = u.id
                ORDER BY j.created_at DESC
            """)
        rows = cur.fetchall()
    conn.close()
    return rows


def list_uploads(user_id=None):
    conn = get_connection()
    if not conn:
        return []
    with conn.cursor() as cur:
        if user_id:
            cur.execute(
                f"SELECT id, filename, saved_path, created_at FROM {SCHEMA}.uploads WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,),
            )
        else:
            cur.execute(f"""
                SELECT u.id, us.username, u.filename, u.saved_path, u.created_at
                FROM {SCHEMA}.uploads u
                JOIN {SCHEMA}.users us ON u.user_id = us.id
                ORDER BY u.created_at DESC
            """)
        rows = cur.fetchall()
    conn.close()
    return rows


def log_job(user_id, job_type, input_summary, output_path, status="ok"):
    conn = get_connection()
    if not conn:
        return
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {SCHEMA}.jobs (user_id, job_type, input_summary, output_path, status) VALUES (%s, %s, %s, %s, %s)",
            (user_id, job_type, input_summary, output_path, status),
        )
        conn.commit()
    conn.close()


def log_upload(user_id, filename, saved_path):
    conn = get_connection()
    if not conn:
        return
    with conn.cursor() as cur:
        cur.execute(
            f"INSERT INTO {SCHEMA}.uploads (user_id, filename, saved_path) VALUES (%s, %s, %s)",
            (user_id, filename, saved_path),
        )
        conn.commit()
    conn.close()
