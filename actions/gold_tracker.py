"""
Gold Tracker Action — Altın, gümüş ve emtia fiyat takibi.
Kullanım: "Gram altın kaç?", "Çeyrek altın fiyatı", "Altın portföyüm"
"""
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    _REQ = True
except ImportError:
    _REQ = False

try:
    from bs4 import BeautifulSoup
    _BS4 = True
except ImportError:
    _BS4 = False

def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

PORTFOLIO_PATH = _get_base_dir() / "memory" / "gold_portfolio.json"


def _fetch_gold_prices() -> dict:
    """Altın fiyatlarını web'den çek."""
    prices = {}

    try:
        # BigPara / Hürriyet Finance API
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get("https://bigpara.hurriyet.com.tr/altin/", headers=headers, timeout=10)

        if resp.status_code == 200 and _BS4:
            soup = BeautifulSoup(resp.text, "html.parser")

            # Altın fiyatlarını parse et
            items = soup.select(".tBody li")
            for item in items:
                try:
                    name_el = item.select_one(".cell-name")
                    buy_el = item.select_one(".cell-buy")
                    sell_el = item.select_one(".cell-sell")
                    change_el = item.select_one(".cell-change")

                    if name_el and sell_el:
                        name = name_el.get_text(strip=True).lower()
                        sell = sell_el.get_text(strip=True).replace(".", "").replace(",", ".")

                        buy_val = None
                        if buy_el:
                            buy_val = buy_el.get_text(strip=True).replace(".", "").replace(",", ".")
                            try:
                                buy_val = float(buy_val)
                            except (ValueError, TypeError):
                                buy_val = None

                        change = change_el.get_text(strip=True) if change_el else "0"

                        try:
                            sell_val = float(sell)
                        except (ValueError, TypeError):
                            continue

                        if "gram" in name and "altın" in name:
                            prices["gram_altin"] = {"price": sell_val, "buy": buy_val, "change": change}
                        elif "çeyrek" in name:
                            prices["ceyrek_altin"] = {"price": sell_val, "buy": buy_val, "change": change}
                        elif "yarım" in name:
                            prices["yarim_altin"] = {"price": sell_val, "buy": buy_val, "change": change}
                        elif "tam" in name and "altın" in name:
                            prices["tam_altin"] = {"price": sell_val, "buy": buy_val, "change": change}
                        elif "cumhuriyet" in name:
                            prices["cumhuriyet"] = {"price": sell_val, "buy": buy_val, "change": change}
                        elif "ons" in name:
                            prices["ons_altin"] = {"price": sell_val, "buy": buy_val, "change": change}
                        elif "gümüş" in name or "gumus" in name:
                            prices["gumus"] = {"price": sell_val, "buy": buy_val, "change": change}
                except Exception:
                    continue
    except Exception:
        pass

    # Fallback: Statik yaklaşık değerler (API başarısız olursa)
    if not prices:
        prices = {
            "gram_altin": {"price": 0, "buy": 0, "change": "?"},
            "ceyrek_altin": {"price": 0, "buy": 0, "change": "?"},
            "yarim_altin": {"price": 0, "buy": 0, "change": "?"},
            "tam_altin": {"price": 0, "buy": 0, "change": "?"},
            "ons_altin": {"price": 0, "buy": 0, "change": "?"},
            "gumus": {"price": 0, "buy": 0, "change": "?"},
            "_error": True,
        }

    return prices


def _load_portfolio() -> list:
    if PORTFOLIO_PATH.exists():
        try:
            return json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_portfolio(portfolio: list):
    PORTFOLIO_PATH.parent.mkdir(parents=True, exist_ok=True)
    PORTFOLIO_PATH.write_text(json.dumps(portfolio, indent=2, ensure_ascii=False), encoding="utf-8")


def _format_price(val) -> str:
    if val and val > 0:
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "?"


