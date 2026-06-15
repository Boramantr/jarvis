"""
World Info Action — Ülke bilgileri, vize durumu, saat farkı, priz tipi, acil numaralar.
Kullanım: "Tokyo'da saat kaç?", "Japonya vizesi gerekiyor mu?", "İngiltere priz tipi ne?"
"""
from datetime import UTC, datetime, timedelta

try:
    import requests
    _REQ = True
except ImportError:
    _REQ = False

# Türk vatandaşları için vize bilgileri (yaygın ülkeler)
VISA_INFO = {
    "almanya": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "fransa": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "italya": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "ispanya": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "hollanda": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "belçika": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "avusturya": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "yunanistan": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "portekiz": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "isviçre": {"status": "Schengen vizesi gerekli", "type": "vize", "note": "Schengen vizesi ile giriş."},
    "ingiltere": {"status": "Vize gerekli", "type": "vize", "note": "UK Standard Visitor Visa başvurusu yapılmalı."},
    "abd": {"status": "Vize gerekli (B1/B2)", "type": "vize", "note": "ABD Büyükelçiliği'nden randevu alınmalı."},
    "kanada": {"status": "Vize gerekli (eTA/Visitor)", "type": "vize", "note": "Online veya büyükelçilik başvurusu."},
    "japonya": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Turistik amaçlı 90 gün vizesiz giriş."},
    "güney kore": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Turistik 90 gün."},
    "brezilya": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Turistik 90 gün."},
    "arjantin": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Turistik 90 gün."},
    "gürcistan": {"status": "1 yıl vizesiz", "type": "vizesiz", "note": "Kimlikle giriş. 1 yıl kalış hakkı."},
    "azerbaycan": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Kimlikle giriş."},
    "katar": {"status": "30 gün vizesiz", "type": "vizesiz", "note": "Kapıda ücretsiz vize."},
    "tayland": {"status": "30 gün vizesiz", "type": "vizesiz", "note": "Kapıda 30 gün. Uzatılabilir."},
    "malezya": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Turistik 90 gün."},
    "singapur": {"status": "30 gün vizesiz", "type": "vizesiz", "note": "Turistik 30 gün."},
    "ukrayna": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Turistik 90 gün."},
    "mısır": {"status": "Kapıda vize", "type": "kapıda_vize", "note": "Havaalanında vize alınır (~25$)."},
    "ürdün": {"status": "Kapıda vize", "type": "kapıda_vize", "note": "Havaalanında vize (~40 JOD)."},
    "endonezya": {"status": "Kapıda vize (30 gün)", "type": "kapıda_vize", "note": "Bali dahil. Kapıda 35$."},
    "moldova": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Turistik 90 gün."},
    "bosna hersek": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Kimlikle giriş."},
    "sırbistan": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Kimlikle giriş."},
    "karadağ": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Kimlikle giriş."},
    "kuzey makedonya": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Kimlikle giriş."},
    "arnavutluk": {"status": "90 gün vizesiz", "type": "vizesiz", "note": "Kimlikle giriş."},
    "avustralya": {"status": "Vize gerekli (eVisitor)", "type": "vize", "note": "Online vize başvurusu."},
    "rusya": {"status": "Vize gerekli", "type": "vize", "note": "E-vize mümkün bazı kapılardan."},
    "çin": {"status": "Vize gerekli", "type": "vize", "note": "Büyükelçilik başvurusu."},
    "hindistan": {"status": "E-vize", "type": "e-vize", "note": "Online e-vize başvurusu."},
}

