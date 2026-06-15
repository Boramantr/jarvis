"""
Calorie Tracker Action — Yemek kalori takibi, BMI hesaplama, günlük hedef.
Kullanım: "Lahmacun kaç kalori?", "Bugün ne kadar yedim?", "BMI hesapla"
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

LOG_PATH = _get_base_dir() / "memory" / "calorie_log.json"

# 🇹🇷 Türk yemekleri kalori veritabanı (porsiyon başına kcal)
FOOD_DATABASE = {
    # Türk yemekleri
    "lahmacun": {"cal": 210, "protein": 9, "fat": 8, "carb": 26, "portion": "1 adet"},
    "döner": {"cal": 450, "protein": 28, "fat": 22, "carb": 35, "portion": "1 porsiyon"},
    "iskender": {"cal": 650, "protein": 35, "fat": 38, "carb": 40, "portion": "1 porsiyon"},
    "pide": {"cal": 380, "protein": 18, "fat": 14, "carb": 42, "portion": "1 dilim"},
    "mantı": {"cal": 350, "protein": 15, "fat": 18, "carb": 30, "portion": "1 porsiyon"},
    "çiğ köfte": {"cal": 180, "protein": 4, "fat": 6, "carb": 28, "portion": "1 porsiyon"},
    "karnıyarık": {"cal": 320, "protein": 14, "fat": 20, "carb": 22, "portion": "1 porsiyon"},
    "imam bayıldı": {"cal": 220, "protein": 4, "fat": 14, "carb": 20, "portion": "1 porsiyon"},
    "mercimek çorbası": {"cal": 150, "protein": 8, "fat": 5, "carb": 20, "portion": "1 kase"},
    "ezogelin çorbası": {"cal": 140, "protein": 6, "fat": 4, "carb": 22, "portion": "1 kase"},
    "tarhana çorbası": {"cal": 130, "protein": 5, "fat": 3, "carb": 22, "portion": "1 kase"},
    "pilav": {"cal": 210, "protein": 4, "fat": 3, "carb": 44, "portion": "1 porsiyon"},
    "bulgur pilavı": {"cal": 190, "protein": 5, "fat": 4, "carb": 36, "portion": "1 porsiyon"},
    "makarna": {"cal": 280, "protein": 10, "fat": 6, "carb": 48, "portion": "1 porsiyon"},
    "köfte": {"cal": 300, "protein": 22, "fat": 20, "carb": 8, "portion": "4 adet"},
    "adana kebab": {"cal": 400, "protein": 30, "fat": 28, "carb": 5, "portion": "1 porsiyon"},
    "urfa kebab": {"cal": 380, "protein": 28, "fat": 26, "carb": 5, "portion": "1 porsiyon"},
    "tavuk göğsü": {"cal": 165, "protein": 31, "fat": 3.6, "carb": 0, "portion": "100g"},
    "tavuk but": {"cal": 209, "protein": 26, "fat": 10.9, "carb": 0, "portion": "100g"},
    "balık": {"cal": 200, "protein": 25, "fat": 10, "carb": 0, "portion": "1 porsiyon"},
    "simit": {"cal": 280, "protein": 8, "fat": 3, "carb": 55, "portion": "1 adet"},
    "poğaça": {"cal": 250, "protein": 5, "fat": 12, "carb": 32, "portion": "1 adet"},
    "börek": {"cal": 300, "protein": 10, "fat": 16, "carb": 30, "portion": "1 dilim"},
    "su böreği": {"cal": 280, "protein": 12, "fat": 14, "carb": 26, "portion": "1 dilim"},
    "gözleme": {"cal": 350, "protein": 12, "fat": 16, "carb": 40, "portion": "1 adet"},
    "tost": {"cal": 320, "protein": 14, "fat": 18, "carb": 26, "portion": "1 adet"},
    "menemen": {"cal": 220, "protein": 12, "fat": 14, "carb": 10, "portion": "1 porsiyon"},
    "omlet": {"cal": 180, "protein": 12, "fat": 14, "carb": 1, "portion": "2 yumurta"},
    "yumurta": {"cal": 78, "protein": 6, "fat": 5, "carb": 0.6, "portion": "1 adet"},
    "peynir": {"cal": 100, "protein": 7, "fat": 8, "carb": 1, "portion": "30g"},
    "zeytin": {"cal": 45, "protein": 0.3, "fat": 4.5, "carb": 1.5, "portion": "10 adet"},
    "salata": {"cal": 80, "protein": 2, "fat": 5, "carb": 8, "portion": "1 tabak"},
    "çoban salata": {"cal": 90, "protein": 2, "fat": 6, "carb": 8, "portion": "1 tabak"},
    "cacık": {"cal": 70, "protein": 4, "fat": 3, "carb": 6, "portion": "1 kase"},
    "ayran": {"cal": 60, "protein": 3, "fat": 2, "carb": 5, "portion": "1 bardak"},
    "çay": {"cal": 2, "protein": 0, "fat": 0, "carb": 0.5, "portion": "1 bardak (şekersiz)"},
    "türk kahvesi": {"cal": 5, "protein": 0.3, "fat": 0.2, "carb": 0.7, "portion": "1 fincan (şekersiz)"},
    "baklava": {"cal": 350, "protein": 6, "fat": 18, "carb": 42, "portion": "1 dilim"},
    "künefe": {"cal": 400, "protein": 8, "fat": 20, "carb": 48, "portion": "1 porsiyon"},
    "sütlaç": {"cal": 200, "protein": 5, "fat": 4, "carb": 38, "portion": "1 kase"},
    "dondurma": {"cal": 200, "protein": 3, "fat": 10, "carb": 24, "portion": "2 top"},
    # Fast food
    "hamburger": {"cal": 500, "protein": 25, "fat": 28, "carb": 38, "portion": "1 adet"},
    "cheeseburger": {"cal": 550, "protein": 28, "fat": 32, "carb": 38, "portion": "1 adet"},
    "pizza": {"cal": 270, "protein": 12, "fat": 10, "carb": 34, "portion": "1 dilim"},
    "patates kızartması": {"cal": 320, "protein": 4, "fat": 15, "carb": 42, "portion": "orta boy"},
    "nugget": {"cal": 280, "protein": 16, "fat": 18, "carb": 16, "portion": "6 adet"},
    "kola": {"cal": 140, "protein": 0, "fat": 0, "carb": 35, "portion": "330ml"},
    "su": {"cal": 0, "protein": 0, "fat": 0, "carb": 0, "portion": "1 bardak"},
    # Meyve
    "elma": {"cal": 52, "protein": 0.3, "fat": 0.2, "carb": 14, "portion": "1 adet (orta)"},
    "muz": {"cal": 105, "protein": 1.3, "fat": 0.4, "carb": 27, "portion": "1 adet"},
    "portakal": {"cal": 62, "protein": 1.2, "fat": 0.2, "carb": 15, "portion": "1 adet"},
    "çilek": {"cal": 50, "protein": 1, "fat": 0.5, "carb": 12, "portion": "1 kase"},
    "karpuz": {"cal": 85, "protein": 1.7, "fat": 0.4, "carb": 21, "portion": "1 dilim"},
    # Atıştırmalık
    "çikolata": {"cal": 230, "protein": 3, "fat": 13, "carb": 25, "portion": "1 bar (40g)"},
    "cips": {"cal": 160, "protein": 2, "fat": 10, "carb": 15, "portion": "1 avuç (30g)"},
    "fındık": {"cal": 180, "protein": 4, "fat": 17, "carb": 5, "portion": "1 avuç (30g)"},
    "badem": {"cal": 170, "protein": 6, "fat": 15, "carb": 6, "portion": "1 avuç (30g)"},
    "kahve": {"cal": 5, "protein": 0.3, "fat": 0, "carb": 0, "portion": "1 fincan (sade)"},
    "latte": {"cal": 190, "protein": 10, "fat": 7, "carb": 19, "portion": "1 bardak"},
    "ekmek": {"cal": 80, "protein": 3, "fat": 1, "carb": 15, "portion": "1 dilim"},
}

PORTION_MULTIPLIERS = {
    "küçük": 0.7, "small": 0.7,
    "orta": 1.0, "medium": 1.0, "normal": 1.0,
    "büyük": 1.5, "large": 1.5,
    "çift": 2.0, "double": 2.0,
    "yarım": 0.5, "half": 0.5,
}


def _load_log() -> dict:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"goal": 2200, "entries": {}}


def _save_log(data: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _find_food(query: str) -> tuple[str, dict] | None:
    query = query.lower().strip()
    if query in FOOD_DATABASE:
        return query, FOOD_DATABASE[query]
    for name, data in FOOD_DATABASE.items():
        if query in name or name in query:
            return name, data
    return None


def calorie_tracker_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "lookup")

    if player:
        player.write_log(f"[CalorieTracker] Komut: {action}")

    if action == "lookup":
        food = params.get("food", "")
        result = _find_food(food)
        if not result:
            return f"❌ '{food}' veritabanında bulunamadı. Yaklaşık değer için Gemini'ye sorabilirsiniz."

        name, data = result
        return (
            f"🍽️ {name.title()} ({data['portion']}):\n"
            f"  🔥 Kalori: {data['cal']} kcal\n"
            f"  🥩 Protein: {data['protein']}g | 🧈 Yağ: {data['fat']}g | 🍞 Karb: {data['carb']}g"
        )

    elif action == "log":
        food = params.get("food", "")
        portion = params.get("portion", "normal").lower()
        result = _find_food(food)

        if not result:
            return f"❌ '{food}' veritabanında bulunamadı."

        name, data = result
        multiplier = PORTION_MULTIPLIERS.get(portion, 1.0)
        cal = int(data["cal"] * multiplier)

        log = _load_log()
        today = date.today().isoformat()
        if today not in log["entries"]:
            log["entries"][today] = []

        log["entries"][today].append({
            "food": name,
            "calories": cal,
            "portion": portion,
            "time": datetime.now().strftime("%H:%M"),
        })
        _save_log(log)

        # Bugünkü toplam
        total = sum(e["calories"] for e in log["entries"][today])
        goal = log.get("goal", 2200)
        remaining = goal - total
        pct = min(total / goal * 100, 100)
        filled = int(pct / 6.67)
        bar = "█" * filled + "░" * (15 - filled)

        return (
            f"✅ Kaydedildi: {name.title()} ({portion}) — {cal} kcal\n"
            f"📊 Bugün: {total} / {goal} kcal\n"
            f"  [{bar}] {pct:.0f}%\n"
            f"  {'🍏 Kalan: ' + str(remaining) + ' kcal' if remaining > 0 else '⚠️ Günlük hedefinizi aştınız!'}"
        )

    elif action == "today":
        log = _load_log()
        today = date.today().isoformat()
        entries = log["entries"].get(today, [])

        if not entries:
            return "📋 Bugün henüz yemek kaydı yok."

        goal = log.get("goal", 2200)
        total = sum(e["calories"] for e in entries)
        remaining = goal - total
        pct = min(total / goal * 100, 100)
        filled = int(pct / 6.67)
        bar = "█" * filled + "░" * (15 - filled)

        lines = [f"📊 Bugünkü Kalori Takibi ({date.today().strftime('%d.%m.%Y')}):"]
        for e in entries:
            lines.append(f"  {e['time']} — {e['food'].title()} ({e['portion']}): {e['calories']} kcal")

        lines.append(f"\n  Toplam: {total} / {goal} kcal")
        lines.append(f"  [{bar}] {pct:.0f}%")
        if remaining > 0:
            lines.append(f"  🍏 Kalan: {remaining} kcal")
        else:
            lines.append(f"  ⚠️ Hedefinizi {abs(remaining)} kcal aştınız!")

        return "\n".join(lines)

    elif action == "goal":
        calories = int(params.get("calories", 2200))
        log = _load_log()
        log["goal"] = calories
        _save_log(log)
        return f"🎯 Günlük kalori hedefi {calories} kcal olarak ayarlandı."

    elif action == "remaining":
        log = _load_log()
        today = date.today().isoformat()
        entries = log["entries"].get(today, [])
        total = sum(e["calories"] for e in entries)
        goal = log.get("goal", 2200)
        remaining = goal - total
        if remaining > 0:
            return f"🍏 Kalan kalori bütçeniz: {remaining} kcal ({total}/{goal})"
        return f"⚠️ Günlük hedefinizi {abs(remaining)} kcal aştınız! ({total}/{goal})"

    elif action == "compare":
        food1 = params.get("food1", "")
        food2 = params.get("food2", "")
        r1 = _find_food(food1)
        r2 = _find_food(food2)

        if not r1:
            return f"❌ '{food1}' bulunamadı."
        if not r2:
            return f"❌ '{food2}' bulunamadı."

        n1, d1 = r1
        n2, d2 = r2

        lines = ["⚖️ Kalori Karşılaştırma:"]
        lines.append(f"  {'':20s} {'🔥 Kcal':>8s} {'🥩 Prot':>8s} {'🧈 Yağ':>8s} {'🍞 Karb':>8s}")
        lines.append(f"  {n1.title():20s} {d1['cal']:>8d} {d1['protein']:>7.1f}g {d1['fat']:>7.1f}g {d1['carb']:>7.1f}g")
        lines.append(f"  {n2.title():20s} {d2['cal']:>8d} {d2['protein']:>7.1f}g {d2['fat']:>7.1f}g {d2['carb']:>7.1f}g")

        diff = d1["cal"] - d2["cal"]
        winner = n1 if diff < 0 else n2
        lines.append(f"\n  💡 {winner.title()} daha düşük kalorili ({abs(diff)} kcal fark)")

        return "\n".join(lines)

    elif action == "bmi":
        weight = float(params.get("weight", 0))
        height = float(params.get("height", 0))

        if weight <= 0 or height <= 0:
            return "❌ Kilo (kg) ve boy (cm) değerleri gerekli."

        height_m = height / 100 if height > 3 else height
        bmi = weight / (height_m ** 2)

        if bmi < 18.5:
            category = "Zayıf"
            icon = "⚠️"
        elif bmi < 25:
            category = "Normal"
            icon = "✅"
        elif bmi < 30:
            category = "Kilolu"
            icon = "🟡"
        else:
            category = "Obez"
            icon = "🔴"

        return (
            f"📏 BMI Hesaplama:\n"
            f"  Boy: {height:.0f} cm | Kilo: {weight:.1f} kg\n"
            f"  BMI: {bmi:.1f} — {icon} {category}\n"
            f"  Normal aralık: 18.5 - 24.9"
        )

    return "Geçersiz komut. Kullanılabilir: lookup, log, today, goal, remaining, compare, bmi"
