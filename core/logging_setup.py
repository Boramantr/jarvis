"""Merkezi logging yapılandırması.

- Konsol: insan-okur, renkli değil (Windows uyumlu).
- Dosya: ~/.jarvis/logs/jarvis.log, döner (10MB x 5 backup).
- Sentry: yalnızca SENTRY_DSN env varsa aktifleşir (opsiyonel, sentry-sdk kuruluysa).

main.py'den `setup_logging()` bir kez çağrılır.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path.home() / ".jarvis" / "logs"
_configured = False


class _SafeStreamHandler(logging.StreamHandler):
    """Windows cp1252 konsolunda emoji/unicode patlamasını yutar."""

    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            try:
                msg = self.format(record).encode("ascii", "replace").decode("ascii")
                self.stream.write(msg + self.terminator)
                self.flush()
            except Exception:
                pass


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    global _configured
    log = logging.getLogger("jarvis")
    if _configured:
        return log

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    log.setLevel(level)
    log.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Konsol
    ch = _SafeStreamHandler(sys.stderr)
    ch.setLevel(level)
    ch.setFormatter(fmt)
    log.addHandler(ch)

    # Dosya (döner)
    fh = RotatingFileHandler(
        _LOG_DIR / "jarvis.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    log.addHandler(fh)

    # Gürültülü 3rd-party logger'ları kıs
    for noisy in ("httpx", "httpcore", "uvicorn.access", "google_genai", "websockets", "comtypes"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _maybe_init_sentry(log)

    _configured = True
    log.info("Logging hazır → %s", _LOG_DIR / "jarvis.log")
    return log


def _maybe_init_sentry(log: logging.Logger) -> None:
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return
    try:
        import sentry_sdk
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.0, send_default_pii=False)
        log.info("Sentry aktif (error tracking)")
    except ImportError:
        log.warning("SENTRY_DSN var ama sentry-sdk kurulu değil — `pip install sentry-sdk`")
    except Exception:
        log.exception("Sentry init başarısız")
