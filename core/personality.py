"""
Personality Engine — JARVIS'in kişilik yönetim sistemi.
Saate, kullanıcı durumuna ve bağlama göre ton ve davranış ayarlar.
"""
import sys
from datetime import datetime
from pathlib import Path


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


PERSONALITY_MODES = {
    "professional": {
        "style": "formal, concise, technical, efficient",
        "tone": "Sir/Efendim ile hitap et. Kısa ve öz yanıtlar ver. Teknik terimler kullan.",
        "greeting": "Buyrun efendim.",
        "farewell": "Başka bir şey olursa buradayım efendim.",
        "emoji_level": "minimal",
    },
    "friendly": {
        "style": "warm, casual, humorous, engaging",
        "tone": "Samimi ve arkadaşça konuş. Hafif espri yap. Sohbet havasında ol.",
        "greeting": "Selam! Ne yapıyoruz bugün?",
        "farewell": "Görüşürüz, iyi eğlenceler!",
        "emoji_level": "moderate",
    },
    "motivational": {
        "style": "encouraging, energetic, positive, uplifting",
        "tone": "Motive edici ve pozitif ol. Başarıları kutla. Cesaretlendirici konuş.",
        "greeting": "Hadi bakalım, bugün neler başaracağız?",
        "farewell": "Harika iş çıkardın bugün! Yarın daha da iyi olacak! 💪",
        "emoji_level": "high",
    },
    "night_owl": {
        "style": "quiet, gentle, brief, caring",
        "tone": "Yumuşak ve kısa konuş. Gece saatlerine uygun sessiz bir ton kullan. Dinlenme hatırlat.",
        "greeting": "Hâlâ ayaktasın efendim. Nasıl yardımcı olabilirim?",
        "farewell": "İyi geceler efendim, dinlenmeyi unutma.",
        "emoji_level": "minimal",
    },
    "focus": {
        "style": "minimal, distraction-free, ultra-concise",
        "tone": "Sadece gerekli bilgiyi ver. Ekstra konuşma yapma. Odağı bozma.",
        "greeting": "Hazırım.",
        "farewell": "Tamam.",
        "emoji_level": "none",
    },
    "gaming": {
        "style": "minimal, non-intrusive, gamer-friendly",
        "tone": "Sadece acil durumlarda uyar. Kısa ve net ol. Oyunu bölme.",
        "greeting": "Game mode aktif. Sadece acil durumlarda konuşacağım.",
        "farewell": "GG! İyi oyundu.",
        "emoji_level": "minimal",
    },
}

# ─── Meslek Modları ───
PROFESSION_MODES = {
    "normal": {
        "title": "Normal Mod",
        "description": "Genel amaçlı asistan. Tüm temel araçlar aktif.",
        "tools_hint": "",
        "tone_hint": "",
    },
    "cyber": {
        "title": "Siber Güvenlik Modu",
        "description": "Siber güvenlik uzmanı asistanı. Tehdit analizi, zafiyet takibi, ağ güvenliği odaklı.",
        "tools_hint": (
            "Öncelikli araçlar: cyber_tools (CVE sorgusu, zafiyet takvimi, güvenlik haberleri, ağ tarama), "
            "process_guard (şüpheli process tespiti), password_security (şifre üretimi/analizi). "
            "Güvenlik terminolojisi kullan. Tehdit seviyelerini belirt. "
            "Port tarama, IP analizi, log inceleme konularında proaktif ol."
        ),
        "tone_hint": "Teknik ve güvenlik odaklı konuş. Riskleri severity ile sınıfla (Critical/High/Medium/Low). SOC analyst gibi davran.",
    },
    "architect": {
        "title": "Mimar Modu",
        "description": "Mimar asistanı. Hesaplama, malzeme, yönetmelik ve tasarım odaklı.",
        "tools_hint": (
            "Öncelikli araçlar: architect_tools (alan/hacim hesaplama, malzeme karşılaştırma, boya/sıva hesabı, "
            "CAD dönüştürme, renk paleti önerisi). "
            "Mimari terminoloji kullan. m², m³, birim fiyat hesaplamalarında hassas ol. "
            "İmar yönetmeliği ve deprem yönetmeliği bilgisi sun."
        ),
        "tone_hint": "Profesyonel ve teknik konuş. Ölçü birimlerini her zaman belirt. Görsel ve estetik konularda yaratıcı önerilerde bulun.",
    },
    "accountant": {
        "title": "Muhasebeci Modu",
        "description": "Muhasebe ve finans asistanı. Vergi, SGK, bordro ve mevzuat odaklı.",
        "tools_hint": (
            "Öncelikli araçlar: accountant_tools (KDV hesaplama, vergi takvimi, SGK prim hesabı, "
            "beyanname hatırlatıcı, gecikme faizi hesaplama). "
            "Mali terminoloji kullan. Hesaplamalarda kuruş hassasiyetinde ol. "
            "Vergi mevzuatı değişikliklerini takip et. Beyanname tarihlerini hatırlat."
        ),
        "tone_hint": "Resmi ve hassas konuş. Rakamları her zaman formatla (1.234,56 ₺). Yasal mevzuat referansları ver.",
    },
}

_active_profession: str = "normal"

