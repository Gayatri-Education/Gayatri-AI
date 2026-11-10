import stat
from backend import config


def test_development_session_key_survives_restart_and_is_private(tmp_path, monkeypatch):
    monkeypatch.delenv("PORTAL_SECRET", raising=False)
    monkeypatch.setattr(config, "STATE_DIR", tmp_path)
    first = config.signing_key()
    assert len(first) == 64
    assert config.signing_key() == first
    assert stat.S_IMODE((tmp_path / "session.key").stat().st_mode) == 0o600