# Priz tipleri
PLUG_TYPES = {
    "türkiye": {"type": "C, F", "voltage": "220V", "frequency": "50Hz"},
    "almanya": {"type": "C, F", "voltage": "230V", "frequency": "50Hz"},
    "fransa": {"type": "C, E", "voltage": "230V", "frequency": "50Hz"},
    "ingiltere": {"type": "G", "voltage": "230V", "frequency": "50Hz"},
    "abd": {"type": "A, B", "voltage": "120V", "frequency": "60Hz"},
    "kanada": {"type": "A, B", "voltage": "120V", "frequency": "60Hz"},
    "japonya": {"type": "A, B", "voltage": "100V", "frequency": "50/60Hz"},
    "avustralya": {"type": "I", "voltage": "230V", "frequency": "50Hz"},
    "çin": {"type": "A, C, I", "voltage": "220V", "frequency": "50Hz"},
    "hindistan": {"type": "C, D, M", "voltage": "230V", "frequency": "50Hz"},
    "brezilya": {"type": "C, N", "voltage": "127/220V", "frequency": "60Hz"},
    "güney kore": {"type": "C, F", "voltage": "220V", "frequency": "60Hz"},
    "italya": {"type": "C, F, L", "voltage": "230V", "frequency": "50Hz"},
    "ispanya": {"type": "C, F", "voltage": "230V", "frequency": "50Hz"},
    "rusya": {"type": "C, F", "voltage": "220V", "frequency": "50Hz"},
    "tayland": {"type": "A, B, C, O", "voltage": "220V", "frequency": "50Hz"},
    "singapur": {"type": "G", "voltage": "230V", "frequency": "50Hz"},
    "mısır": {"type": "C, F", "voltage": "220V", "frequency": "50Hz"},
}

# Saat dilimleri (UTC offset)
TIMEZONES = {
    "tokyo": +9, "osaka": +9, "japonya": +9,
    "new york": -5, "washington": -5,
    "los angeles": -8, "san francisco": -8,
    "londra": 0, "ingiltere": 0,
    "paris": +1, "fransa": +1,
    "berlin": +1, "almanya": +1,
    "roma": +1, "italya": +1,
    "madrid": +1, "ispanya": +1,
    "moskova": +3, "rusya": +3,
    "dubai": +4, "bae": +4,
    "pekin": +8, "şanghay": +8, "çin": +8,
    "seoul": +9, "güney kore": +9,
    "sydney": +11, "avustralya": +11,
    "singapur": +8,
    "bangkok": +7, "tayland": +7,
    "kahire": +2, "mısır": +2,
    "istanbul": +3, "türkiye": +3, "ankara": +3,
    "mumbai": +5.5, "hindistan": +5.5,
    "são paulo": -3, "brezilya": -3,
    "buenos aires": -3, "arjantin": -3,
    "toronto": -5, "kanada": -5,
    "hawaii": -10,
}

# Acil numaralar
EMERGENCY_NUMBERS = {
    "türkiye": {"polis": "155", "ambulans": "112", "itfaiye": "110", "genel": "112"},
    "abd": {"polis": "911", "ambulans": "911", "itfaiye": "911", "genel": "911"},
    "ingiltere": {"polis": "999", "ambulans": "999", "itfaiye": "999", "genel": "112/999"},
    "almanya": {"polis": "110", "ambulans": "112", "itfaiye": "112", "genel": "112"},
    "fransa": {"polis": "17", "ambulans": "15", "itfaiye": "18", "genel": "112"},
    "japonya": {"polis": "110", "ambulans": "119", "itfaiye": "119", "genel": "110/119"},
    "güney kore": {"polis": "112", "ambulans": "119", "itfaiye": "119", "genel": "112"},
    "avustralya": {"polis": "000", "ambulans": "000", "itfaiye": "000", "genel": "000"},
    "kanada": {"polis": "911", "ambulans": "911", "itfaiye": "911", "genel": "911"},
    "italya": {"polis": "113", "ambulans": "118", "itfaiye": "115", "genel": "112"},
    "ispanya": {"polis": "091", "ambulans": "061", "itfaiye": "080", "genel": "112"},
    "rusya": {"polis": "102", "ambulans": "103", "itfaiye": "101", "genel": "112"},
    "çin": {"polis": "110", "ambulans": "120", "itfaiye": "119", "genel": "110"},
    "hindistan": {"polis": "100", "ambulans": "102", "itfaiye": "101", "genel": "112"},
    "brezilya": {"polis": "190", "ambulans": "192", "itfaiye": "193", "genel": "190"},
    "mısır": {"polis": "122", "ambulans": "123", "itfaiye": "180", "genel": "122"},
}

