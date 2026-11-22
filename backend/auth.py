import hashlib
import hmac
import secrets
import time
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from backend.config import signing_key, COOKIE_SECURE
from backend.database import get_db
from backend.models import User

KEY = signing_key()
COOKIE_NAME = "gayatri_session"


def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 600_000
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password, stored):
    try:
        _, salt, digest = stored.split("$")
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 600_000
        ).hex()
        return hmac.compare_digest(digest, actual)
    except ValueError:
        return False


# Equal work for unknown accounts avoids the obvious account timing oracle.
DUMMY_HASH = password_hash(secrets.token_urlsafe(32))


def set_session(response, user):
    token = jwt.encode(
        {
            "sub": str(user.id),
            "iat": int(time.time()),
            "exp": int(time.time()) + 8 * 3600,
        },
        KEY,
        algorithm="HS256",
    )
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=8 * 3600,
        path="/",
    )


def current_user(request: Request, db=Depends(get_db)):
    try:
        token = request.cookies.get(COOKIE_NAME, "")
        claims = jwt.decode(
            token, KEY, algorithms=["HS256"], options={"require": ["sub", "exp", "iat"]}
        )
        user = db.get(User, int(claims["sub"]))
    except (jwt.PyJWTError, ValueError, TypeError):
        user = None
    if not user:
        raise HTTPException(401, "Sign in to continue")
    return user


def admin_user(user=Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required")
    return user
