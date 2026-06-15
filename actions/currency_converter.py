"""
Currency Converter Action — Anlık döviz kuru çevirici.
Kullanım: "100 dolar kaç TL?", "Euro-Dolar paritesi ne?", "Döviz kurlarını göster"
"""
import json
import urllib.request
from datetime import datetime, timedelta

# Sık kullanılan para birimleri
CURRENCY_ALIASES = {
    "dolar": "USD", "dollar": "USD", "$": "USD", "usd": "USD",
    "euro": "EUR", "€": "EUR", "eur": "EUR",
    "sterlin": "GBP", "pound": "GBP", "£": "GBP", "gbp": "GBP",
    "tl": "TRY", "lira": "TRY", "türk lirası": "TRY", "try": "TRY",
    "yen": "JPY", "¥": "JPY", "jpy": "JPY",
    "won": "KRW", "krw": "KRW",
    "ruble": "RUB", "rub": "RUB",
    "yuan": "CNY", "cny": "CNY",
    "frank": "CHF", "chf": "CHF",
    "bitcoin": "BTC", "btc": "BTC",
    "altın": "XAU", "gold": "XAU",
}

_rate_cache: dict = {}
_cache_time: datetime = datetime.min


def _resolve_currency(input_str: str) -> str:
    """Para birimi adını veya kısaltmasını standart koda çevir."""
    key = input_str.lower().strip()
    if key in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[key]
    return input_str.upper().strip()


def _fetch_rates(base: str = "USD") -> dict:
    """Exchangerate API'den güncel kurları çek."""
    global _rate_cache, _cache_time

    if _rate_cache and datetime.now() - _cache_time < timedelta(minutes=30):
        return _rate_cache

    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{base}"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            _rate_cache = data.get("rates", {})
            _cache_time = datetime.now()
            return _rate_cache
    except Exception:
        pass

    # Fallback: Open Exchange Rates (ücretsiz)
    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            _rate_cache = data.get("rates", {})
            _cache_time = datetime.now()
            return _rate_cache
    except Exception as e:
        raise RuntimeError(f"Döviz kurları alınamadı: {e}")


def currency_converter_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "convert")
    amount_str = params.get("amount", "1")
    from_currency = params.get("from", "USD")
    to_currency = params.get("to", "TRY")

    if player:
        player.write_log(f"[Currency] {action}: {from_currency} → {to_currency}")

    from_code = _resolve_currency(from_currency)
    to_code = _resolve_currency(to_currency)

    try:
        amount = float(str(amount_str).replace(",", "."))
    except (ValueError, TypeError):
        amount = 1.0

    try:
        if action == "convert":
            rates = _fetch_rates(from_code)
            if to_code not in rates:
                return f"'{to_code}' para birimi bulunamadı efendim."

            rate = rates[to_code]
            result = amount * rate
            return (
                f"💱 {amount:,.2f} {from_code} = {result:,.2f} {to_code}\n"
                f"   Kur: 1 {from_code} = {rate:,.4f} {to_code}"
            )

        elif action == "rates":
            rates = _fetch_rates("USD")
            popular = ["TRY", "EUR", "GBP", "JPY", "CHF", "CNY", "KRW", "RUB"]
            lines = ["💰 Güncel Döviz Kurları (1 USD karşılığı):"]
            for code in popular:
                if code in rates:
                    lines.append(f"  {code}: {rates[code]:,.4f}")
            return "\n".join(lines)

        elif action == "gold":
            rates = _fetch_rates("XAU")
            if "TRY" in rates:
                gold_try = rates["TRY"]
                gold_gram = gold_try / 31.1035  # troy ons → gram
                return (
                    f"🥇 Altın Fiyatları:\n"
                    f"  1 Ons = {gold_try:,.2f} TRY\n"
                    f"  1 Gram = {gold_gram:,.2f} TRY"
                )
            return "Altın fiyatı alınamadı."

        elif action == "compare":
            base = _resolve_currency(params.get("base", "TRY"))
            currencies = params.get("currencies", ["USD", "EUR", "GBP"])
            if isinstance(currencies, str):
                currencies = [c.strip() for c in currencies.split(",")]
            currencies = [_resolve_currency(c) for c in currencies]

            rates = _fetch_rates(base)
            lines = [f"📊 {base} karşılaştırması:"]
            for code in currencies:
                if code in rates:
                    lines.append(f"  1 {base} = {rates[code]:,.4f} {code}")
            return "\n".join(lines)

        return "Geçersiz döviz komutu. Kullanılabilir: convert, rates, gold, compare"

    except Exception as e:
        return f"Döviz çevirme hatası: {e}"