COUNTRY_DATA = {
    "japonya": {"capital": "Tokyo", "population": "125.7M", "currency": "Yen (¥)", "languages": "Japonca", "continent": "Asya", "drive": "Sol"},
    "abd": {"capital": "Washington D.C.", "population": "331M", "currency": "Dolar ($)", "languages": "İngilizce", "continent": "Kuzey Amerika", "drive": "Sağ"},
    "ingiltere": {"capital": "Londra", "population": "67M", "currency": "Sterlin (£)", "languages": "İngilizce", "continent": "Avrupa", "drive": "Sol"},
    "almanya": {"capital": "Berlin", "population": "83M", "currency": "Euro (€)", "languages": "Almanca", "continent": "Avrupa", "drive": "Sağ"},
    "fransa": {"capital": "Paris", "population": "67M", "currency": "Euro (€)", "languages": "Fransızca", "continent": "Avrupa", "drive": "Sağ"},
    "italya": {"capital": "Roma", "population": "60M", "currency": "Euro (€)", "languages": "İtalyanca", "continent": "Avrupa", "drive": "Sağ"},
    "ispanya": {"capital": "Madrid", "population": "47M", "currency": "Euro (€)", "languages": "İspanyolca", "continent": "Avrupa", "drive": "Sağ"},
    "güney kore": {"capital": "Seul", "population": "51.7M", "currency": "Won (₩)", "languages": "Korece", "continent": "Asya", "drive": "Sağ"},
    "çin": {"capital": "Pekin", "population": "1.4B", "currency": "Yuan (¥)", "languages": "Mandarin Çince", "continent": "Asya", "drive": "Sağ"},
    "hindistan": {"capital": "Yeni Delhi", "population": "1.4B", "currency": "Rupi (₹)", "languages": "Hintçe, İngilizce", "continent": "Asya", "drive": "Sol"},
    "rusya": {"capital": "Moskova", "population": "144M", "currency": "Ruble (₽)", "languages": "Rusça", "continent": "Avrupa/Asya", "drive": "Sağ"},
    "avustralya": {"capital": "Canberra", "population": "25.7M", "currency": "Avustralya Doları (A$)", "languages": "İngilizce", "continent": "Okyanusya", "drive": "Sol"},
    "kanada": {"capital": "Ottawa", "population": "38M", "currency": "Kanada Doları (C$)", "languages": "İngilizce, Fransızca", "continent": "Kuzey Amerika", "drive": "Sağ"},
    "brezilya": {"capital": "Brasília", "population": "213M", "currency": "Real (R$)", "languages": "Portekizce", "continent": "Güney Amerika", "drive": "Sağ"},
    "mısır": {"capital": "Kahire", "population": "102M", "currency": "Mısır Lirası (EGP)", "languages": "Arapça", "continent": "Afrika", "drive": "Sağ"},
    "tayland": {"capital": "Bangkok", "population": "70M", "currency": "Baht (฿)", "languages": "Tayca", "continent": "Asya", "drive": "Sol"},
    "singapur": {"capital": "Singapur", "population": "5.9M", "currency": "Singapur Doları (S$)", "languages": "İngilizce, Mandarin, Malay, Tamil", "continent": "Asya", "drive": "Sol"},
}


def _find_country(query: str) -> str | None:
    query = query.lower().strip()
    # Direkt eşleşme
    if query in COUNTRY_DATA:
        return query
    # Kısmi eşleşme
    for key in COUNTRY_DATA:
        if query in key or key in query:
            return key
    # Şehirden ülke bul
    city_to_country = {
        "tokyo": "japonya", "osaka": "japonya", "new york": "abd", "washington": "abd",
        "londra": "ingiltere", "paris": "fransa", "berlin": "almanya", "roma": "italya",
        "madrid": "ispanya", "moskova": "rusya", "pekin": "çin", "şanghay": "çin",
        "seoul": "güney kore", "sydney": "avustralya", "toronto": "kanada",
        "mumbai": "hindistan", "bangkok": "tayland", "kahire": "mısır",
    }
    return city_to_country.get(query)


