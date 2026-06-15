"""
Unit Converter Action — Kapsamlı birim dönüştürücü.
Kullanım: "150 pound kaç kilo?", "1 cup kaç ml?", "350°F kaç derece?"
"""

CONVERSIONS = {
    # Uzunluk (metre bazlı)
    "length": {
        "m": 1, "metre": 1, "meter": 1,
        "cm": 0.01, "santimetre": 0.01,
        "mm": 0.001, "milimetre": 0.001,
        "km": 1000, "kilometre": 1000,
        "inch": 0.0254, "inç": 0.0254, "in": 0.0254,
        "feet": 0.3048, "ft": 0.3048, "foot": 0.3048, "ayak": 0.3048,
        "yard": 0.9144, "yd": 0.9144,
        "mile": 1609.344, "mil": 1609.344, "mi": 1609.344,
        "nautical_mile": 1852, "deniz_mili": 1852,
    },
    # Ağırlık (gram bazlı)
    "weight": {
        "g": 1, "gram": 1, "gr": 1,
        "kg": 1000, "kilogram": 1000, "kilo": 1000,
        "mg": 0.001, "miligram": 0.001,
        "ton": 1_000_000,
        "lb": 453.592, "pound": 453.592, "lbs": 453.592,
        "oz": 28.3495, "ounce": 28.3495, "ons": 28.3495,
        "stone": 6350.29,
    },
    # Hacim (mililitre bazlı)
    "volume": {
        "ml": 1, "mililitre": 1,
        "l": 1000, "lt": 1000, "litre": 1000,
        "cl": 10,
        "dl": 100, "desilitre": 100,
        "cup": 236.588, "bardak": 236.588,
        "tbsp": 14.787, "yemek_kasigi": 14.787, "yemek kaşığı": 14.787,
        "tsp": 4.929, "cay_kasigi": 4.929, "çay kaşığı": 4.929,
        "fl_oz": 29.5735,
        "gallon": 3785.41, "galon": 3785.41,
        "pint": 473.176,
        "quart": 946.353,
    },
    # Alan (m² bazlı)
    "area": {
        "m2": 1, "m²": 1, "metrekare": 1,
        "cm2": 0.0001, "cm²": 0.0001,
        "km2": 1_000_000, "km²": 1_000_000,
        "ft2": 0.092903, "ft²": 0.092903,
        "acre": 4046.86, "dönüm": 1000,
        "hektar": 10000, "ha": 10000,
    },
    # Hız (m/s bazlı)
    "speed": {
        "m/s": 1, "mps": 1,
        "km/h": 0.277778, "kmh": 0.277778, "kms": 0.277778,
        "mph": 0.44704, "mil/saat": 0.44704,
        "knot": 0.514444, "knots": 0.514444,
    },
    # Veri (byte bazlı)
    "data": {
        "b": 1, "byte": 1,
        "kb": 1024,
        "mb": 1_048_576,
        "gb": 1_073_741_824,
        "tb": 1_099_511_627_776,
        "pb": 1_125_899_906_842_624,
    },
    # Zaman (saniye bazlı)
    "time": {
        "sn": 1, "saniye": 1, "s": 1, "sec": 1, "second": 1,
        "dk": 60, "dakika": 60, "min": 60, "minute": 60,
        "saat": 3600, "h": 3600, "hour": 3600,
        "gün": 86400, "gun": 86400, "day": 86400,
        "hafta": 604800, "week": 604800,
        "ay": 2_592_000, "month": 2_592_000,
        "yıl": 31_536_000, "year": 31_536_000,
    },
}

# Mutfak özel dönüşümler tablosu
COOKING_QUICK = {
    ("cup", "ml"): 237, ("cup", "tbsp"): 16, ("cup", "tsp"): 48,
    ("tbsp", "ml"): 15, ("tbsp", "tsp"): 3,
    ("tsp", "ml"): 5,
}

CATEGORY_ICONS = {
    "length": "📏", "weight": "⚖️", "volume": "🧪", "area": "📐",
    "speed": "🏎️", "data": "💾", "time": "⏱️", "temperature": "🌡️",
    "cooking": "🥄",
}


def _find_unit(unit_str: str) -> tuple[str, str] | None:
    """Birim string'inden kategori ve normalize edilmiş birim bul."""
    unit_str = unit_str.lower().strip().replace("²", "2")
    for category, units in CONVERSIONS.items():
        if unit_str in units:
            return category, unit_str
    return None


