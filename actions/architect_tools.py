"""
Architect Tools Action — Mimar yardımcı araçları.
Alan/hacim hesaplama, malzeme karşılaştırma, boya hesabı, CAD dönüşüm, renk paleti.
Kullanım: "5x8 odanın alanı", "100m² boya hesapla", "Modern renk paleti öner"
"""
import math

# Malzeme veritabanı
MATERIALS = {
    "seramik": {
        "birim_fiyat": "250-800 ₺/m²",
        "dayanıklılık": "Yüksek",
        "bakım": "Kolay",
        "uygun_mekan": "Mutfak, banyo, giriş",
        "pei": "PEI 3-5",
        "su_emme": "<%0.5 - %6",
    },
    "laminat": {
        "birim_fiyat": "150-500 ₺/m²",
        "dayanıklılık": "Orta-Yüksek",
        "bakım": "Kolay",
        "uygun_mekan": "Salon, yatak odası, ofis",
        "ac_sinif": "AC3-AC5",
        "su_emme": "Suya dayanıksız",
    },
    "parke": {
        "birim_fiyat": "400-1500 ₺/m²",
        "dayanıklılık": "Orta",
        "bakım": "Zor (cilalama gerekir)",
        "uygun_mekan": "Salon, yatak odası",
        "not": "Doğal ahşap, sıcak görünüm",
    },
    "mermer": {
        "birim_fiyat": "600-3000 ₺/m²",
        "dayanıklılık": "Orta (çizilir)",
        "bakım": "Zor (leke tutar)",
        "uygun_mekan": "Giriş, banyo, tezgah",
        "not": "Lüks görünüm, ağır",
    },
    "granit": {
        "birim_fiyat": "500-2000 ₺/m²",
        "dayanıklılık": "Çok Yüksek",
        "bakım": "Kolay",
        "uygun_mekan": "Mutfak tezgahı, dış cephe, zemin",
        "not": "Çizilmez, asit dayanıklı",
    },
    "vinil": {
        "birim_fiyat": "100-400 ₺/m²",
        "dayanıklılık": "Orta",
        "bakım": "Çok Kolay",
        "uygun_mekan": "Her mekan (su geçirmez)",
        "not": "LVT/LVP, hızlı montaj",
    },
    "doğal taş": {
        "birim_fiyat": "300-2500 ₺/m²",
        "dayanıklılık": "Yüksek",
        "bakım": "Orta",
        "uygun_mekan": "Dış cephe, bahçe, şömine",
    },
    "cam": {
        "birim_fiyat": "200-1200 ₺/m²",
        "dayanıklılık": "Kırılgan",
        "bakım": "Kolay",
        "uygun_mekan": "Pencere, bölme, vitrin",
        "not": "Temperli/lamine güvenlik camı tercih edilmeli",
    },
}

# Renk paletleri
COLOR_PALETTES = {
    "modern": {
        "colors": ["#2C3E50 (Kömür)", "#ECF0F1 (Bulut)", "#3498DB (Okyanus)", "#E74C3C (Mercan)", "#1ABC9C (Turkuaz)"],
        "mood": "Çağdaş, şık, dengeli",
    },
    "skandinav": {
        "colors": ["#F5F5F0 (Krem Beyaz)", "#D5C4A1 (Kum)", "#8B7355 (Meşe)", "#6B8F71 (Adaçayı)", "#2F4F4F (Koyu Orman)"],
        "mood": "Sade, doğal, huzurlu",
    },
    "minimalist": {
        "colors": ["#FFFFFF (Beyaz)", "#F2F2F2 (Açık Gri)", "#333333 (Antrasit)", "#000000 (Siyah)", "#C0B283 (Altın Kum)"],
        "mood": "Temiz, net, sofistike",
    },
    "endüstriyel": {
        "colors": ["#36454F (Kömür)", "#708090 (Çelik)", "#B87333 (Bakır)", "#8B4513 (Tuğla)", "#F5F5DC (Bej)"],
        "mood": "Ham, güçlü, kentsel",
    },
    "akdeniz": {
        "colors": ["#FFFFFF (Beyaz)", "#1E90FF (Ege Mavisi)", "#DAA520 (Altın)", "#228B22 (Zeytin)", "#F4A460 (Kum)"],
        "mood": "Aydınlık, canlı, tatil havası",
    },
    "japon": {
        "colors": ["#F5F0E1 (Washi)", "#5B7065 (Matcha)", "#8B4513 (Ahşap)", "#2F2F2F (Sumi)", "#C41E3A (Akane)"],
        "mood": "Zen, huzurlu, dengeli",
    },
    "boho": {
        "colors": ["#E8D5B7 (Kum)", "#B8860B (Hardal)", "#8B0000 (Bordo)", "#2E8B57 (Yeşil)", "#4682B4 (Çivit)"],
        "mood": "Eklektik, sıcak, yaratıcı",
    },
    "lüks": {
        "colors": ["#1C1C1C (Siyah)", "#C0A062 (Altın)", "#4A0E2E (Bordo)", "#F5F5F5 (Beyaz)", "#36454F (Antrasit)"],
        "mood": "Zarif, prestijli, gösterişli",
    },
}