def world_info_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "country")

    if player:
        player.write_log(f"[WorldInfo] Komut: {action}")

    query = params.get("name", "") or params.get("country", "") or params.get("city", "") or params.get("destination", "")
    query = query.lower().strip()

    if action == "country":
        country = _find_country(query)
        if not country or country not in COUNTRY_DATA:
            return f"❌ '{query}' hakkında bilgi bulunamadı. Desteklenen ülkeler: {', '.join(sorted(COUNTRY_DATA.keys()))}"

        data = COUNTRY_DATA[country]
        visa = VISA_INFO.get(country, {})
        plug = PLUG_TYPES.get(country, {})
        emerg = EMERGENCY_NUMBERS.get(country, {})
        tz_offset = None
        for k, v in TIMEZONES.items():
            if country in k or k in country:
                tz_offset = v
                break

        lines = [f"🌍 {country.title()}:"]
        lines.append(f"  🏛️ Başkent: {data['capital']}")
        lines.append(f"  👥 Nüfus: {data['population']}")
        lines.append(f"  💵 Para: {data['currency']}")
        lines.append(f"  🗣️ Dil: {data['languages']}")
        lines.append(f"  🌐 Kıta: {data['continent']}")
        lines.append(f"  🚗 Trafik: {data['drive']} şerit")

        if tz_offset is not None:
            now_utc = datetime.now(UTC)
            local = now_utc + timedelta(hours=tz_offset)
            diff = tz_offset - 3  # TR = UTC+3
            lines.append(f"  🕐 Saat: {local.strftime('%H:%M')} (TR {'+'if diff>=0 else ''}{diff:.0f} saat)")

        if plug:
            lines.append(f"  🔌 Priz: Tip {plug['type']} — {plug['voltage']} {plug['frequency']}")

        if visa:
            icon = "✅" if visa["type"] == "vizesiz" else "🟡" if visa["type"] in ("kapıda_vize", "e-vize") else "🔴"
            lines.append(f"  🛂 {icon} Vize: {visa['status']}")
            lines.append(f"     ℹ️ {visa['note']}")

        if emerg:
            lines.append(f"  📞 Acil: Polis {emerg.get('polis', '?')}, Ambulans {emerg.get('ambulans', '?')}, İtfaiye {emerg.get('itfaiye', '?')}")

        return "\n".join(lines)

    elif action == "time":
        offset = TIMEZONES.get(query)
        if offset is None:
            # Ülke adıyla dene
            for k, v in TIMEZONES.items():
                if query in k or k in query:
                    offset = v
                    break

        if offset is None:
            return f"❌ '{query}' için saat dilimi bulunamadı."

        now_utc = datetime.now(UTC)
        local = now_utc + timedelta(hours=offset)
        diff = offset - 3
        return f"🕐 {query.title()}: {local.strftime('%H:%M (%d.%m.%Y)')} — TR'den {'+'if diff>=0 else ''}{diff:.0f} saat fark"

    elif action == "visa":
        country = _find_country(query) or query
        visa = VISA_INFO.get(country)
        if not visa:
            return f"❌ '{query}' için vize bilgisi bulunamadı. Lütfen güncel bilgi için konsolosluk sitesini kontrol edin."

        icon = "✅" if visa["type"] == "vizesiz" else "🟡" if visa["type"] in ("kapıda_vize", "e-vize") else "🔴"
        return f"🛂 {country.title()} — {icon} {visa['status']}\n   ℹ️ {visa['note']}"

    elif action == "plug":
        country = _find_country(query) or query
        plug = PLUG_TYPES.get(country)
        if not plug:
            return f"❌ '{query}' için priz bilgisi bulunamadı."
        tr_plug = PLUG_TYPES["türkiye"]
        compatible = any(t.strip() in plug["type"] for t in tr_plug["type"].split(","))
        compat_msg = "✅ TR fişi uyumlu" if compatible else "⚠️ TR fişi uyumsuz — adaptör gerekli"
        return f"🔌 {country.title()}: Tip {plug['type']} — {plug['voltage']} {plug['frequency']}\n   {compat_msg}"

    elif action == "emergency":
        country = _find_country(query) or query
        emerg = EMERGENCY_NUMBERS.get(country)
        if not emerg:
            return f"❌ '{query}' için acil numara bilgisi bulunamadı. Genel acil numara: 112"
        lines = [f"📞 {country.title()} Acil Numaraları:"]
        lines.append(f"  🚔 Polis: {emerg['polis']}")
        lines.append(f"  🚑 Ambulans: {emerg['ambulans']}")
        lines.append(f"  🚒 İtfaiye: {emerg['itfaiye']}")
        lines.append(f"  📱 Genel: {emerg['genel']}")
        return "\n".join(lines)

    elif action == "safety":
        country = _find_country(query) or query
        return f"🌍 {country.title()} güvenlik bilgisi için Dışişleri Bakanlığı seyahat uyarılarını kontrol etmenizi öneririm: https://www.mfa.gov.tr/ulke-bilgileri.tr.mfa"

    return "Geçersiz komut. Kullanılabilir: country, time, visa, plug, emergency, safety"