def _convert_temperature(value: float, from_u: str, to_u: str) -> float | None:
    """Sıcaklık dönüşümü (özel formül)."""
    from_u = from_u.lower().strip()
    to_u = to_u.lower().strip()

    # Normalize
    temp_map = {"c": "c", "celsius": "c", "°c": "c", "derece": "c", "santigrat": "c",
                "f": "f", "fahrenheit": "f", "°f": "f",
                "k": "k", "kelvin": "k"}

    f = temp_map.get(from_u)
    t = temp_map.get(to_u)
    if not f or not t:
        return None

    # Önce Celsius'a çevir
    if f == "c":
        celsius = value
    elif f == "f":
        celsius = (value - 32) * 5 / 9
    elif f == "k":
        celsius = value - 273.15
    else:
        return None

    # Celsius'tan hedefe
    if t == "c":
        return celsius
    elif t == "f":
        return celsius * 9 / 5 + 32
    elif t == "k":
        return celsius + 273.15
    return None


def _format_number(val: float) -> str:
    """Sayıyı güzel formatla."""
    if val == int(val):
        return f"{int(val):,}".replace(",", ".")
    elif abs(val) < 0.01:
        return f"{val:.6f}"
    elif abs(val) < 1:
        return f"{val:.4f}"
    else:
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def unit_converter_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "convert")

    if player:
        player.write_log(f"[UnitConverter] Komut: {action}")

    value_str = str(params.get("value", "0"))
    from_unit = params.get("from_unit", "") or params.get("from", "")
    to_unit = params.get("to_unit", "") or params.get("to", "")

    try:
        value = float(value_str.replace(",", "."))
    except (ValueError, TypeError):
        return f"❌ Geçersiz sayı: {value_str}"

    if action == "convert" or action in ("length", "weight", "volume", "area", "speed", "data", "time_convert", "cooking"):
        # Sıcaklık kontrolü
        temp_keywords = {"c", "f", "k", "celsius", "fahrenheit", "kelvin", "°c", "°f", "derece", "santigrat"}
        if from_unit.lower().strip() in temp_keywords or to_unit.lower().strip() in temp_keywords:
            result = _convert_temperature(value, from_unit, to_unit)
            if result is not None:
                return f"🌡️ {_format_number(value)} {from_unit} = {_format_number(result)} {to_unit}"
            return f"❌ Sıcaklık dönüşümü yapılamadı: {from_unit} → {to_unit}"

        # Normal birim dönüşümü
        from_info = _find_unit(from_unit)
        to_info = _find_unit(to_unit)

        if not from_info:
            return f"❌ Bilinmeyen birim: '{from_unit}'. Desteklenen birimler: m, cm, km, kg, lb, ml, cup, tbsp, °C, °F vb."
        if not to_info:
            return f"❌ Bilinmeyen birim: '{to_unit}'"

        from_cat, from_key = from_info
        to_cat, to_key = to_info

        if from_cat != to_cat:
            return f"❌ Farklı kategoriler dönüştürülemez: {from_cat} ↔ {to_cat}"

        # Dönüşüm: kaynak → baz birim → hedef
        base_value = value * CONVERSIONS[from_cat][from_key]
        result = base_value / CONVERSIONS[to_cat][to_key]

        icon = CATEGORY_ICONS.get(from_cat, "🔄")
        return f"{icon} {_format_number(value)} {from_unit} = {_format_number(result)} {to_unit}"

    elif action == "temperature":
        result = _convert_temperature(value, from_unit, to_unit)
        if result is not None:
            return f"🌡️ {_format_number(value)} {from_unit} = {_format_number(result)} {to_unit}"
        return "❌ Sıcaklık dönüşümü yapılamadı. Desteklenen: C, F, K"

    elif action == "cooking":
        # Mutfak özel dönüşümleri
        lines = ["🥄 Mutfak Ölçü Tablosu:"]
        lines.append("  1 cup    = 237 ml = 16 tbsp = 48 tsp")
        lines.append("  1 tbsp   = 15 ml = 3 tsp")
        lines.append("  1 tsp    = 5 ml")
        lines.append("  1 fl oz  = 30 ml")
        lines.append("  1 gallon = 3.785 lt")
        lines.append("  1 pint   = 473 ml")
        lines.append("  1 stick butter = 113g = 8 tbsp")
        return "\n".join(lines)

    return "Geçersiz komut. Kullanılabilir: convert, temperature, cooking"
