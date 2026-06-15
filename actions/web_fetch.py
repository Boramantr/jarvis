"""web_fetch — bir URL'i indir, içeriği temizleyip metin olarak döndür.

Kullanım: "Şu sayfada ne yazıyor?", "Bu makaleyi özetle", "Şu URL'den fiyatı al"
gibi isteklerde web_search'ten daha keskin bir araç.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}
_MAX_BYTES = 2_000_000   # 2 MB indirme tavanı
_MAX_TEXT = 8000         # döndürülen metin tavanı

# Singleton Session — TCP/TLS keepalive, her çağrıda yeni handshake yok
_session = requests.Session()
_session.headers.update(_HEADERS)


def _clean(text: str) -> str:
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_url(url: str) -> str:
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def web_fetch_action(parameters: dict | None = None, player=None) -> str:
    params = parameters or {}
    url = (params.get("url") or "").strip()
    mode = (params.get("mode") or "text").strip().lower()
    selector = params.get("selector")

    if not url:
        return "Hata: url parametresi gerekli."
    url = _normalize_url(url)

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return f"Hata: yalnızca http/https desteklenir ({parsed.scheme})."
    except Exception as e:
        return f"Hata: geçersiz URL ({e})."

    if player:
        try:
            player.write_log(f"[web_fetch] GET {url}")
        except Exception:
            pass

    try:
        resp = _session.get(url, timeout=15, stream=True)
        resp.raise_for_status()
        content = bytearray()
        for chunk in resp.iter_content(8192):
            content.extend(chunk)
            if len(content) > _MAX_BYTES:
                break
        encoding = resp.encoding or "utf-8"
        html = bytes(content).decode(encoding, errors="replace")
    except requests.HTTPError as e:
        return f"Hata: HTTP {resp.status_code} — {e}"
    except requests.RequestException as e:
        return f"Hata: istek başarısız ({type(e).__name__}: {e})."

    if mode == "raw":
        return _clean(html)[:_MAX_TEXT]

    if BeautifulSoup is None:
        return "Hata: BeautifulSoup yüklü değil. `pip install beautifulsoup4` çalıştır."

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    if mode == "links":
        links = []
        for a in soup.find_all("a", href=True)[:50]:
            label = a.get_text(strip=True)[:80]
            if label:
                links.append(f"- {label} → {a['href']}")
        return "\n".join(links) or "(link bulunamadı)"

    if selector:
        try:
            nodes = soup.select(selector)
        except Exception as e:
            return f"Hata: geçersiz CSS selector ({e})."
        if not nodes:
            return f"Hiçbir element '{selector}' ile eşleşmedi."
        text = "\n\n".join(n.get_text("\n", strip=True) for n in nodes[:20])
    else:
        title = soup.title.get_text(strip=True) if soup.title else ""
        body_text = soup.get_text("\n", strip=True)
        text = f"# {title}\n\n{body_text}" if title else body_text

    text = _clean(text)
    if len(text) > _MAX_TEXT:
        text = text[:_MAX_TEXT] + f"\n... [+{len(text) - _MAX_TEXT} karakter daha]"
    return text or "(içerik boş)"