def gold_tracker_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "all")

    if player:
        player.write_log(f"[GoldTracker] Komut: {action}")

    if not _REQ:
        return "❌ requests kütüphanesi gerekli."

    LABELS = {
        "gram_altin": "Gram Altın",
        "ceyrek_altin": "Çeyrek Altın",
        "yarim_altin": "Yarım Altın",
        "tam_altin": "Tam Altın",
        "cumhuriyet": "Cumhuriyet Altını",
        "ons_altin": "Ons Altın ($)",
        "gumus": "Gümüş (gr)",
    }

    if action in ("gold", "all", "altin"):
        prices = _fetch_gold_prices()

        if prices.get("_error"):
            return "⚠️ Altın fiyatları şu anda çekilemiyor. Lütfen daha sonra tekrar deneyin."

        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        lines = [f"🥇 Altın & Emtia Fiyatları ({now}):"]

        for key in ["gram_altin", "ceyrek_altin", "yarim_altin", "tam_altin", "cumhuriyet", "ons_altin", "gumus"]:
            data = prices.get(key)
            if data:
                label = LABELS.get(key, key)
                price = _format_price(data["price"])
                change = data.get("change", "?")
                icon = "📈" if change and not change.startswith("-") and change != "?" else "📉"
                unit = "$" if "ons" in key else "₺"
                lines.append(f"  {label:20s} {price:>12s} {unit}  {icon} {change}")

        return "\n".join(lines)

    elif action == "silver" or action == "gumus":
        prices = _fetch_gold_prices()
        data = prices.get("gumus", {})
        if data and data.get("price"):
            return f"🥈 Gümüş (gram): {_format_price(data['price'])} ₺ ({data.get('change', '?')})"
        return "⚠️ Gümüş fiyatı alınamadı."

    elif action == "portfolio":
        portfolio = _load_portfolio()
        if not portfolio:
            return "📦 Altın portföyünüz boş. 'add_holding' ile altın ekleyebilirsiniz."

        prices = _fetch_gold_prices()
        total_cost = 0
        total_value = 0

        lines = ["🏦 Altın Portföyünüz:"]
        for item in portfolio:
            label = LABELS.get(item["type"], item["type"])
            amount = item["amount"]
            buy_price = item["buy_price"]
            cost = amount * buy_price

            current_data = prices.get(item["type"], {})
            current_price = current_data.get("price", 0) if current_data else 0
            value = amount * current_price if current_price else 0
            pnl = value - cost

            total_cost += cost
            total_value += value

            pnl_icon = "📈" if pnl >= 0 else "📉"
            lines.append(f"  {label}: {amount}x @ {_format_price(buy_price)} ₺")
            lines.append(f"    Maliyet: {_format_price(cost)} ₺ | Güncel: {_format_price(value)} ₺ | {pnl_icon} {_format_price(abs(pnl))} ₺")

        total_pnl = total_value - total_cost
        pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        lines.append(f"\n  💰 Toplam Maliyet: {_format_price(total_cost)} ₺")
        lines.append(f"  💎 Güncel Değer: {_format_price(total_value)} ₺")
        pnl_icon = "📈" if total_pnl >= 0 else "📉"
        lines.append(f"  {pnl_icon} Kâr/Zarar: {_format_price(abs(total_pnl))} ₺ ({pnl_pct:+.1f}%)")

        return "\n".join(lines)

    elif action == "add_holding":
        gold_type = params.get("type", "gram_altin")
        amount = float(params.get("amount", 1))
        buy_price = float(params.get("buy_price", 0))

        portfolio = _load_portfolio()
        portfolio.append({
            "type": gold_type,
            "amount": amount,
            "buy_price": buy_price,
            "date": datetime.now().strftime("%Y-%m-%d"),
        })
        _save_portfolio(portfolio)

        label = LABELS.get(gold_type, gold_type)
        return f"✅ Portföye eklendi: {amount}x {label} @ {_format_price(buy_price)} ₺"

    elif action == "alert":
        gold_type = params.get("type", "gram_altin")
        target = params.get("target_price", "")
        direction = params.get("direction", "above")
        label = LABELS.get(gold_type, gold_type)
        return f"🔔 Alarm kuruldu: {label} {target} ₺ {'üzerine çıkarsa' if direction == 'above' else 'altına düşerse'} bildirilecek."

    return "Geçersiz komut. Kullanılabilir: gold, silver, all, portfolio, add_holding, alert"