# Boya hesaplama sabitleri
PAINT_COVERAGE = {
    "iç cephe": {"m2_per_lt": 12, "kat": 2, "fiyat_lt": 150},
    "dış cephe": {"m2_per_lt": 10, "kat": 2, "fiyat_lt": 200},
    "tavan": {"m2_per_lt": 14, "kat": 1, "fiyat_lt": 120},
    "astar": {"m2_per_lt": 15, "kat": 1, "fiyat_lt": 80},
    "vernik": {"m2_per_lt": 12, "kat": 2, "fiyat_lt": 250},
}


def architect_tools_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "status")

    if player:
        player.write_log(f"[ArchitectTools] Komut: {action}")

    if action in ("area", "alan"):
        width = float(params.get("width", 0))
        length = float(params.get("length", 0))
        height = float(params.get("height", 0))

        if width <= 0 or length <= 0:
            return "❌ En ve boy değerleri gerekli (width, length)."

        area = width * length
        lines = ["📐 Alan Hesaplama:"]
        lines.append(f"  📏 Boyutlar: {width}m × {length}m")
        lines.append(f"  📊 Alan: {area:.2f} m²")

        if height > 0:
            volume = area * height
            wall_area = 2 * (width + length) * height
            lines.append(f"  📦 Hacim: {volume:.2f} m³ (yükseklik: {height}m)")
            lines.append(f"  🧱 Duvar alanı: {wall_area:.2f} m² (kapı/pencere hariç)")

        # Yararlı bilgiler
        lines.append("\n  💡 Referanslar:")
        lines.append("     Standart oda: 12-20 m²")
        lines.append("     Salon: 25-40 m²")
        lines.append("     Mutfak: 8-15 m²")
        lines.append("     Banyo: 4-8 m²")

        return "\n".join(lines)

    elif action in ("material_compare", "malzeme"):
        mat1 = params.get("material1", "").lower()
        mat2 = params.get("material2", "").lower()

        # Tek malzeme sorgusu
        if mat1 and not mat2:
            data = MATERIALS.get(mat1)
            if not data:
                return f"❌ '{mat1}' bulunamadı. Mevcut: {', '.join(MATERIALS.keys())}"
            lines = [f"🧱 {mat1.title()} Özellikleri:"]
            for key, val in data.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {val}")
            return "\n".join(lines)

        # Karşılaştırma
        d1 = MATERIALS.get(mat1)
        d2 = MATERIALS.get(mat2)

        if not d1:
            return f"❌ '{mat1}' bulunamadı. Mevcut: {', '.join(MATERIALS.keys())}"
        if not d2:
            return f"❌ '{mat2}' bulunamadı. Mevcut: {', '.join(MATERIALS.keys())}"

        lines = [f"⚖️ Malzeme Karşılaştırma: {mat1.title()} vs {mat2.title()}"]
        all_keys = set(list(d1.keys()) + list(d2.keys()))
        for key in sorted(all_keys):
            v1 = d1.get(key, "-")
            v2 = d2.get(key, "-")
            lines.append(f"  {key.replace('_', ' ').title():20s} {str(v1):25s} {str(v2):25s}")

        return "\n".join(lines)

    elif action in ("paint", "boya"):
        area = float(params.get("area", 0))
        paint_type = params.get("type", "iç cephe").lower()

        if area <= 0:
            return "❌ Alan (m²) değeri gerekli."

        spec = PAINT_COVERAGE.get(paint_type, PAINT_COVERAGE["iç cephe"])
        total_lt = (area / spec["m2_per_lt"]) * spec["kat"]
        teneke_count = math.ceil(total_lt / 2.5)  # 2.5 lt'lik teneke
        cost = total_lt * spec["fiyat_lt"]

        lines = [
            f"🎨 Boya Hesaplama ({paint_type.title()}):",
            f"  📐 Alan: {area:.1f} m²",
            f"  🪣 Gereken boya: {total_lt:.1f} litre ({spec['kat']} kat)",
            f"  📦 Teneke (2.5L): {teneke_count} adet",
            f"  💰 Tahmini maliyet: {cost:,.0f} ₺",
            "\n  💡 Not: Kapı, pencere ve dolap alanlarını çıkarmayı unutmayın.",
            "  💡 Astar uygulaması önerilir (+%20 maliyet).",
        ]
        return "\n".join(lines)

    elif action in ("stairs", "merdiven"):
        height = float(params.get("height", 0))

        if height <= 0:
            return "❌ Kat yüksekliği (metre) gerekli."

        height_cm = height * 100 if height < 10 else height  # m veya cm kabul et

        # Standart: rıht 17-18cm, basamak genişliği 28-30cm
        riht = 17.5  # cm
        step_count = math.ceil(height_cm / riht)
        actual_riht = height_cm / step_count
        step_width = 63 - 2 * actual_riht  # Blondel formülü: 2R + G = 63cm

        # Merdiven uzunluğu
        total_length = step_count * step_width
        angle = math.degrees(math.atan(height_cm / total_length))

        lines = [
            "🪜 Merdiven Hesaplama:",
            f"  📏 Kat yüksekliği: {height_cm:.0f} cm",
            f"  🔢 Basamak sayısı: {step_count}",
            f"  📐 Rıht yüksekliği: {actual_riht:.1f} cm",
            f"  📐 Basamak genişliği: {step_width:.1f} cm",
            f"  📏 Toplam uzunluk: {total_length:.0f} cm ({total_length/100:.1f} m)",
            f"  📐 Eğim açısı: {angle:.1f}°",
            f"\n  ✅ Blondel Formülü: 2×{actual_riht:.1f} + {step_width:.1f} = {2*actual_riht + step_width:.1f} cm (ideal: 62-64)",
            "  📋 Yönetmelik: Rıht 15-18cm, genişlik min 28cm (konut)",
        ]
        return "\n".join(lines)

    elif action in ("color_palette", "renk", "palette"):
        style = params.get("style", "modern").lower()

        # Tüm paletleri göster
        if style in ("all", "tümü", "hepsi", "list"):
            lines = ["🎨 Mevcut Renk Paletleri:"]
            for name, data in COLOR_PALETTES.items():
                lines.append(f"  🎯 {name.title()} — {data['mood']}")
            return "\n".join(lines)

        palette = COLOR_PALETTES.get(style)
        if not palette:
            # Kısmi eşleşme
            for key, data in COLOR_PALETTES.items():
                if style in key:
                    palette = data
                    style = key
                    break

        if not palette:
            available = ", ".join(COLOR_PALETTES.keys())
            return f"❌ '{style}' paleti bulunamadı. Mevcut: {available}"

        lines = [f"🎨 {style.title()} Renk Paleti:"]
        lines.append(f"  🌟 Mood: {palette['mood']}")
        lines.append("  🎯 Renkler:")
        for color in palette["colors"]:
            lines.append(f"     ● {color}")

        return "\n".join(lines)

    elif action in ("light", "aydınlatma", "lux"):
        area = float(params.get("area", 0))
        room_type = params.get("room_type", "ofis").lower()

        lux_standards = {
            "ofis": 500, "yatak odası": 150, "salon": 300, "mutfak": 500,
            "banyo": 300, "koridor": 100, "garaj": 300, "depo": 200,
            "okuma": 500, "atölye": 750, "mağaza": 500, "restoran": 200,
        }

        lux = lux_standards.get(room_type, 300)
        if area <= 0:
            return f"💡 {room_type.title()} için önerilen aydınlatma: {lux} lux\nAlan belirtin (m²) detaylı hesaplama için."

        total_lumen = lux * area
        # Ortalama LED ampul: ~100 lm/W, 10W ampul = 1000 lumen
        bulb_count_10w = math.ceil(total_lumen / 1000)

        lines = [
            f"💡 Aydınlatma Hesaplama ({room_type.title()}):",
            f"  📐 Alan: {area:.1f} m²",
            f"  🔆 Gerekli: {lux} lux × {area:.0f} m² = {total_lumen:,.0f} lümen",
            f"  💡 ~{bulb_count_10w} adet 10W LED ampul (1000lm)",
            f"  💡 ~{math.ceil(total_lumen/1600)} adet 15W LED ampul (1600lm)",
        ]
        return "\n".join(lines)

    elif action == "status":
        return (
            "🏗️ Mimar Araçları:\n"
            "  • area / alan — Alan ve hacim hesaplama\n"
            "  • material_compare — Malzeme karşılaştırma\n"
            "  • paint / boya — Boya miktarı hesaplama\n"
            "  • stairs / merdiven — Merdiven hesaplama\n"
            "  • color_palette / renk — Renk paleti önerisi\n"
            "  • light / aydınlatma — Aydınlatma hesaplama"
        )

    return "Geçersiz komut. Kullanılabilir: area, material_compare, paint, stairs, color_palette, light, status"