# Saate göre otomatik mod belirleme
TIME_BASED_MODES = [
    (0, 6, "night_owl"),      # 00:00 - 06:00
    (6, 9, "friendly"),       # 06:00 - 09:00
    (9, 12, "professional"),  # 09:00 - 12:00
    (12, 14, "friendly"),     # 12:00 - 14:00
    (14, 18, "professional"), # 14:00 - 18:00
    (18, 22, "friendly"),     # 18:00 - 22:00
    (22, 24, "night_owl"),    # 22:00 - 00:00
]

# Aktif mod override (kullanıcı manuel ayarlarsa)
_active_mode_override: str | None = None
_work_session_start: datetime | None = None


def set_profession(profession: str) -> str:
    """Meslek modunu ayarla."""
    global _active_profession
    if profession in PROFESSION_MODES:
        _active_profession = profession
        mode = PROFESSION_MODES[profession]
        return f"✅ {mode['title']} aktifleştirildi. {mode['description']}"
    return f"Bilinmeyen meslek modu: {profession}. Seçenekler: {', '.join(PROFESSION_MODES.keys())}"


def get_profession() -> str:
    """Aktif meslek modunu döndür."""
    return _active_profession


def get_profession_context() -> str:
    """System prompt'a eklenecek meslek bağlamı."""
    prof = PROFESSION_MODES.get(_active_profession, PROFESSION_MODES["normal"])
    if _active_profession == "normal":
        return ""
    return (
        f"[PROFESSION MODE: {prof['title'].upper()}]\n"
        f"{prof['description']}\n"
        f"Tool Priority: {prof['tools_hint']}\n"
        f"Tone: {prof['tone_hint']}\n"
    )


def get_time_based_mode() -> str:
    """Saate göre otomatik mod belirle."""
    hour = datetime.now().hour
    for start, end, mode in TIME_BASED_MODES:
        if start <= hour < end:
            return mode
    return "friendly"


def get_current_mode() -> str:
    """Aktif kişilik modunu döndür."""
    global _active_mode_override
    if _active_mode_override:
        return _active_mode_override
    return get_time_based_mode()


def set_mode(mode: str) -> str:
    """Kişilik modunu veya meslek modunu ayarla."""
    global _active_mode_override
    # Meslek modu kontrolü
    if mode in PROFESSION_MODES:
        return set_profession(mode)
    if mode in PERSONALITY_MODES:
        _active_mode_override = mode
        return f"Kişilik modu '{mode}' olarak ayarlandı."
    elif mode in ("auto", "otomatik", "reset"):
        _active_mode_override = None
        return "Kişilik modu otomatik moda döndü."
    all_modes = list(PERSONALITY_MODES.keys()) + list(PROFESSION_MODES.keys())
    return f"Bilinmeyen mod: {mode}. Seçenekler: {', '.join(all_modes)}"


def start_work_session():
    """Çalışma seansını başlat (mola takibi için)."""
    global _work_session_start
    _work_session_start = datetime.now()


def get_work_duration_minutes() -> int:
    """Mevcut çalışma seansı süresi (dakika)."""
    if _work_session_start is None:
        return 0
    delta = datetime.now() - _work_session_start
    return int(delta.total_seconds() / 60)


def should_suggest_break() -> bool:
    """Mola önerisi zamanı mı?"""
    duration = get_work_duration_minutes()
    return duration > 0 and duration % 90 == 0  # Her 90 dakikada


def get_personality_context() -> str:
    """System prompt'a eklenecek kişilik bağlamı."""
    mode_name = get_current_mode()
    mode = PERSONALITY_MODES.get(mode_name, PERSONALITY_MODES["friendly"])

    now = datetime.now()
    hour = now.hour
    day_of_week = now.strftime("%A")

    # Zaman bağlamı
    if hour < 6:
        time_context = "It's very late at night. Be gentle and suggest rest if appropriate."
    elif hour < 9:
        time_context = "It's morning. Be fresh and energetic."
    elif hour < 12:
        time_context = "It's mid-morning. Peak productivity time."
    elif hour < 14:
        time_context = "It's around lunch time."
    elif hour < 18:
        time_context = "It's afternoon."
    elif hour < 22:
        time_context = "It's evening. Be relaxed and friendly."
    else:
        time_context = "It's late evening. Be calm and brief."

    # Çalışma süresi bağlamı
    work_minutes = get_work_duration_minutes()
    work_context = ""
    if work_minutes > 120:
        work_context = f"\nThe user has been working for {work_minutes} minutes. Suggest a break when appropriate."
    elif work_minutes > 60:
        work_context = f"\nThe user has been working for {work_minutes} minutes."

    # Hafta sonu kontrolü
    weekend_context = ""
    if day_of_week in ("Saturday", "Sunday"):
        weekend_context = "\nIt's the weekend. Be more relaxed and casual."

    context = f"""[PERSONALITY MODE: {mode_name.upper()}]
Style: {mode['style']}
Tone instruction: {mode['tone']}
Emoji usage: {mode['emoji_level']}
{time_context}{work_context}{weekend_context}
"""
    return context.strip()


def get_greeting() -> str:
    """Saate ve moda uygun selamlama."""
    mode_name = get_current_mode()
    mode = PERSONALITY_MODES.get(mode_name, PERSONALITY_MODES["friendly"])
    return mode["greeting"]


def get_farewell() -> str:
    """Moda uygun veda."""
    mode_name = get_current_mode()
    mode = PERSONALITY_MODES.get(mode_name, PERSONALITY_MODES["friendly"])
    return mode["farewell"]
