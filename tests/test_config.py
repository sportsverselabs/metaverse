"""Tests for the config loader and the pure-Python .env parser."""

from core.config import Config, load_config, load_dotenv


def test_load_config_returns_defaults():
    cfg = load_config()
    assert isinstance(cfg, Config)
    assert cfg.env  # non-empty
    assert cfg.log_level


def test_dotenv_parsing(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# a comment\n"
        "FOO=bar\n"
        'QUOTED="hello world"\n'
        "export EXPORTED=ok\n",
        encoding="utf-8",
    )
    # Ensure a clean slate for these keys.
    for k in ("FOO", "QUOTED", "EXPORTED"):
        monkeypatch.delenv(k, raising=False)

    found = load_dotenv(env_file)
    assert found["FOO"] == "bar"
    assert found["QUOTED"] == "hello world"
    assert found["EXPORTED"] == "ok"


def test_secret_only_reads_env(monkeypatch):
    cfg = load_config()
    monkeypatch.delenv("DOES_NOT_EXIST_KEY", raising=False)
    assert cfg.secret("DOES_NOT_EXIST_KEY") is None
