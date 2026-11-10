import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
STATE_DIR = Path(os.getenv("PORTAL_STATE_DIR", ROOT / "var"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{STATE_DIR / 'portal.db'}")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1")
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "")


def signing_key():
    configured = os.getenv("PORTAL_SECRET")
    if configured:
        if len(configured) < 32:
            raise RuntimeError("PORTAL_SECRET must contain at least 32 characters")
        return configured
    # A retained development key avoids invalidating sessions after each restart.
    # Production and multi-instance deployments must set PORTAL_SECRET.
    import secrets

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    key_file = STATE_DIR / "session.key"
    try:
        with open(
            key_file, "x", opener=lambda path, flags: os.open(path, flags, 0o600)
        ) as f:
            f.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    return key_file.read_text().strip()
