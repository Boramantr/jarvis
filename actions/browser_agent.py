"""browser_agent — Playwright ile gerçek tarayıcı kontrolü.

Form doldurma, butona basma, sayfadan veri çekme gibi etkileşimli web
işlerini yapar. Senkron API kullanır (asyncio loop'una karışmasın diye
JARVIS zaten her aksiyonu thread executor'da çağırıyor).

Singleton browser: ardışık çağrılarda aynı oturum kullanılır.
"""
from __future__ import annotations

import threading
import time as _time
from typing import Any

try:
    from playwright.sync_api import TimeoutError as PWTimeout
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None
    PWTimeout = Exception  # type: ignore

_lock = threading.Lock()
_state: dict[str, Any] = {
    "pw": None, "browser": None, "context": None, "page": None,
    "last_use": 0.0, "watchdog": None,
}

_DEFAULT_TIMEOUT_MS = 15000
_IDLE_TIMEOUT_S = 300   # 5 dakika işlem yoksa Chromium'u kapat


def _watchdog_loop():
    """Idle ise tarayıcıyı otomatik kapat — RAM'i geri al."""
    while True:
        _time.sleep(30)
        with _lock:
            if _state["page"] is None:
                _state["watchdog"] = None
                return
            if _time.monotonic() - _state["last_use"] > _IDLE_TIMEOUT_S:
                _close_browser_inner()
                _state["watchdog"] = None
                return


def _ensure_browser(headless: bool) -> str | None:
    if sync_playwright is None:
        return "Hata: Playwright yüklü değil. `pip install playwright && playwright install chromium`."
    _state["last_use"] = _time.monotonic()
    if _state["page"] is not None:
        return None
    _state["pw"] = sync_playwright().start()
    _state["browser"] = _state["pw"].chromium.launch(headless=headless)
    _state["context"] = _state["browser"].new_context()
    _state["page"] = _state["context"].new_page()
    _state["page"].set_default_timeout(_DEFAULT_TIMEOUT_MS)
    if _state["watchdog"] is None:
        t = threading.Thread(target=_watchdog_loop, daemon=True, name="browser-idle-watchdog")
        _state["watchdog"] = t
        t.start()
    return None


def _close_browser_inner():
    if _state["browser"]:
        try:
            _state["browser"].close()
        except Exception:
            pass
    if _state["pw"]:
        try:
            _state["pw"].stop()
        except Exception:
            pass
    for k in ("pw", "browser", "context", "page"):
        _state[k] = None


def _close_browser() -> str:
    _close_browser_inner()
    return "Tarayıcı kapatıldı."


def browser_agent_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    action = (params.get("action") or "").strip().lower()
    if not action:
        return "Hata: action gerekli (navigate | click | fill | extract | screenshot | wait | close)."

    headless = bool(params.get("headless", False))

    with _lock:
        if action == "close":
            return _close_browser()

        err = _ensure_browser(headless)
        if err:
            return err
        page = _state["page"]
        if player:
            try:
                player.write_log(f"[browser_agent] {action}")
            except Exception:
                pass

        try:
            if action == "navigate":
                url = (params.get("url") or "").strip()
                if not url:
                    return "Hata: url gerekli."
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                page.goto(url, wait_until="domcontentloaded")
                return f"Açıldı: {page.url}\nBaşlık: {page.title()}"

            if action == "click":
                selector = params.get("selector")
                text = params.get("text")
                if selector:
                    page.click(selector)
                    return f"Tıklandı (selector): {selector}"
                if text:
                    page.get_by_text(text, exact=False).first.click()
                    return f"Tıklandı (metin): {text}"
                return "Hata: selector veya text gerekli."

            if action == "fill":
                selector = params.get("selector") or ""
                value = params.get("value") or ""
                if not selector:
                    return "Hata: selector gerekli."
                page.fill(selector, value)
                if params.get("submit"):
                    page.press(selector, "Enter")
                return f"Dolduruldu: {selector} ← '{value[:50]}'"

            if action == "extract":
                selector = params.get("selector")
                if selector:
                    nodes = page.query_selector_all(selector)
                    if not nodes:
                        return f"'{selector}' ile eşleşen yok."
                    out = [(n.inner_text() or "").strip() for n in nodes[:20]]
                    return "\n---\n".join(t for t in out if t) or "(boş)"
                text = page.evaluate("() => document.body.innerText")
                text = (text or "").strip()
                return text[:8000] or "(sayfa boş)"

            if action == "screenshot":
                path = params.get("path") or "browser_shot.png"
                page.screenshot(path=path, full_page=bool(params.get("full_page")))
                return f"Ekran görüntüsü kaydedildi: {path}"

            if action == "wait":
                selector = params.get("selector")
                if selector:
                    page.wait_for_selector(selector)
                    return f"Beklendi: {selector}"
                ms = int(params.get("ms") or 1000)
                page.wait_for_timeout(ms)
                return f"Beklendi: {ms} ms"

            if action == "current":
                return f"URL: {page.url}\nBaşlık: {page.title()}"

            return f"Hata: bilinmeyen action '{action}'."
        except PWTimeout as e:
            return f"Hata: zaman aşımı ({e})."
        except Exception as e:
            return f"Hata: {type(e).__name__}: {e}"
