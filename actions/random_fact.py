"""
Random Fact Action — Rastgele ilginç bilgi / günün sözü.
Kullanım: "Bana ilginç bir şey söyle", "Günün bilgisi", "Rastgele gerçek"
"""
import json
import sys
from pathlib import Path
from random import choice


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def _get_api_key() -> str:
    config_path = _get_base_dir() / "config" / "api_keys.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)["gemini_api_key"]


# Offline yedek bilgiler (API erişimi yoksa)
OFFLINE_FACTS = [
    "Bir ahtapotun 3 kalbi, 9 beyni ve mavi kanı vardır.",
    "Bal asla bozulmaz — arkeologlar Mısır'da 3000 yıllık hâlâ yenilebilir bal bulmuştur.",
    "Bir insan ömrü boyunca ortalama 25 yıl uyur.",
    "Ay her yıl Dünya'dan 3.8 cm uzaklaşıyor.",
    "Bir şimşek, Güneş yüzeyinden 5 kat daha sıcaktır.",
    "İnsan DNA'sının %60'ı muzla ortaktır.",
    "Venüs'ün bir günü, bir yılından daha uzundur.",
    "Köpekbalıkları dinozorlardan önce var olmuştur.",
    "Bir kuş türü olan Arctic Tern, her yıl 70.000 km göç eder.",
    "İnsan beyni uyanıkken küçük bir ampulü yakabilecek kadar elektrik üretir.",
    "Bilinen en eski canlı ağaç 5000 yaşındadır (Methuselah, ABD).",
    "Karıncalar kendi vücut ağırlıklarının 50 katını taşıyabilir.",
    "Mars'taki Olympus Mons, Güneş Sistemi'ndeki en yüksek dağdır — 21.9 km.",
    "Bir insanın yaşamı boyunca yürüdüğü mesafe Dünya'nın çevresinin yaklaşık 5 katıdır.",
    "Buz yüzeyinde kayma aslında buzun erimesiyle oluşan ince su tabakası sayesinde olur.",
    "Kahve dünyada petrolden sonra en çok ticareti yapılan maddedir.",
    "Japonya'da kedilerden fazla evcil hayvan olarak robot köpek vardır.",
    "İnsan gözü yaklaşık 10 milyon farklı renk tonunu ayırt edebilir.",
    "Bir kelebeğin kanatlarındaki desenler, parmak izi kadar benzersizdir.",
    "Evrendeki yıldız sayısı, Dünya'daki tüm kumsalların kum tanelerinden fazladır.",
]

CATEGORIES = [
    "bilim", "uzay", "tarih", "doğa", "teknoloji",
    "insan vücudu", "hayvanlar", "psikoloji", "matematik",
    "coğrafya", "mimarlık", "müzik", "spor", "yemek",
]


def random_fact_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "fact")
    category = params.get("category", "")
    language = params.get("language", "Turkish")

    if player:
        player.write_log(f"[RandomFact] Komut: {action}")

    try:
        import google.generativeai as genai
        genai.configure(api_key=_get_api_key())
        model = genai.GenerativeModel("gemini-2.5-flash")

        if action == "fact":
            cat = category if category else choice(CATEGORIES)
            prompt = (
                f"Tell me ONE fascinating, little-known fact about {cat}. "
                f"Respond in {language}. Max 2 sentences. "
                f"Start directly with the fact, no intro like 'Did you know' etc."
            )
            response = model.generate_content(prompt)
            return f"💡 {response.text.strip()}"

        elif action == "quote":
            prompt = (
                f"Give me ONE inspiring quote from a famous person. "
                f"Include the author. Respond in {language}. "
                f"Format: Quote text — Author Name"
            )
            response = model.generate_content(prompt)
            return f"💬 {response.text.strip()}"

        elif action == "word":
            prompt = (
                f"Teach me ONE interesting/unusual word in any language. "
                f"Give the word, its language, pronunciation, and meaning. "
                f"Respond in {language}. Keep it brief."
            )
            response = model.generate_content(prompt)
            return f"📖 {response.text.strip()}"

        elif action == "riddle":
            prompt = (
                f"Give me ONE clever riddle or brain teaser. "
                f"Respond in {language}. "
                f"Format: Riddle: [question]\\nCevap: [answer]"
            )
            response = model.generate_content(prompt)
            return f"🧩 {response.text.strip()}"

        elif action == "today_in_history":
            from datetime import datetime
            today = datetime.now().strftime("%B %d")
            prompt = (
                f"What is ONE interesting historical event that happened on {today}? "
                f"Respond in {language}. Max 2 sentences. Include the year."
            )
            response = model.generate_content(prompt)
            return f"📜 Tarihte Bugün:\n{response.text.strip()}"

        elif action == "joke":
            prompt = (
                f"Tell me ONE short, clean, clever joke or pun. "
                f"Respond in {language}. Keep it under 3 sentences."
            )
            response = model.generate_content(prompt)
            return f"😄 {response.text.strip()}"

        elif action == "tip":
            tip_topics = [
                "productivity", "health", "coding", "mental health",
                "time management", "learning", "creativity", "fitness"
            ]
            topic = category if category else choice(tip_topics)
            prompt = (
                f"Give me ONE practical, actionable tip about {topic}. "
                f"Respond in {language}. Max 2 sentences."
            )
            response = model.generate_content(prompt)
            return f"🎯 {response.text.strip()}"

        return "Geçersiz komut. Kullanılabilir: fact, quote, word, riddle, today_in_history, joke, tip"

    except Exception as e:
        # Offline fallback
        if action in ("fact", ""):
            return f"💡 {choice(OFFLINE_FACTS)}"
        return f"Bilgi alınamadı: {e}"
