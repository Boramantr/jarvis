"""
Accountant Tools Action — Muhasebe ve finans araçları.
KDV hesaplama, vergi takvimi, SGK prim, beyanname hatırlatma, gecikme faizi.
Kullanım: "KDV hesapla", "Bu ay beyanname var mı?", "Brüt net hesapla"
"""
from datetime import datetime

# 2024-2025 vergi dilimleri (güncelleme gerekebilir)
INCOME_TAX_BRACKETS = [
    (110_000, 0.15),
    (230_000, 0.20),
    (580_000, 0.27),
    (3_000_000, 0.35),
    (float("inf"), 0.40),
]

# SGK sabitleri (2025 tahmini)
SGK_CONSTANTS = {
    "asgari_ucret_brut": 22_104,  # 2025 brüt asgari ücret (güncellenebilir)
    "sgk_iscsi_orani": 0.14,     # İşçi SGK primi
    "issizlik_isci": 0.01,       # İşsizlik sigortası işçi payı
    "sgk_isveren": 0.205,        # İşveren SGK primi (toplam)
    "issizlik_isveren": 0.02,    # İşsizlik sigortası işveren payı
    "damga_vergisi": 0.00759,    # Damga vergisi oranı
}

# KDV oranları
KDV_RATES = {
    "genel": 20,
    "temel_gida": 1,
    "gıda": 10,
    "kitap": 0,
    "gazete": 0,
    "eğitim": 10,
    "sağlık": 10,
    "konut": 10,   # 150m² altı
    "turizm": 10,
    "tekstil": 10,
    "tarım": 1,
}

# Vergi beyanname takvimi
TAX_CALENDAR = {
    1: [
        ("1-26 Ocak", "Aralık KDV Beyannamesi"),
        ("1-26 Ocak", "4. Dönem Geçici Vergi Beyannamesi"),
        ("1-26 Ocak", "Aralık Muhtasar ve Prim Hizmet Beyannamesi"),
    ],
    2: [
        ("1-26 Şubat", "Ocak KDV Beyannamesi"),
        ("1-26 Şubat", "Ocak Muhtasar ve Prim Hizmet Beyannamesi"),
        ("1-28 Şubat", "Yıllık Gelir Vergisi (Basit Usul)"),
    ],
    3: [
        ("1-26 Mart", "Şubat KDV Beyannamesi"),
        ("1-31 Mart", "Yıllık Gelir Vergisi Beyannamesi"),
        ("1-31 Mart", "Ba-Bs Bildirim Formu (yıllık)"),
    ],
    4: [
        ("1-26 Nisan", "Mart KDV Beyannamesi"),
        ("1-30 Nisan", "Yıllık Kurumlar Vergisi Beyannamesi"),
        ("1-17 Nisan", "1. Dönem Geçici Vergi Beyannamesi"),
    ],
    5: [
        ("1-26 Mayıs", "Nisan KDV Beyannamesi"),
        ("1-26 Mayıs", "Nisan Muhtasar ve Prim Hizmet Beyannamesi"),
    ],
    6: [
        ("1-26 Haziran", "Mayıs KDV Beyannamesi"),
    ],
    7: [
        ("1-26 Temmuz", "Haziran KDV Beyannamesi"),
        ("1-17 Temmuz", "2. Dönem Geçici Vergi Beyannamesi"),
    ],
    8: [
        ("1-26 Ağustos", "Temmuz KDV Beyannamesi"),
    ],
    9: [
        ("1-26 Eylül", "Ağustos KDV Beyannamesi"),
    ],
    10: [
        ("1-26 Ekim", "Eylül KDV Beyannamesi"),
        ("1-17 Ekim", "3. Dönem Geçici Vergi Beyannamesi"),
    ],
    11: [
        ("1-26 Kasım", "Ekim KDV Beyannamesi"),
    ],
    12: [
        ("1-26 Aralık", "Kasım KDV Beyannamesi"),
    ],
}


def _calc_kdv(amount: float, rate: float, mode: str) -> dict:
    """KDV hesaplama."""
    rate_decimal = rate / 100
    if mode == "dahil":
        kdv = amount - (amount / (1 + rate_decimal))
        net = amount - kdv
        return {"brüt": amount, "kdv": kdv, "net": net, "oran": rate}
    else:  # hariç
        kdv = amount * rate_decimal
        brut = amount + kdv
        return {"brüt": brut, "kdv": kdv, "net": amount, "oran": rate}


def _calc_net_salary(brut: float) -> dict:
    """Brüt maaştan net maaş hesapla."""
    sgk = SGK_CONSTANTS

    sgk_primi = brut * sgk["sgk_iscsi_orani"]
    issizlik = brut * sgk["issizlik_isci"]
    toplam_kesinti_sgk = sgk_primi + issizlik

    gelir_vergisi_matrahi = brut - toplam_kesinti_sgk

    # Gelir vergisi (kümülatif — basitleştirilmiş aylık)
    yillik_matrah = gelir_vergisi_matrahi * 12
    yillik_vergi = 0
    kalan = yillik_matrah
    for limit, oran in INCOME_TAX_BRACKETS:
        if kalan <= 0:
            break
        taxable = min(kalan, limit)
        yillik_vergi += taxable * oran
        kalan -= taxable

    aylik_gelir_vergisi = yillik_vergi / 12

    damga = brut * sgk["damga_vergisi"]

    net = brut - toplam_kesinti_sgk - aylik_gelir_vergisi - damga

    # İşveren maliyeti
    isveren_sgk = brut * sgk["sgk_isveren"]
    isveren_issizlik = brut * sgk["issizlik_isveren"]
    isveren_toplam = brut + isveren_sgk + isveren_issizlik

    return {
        "brüt": brut,
        "sgk_primi": sgk_primi,
        "issizlik": issizlik,
        "gelir_vergisi": aylik_gelir_vergisi,
        "damga_vergisi": damga,
        "net": net,
        "isveren_maliyeti": isveren_toplam,
    }


def _calc_severance(years: float, last_salary: float) -> dict:
    """Kıdem tazminatı hesaplama."""
    # Kıdem tazminatı tavanı (2025 tahmini)
    tavan = 35_000  # Güncellenebilir

    base = min(last_salary, tavan)
    total = base * years

    return {
        "yıl": years,
        "son_maaş": last_salary,
        "tavan": tavan,
        "baz": base,
        "toplam": total,
    }


def _calc_late_interest(amount: float, days: int, rate_type: str = "yasal") -> dict:
    """Gecikme faizi hesaplama."""
    # Yıllık faiz oranları
    rates = {
        "yasal": 0.24,    # Yasal faiz (güncel)
        "ticari": 0.36,   # Ticari temerrüt faizi
        "vergi": 0.048,   # Vergi gecikme zammı (aylık %4.8 → yıllık ~57.6%)
    }

    annual_rate = rates.get(rate_type, rates["yasal"])
    daily_rate = annual_rate / 365
    interest = amount * daily_rate * days
    total = amount + interest

    return {
        "anapara": amount,
        "gün": days,
        "oran_yıllık": annual_rate * 100,
        "faiz": interest,
        "toplam": total,
    }


def _format_money(val: float) -> str:
    """Para formatla: 1.234,56 ₺"""
    return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"


def accountant_tools_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "status")

    if player:
        player.write_log(f"[AccountantTools] Komut: {action}")

    if action == "kdv" or action == "kdv_hesapla":
        amount = float(params.get("amount", 0))
        rate = float(params.get("rate", 20))
        mode = params.get("mode", "hariç").lower()  # dahil / hariç

        if amount <= 0:
            return "❌ Tutar belirtilmedi."

        result = _calc_kdv(amount, rate, mode)

        lines = [
            f"🧮 KDV Hesaplama (%{result['oran']:.0f} — KDV {mode}):",
            f"  💰 Net tutar: {_format_money(result['net'])}",
            f"  📋 KDV tutarı: {_format_money(result['kdv'])}",
            f"  💵 Brüt tutar: {_format_money(result['brüt'])}",
        ]

        # KDV oranları referans
        lines.append("\n  📌 KDV Oranları: Genel %20 | Gıda %10 | Temel gıda %1 | Kitap %0")

        return "\n".join(lines)

    elif action == "vergi_takvimi" or action == "tax_calendar":
        month = int(params.get("month", datetime.now().month))
        month_name = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                      "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][month - 1]

        events = TAX_CALENDAR.get(month, [])
        if not events:
            return f"📅 {month_name} ayında beyanname yok."

        lines = [f"📅 Vergi Takvimi — {month_name}:"]
        for date_range, desc in events:
            lines.append(f"  📋 {date_range}: {desc}")

        # Sonraki ayı da göster
        next_month = month + 1 if month < 12 else 1
        next_events = TAX_CALENDAR.get(next_month, [])
        if next_events:
            next_name = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
                        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][next_month - 1]
            lines.append(f"\n  📆 Gelecek ay ({next_name}):")
            for date_range, desc in next_events[:3]:
                lines.append(f"    📋 {date_range}: {desc}")

        return "\n".join(lines)

    elif action == "sgk_prim" or action == "sgk":
        brut = float(params.get("brut", SGK_CONSTANTS["asgari_ucret_brut"]))

        sgk = SGK_CONSTANTS
        isci_sgk = brut * sgk["sgk_iscsi_orani"]
        isci_issizlik = brut * sgk["issizlik_isci"]
        isveren_sgk = brut * sgk["sgk_isveren"]
        isveren_issizlik = brut * sgk["issizlik_isveren"]

        lines = [
            f"🏥 SGK Prim Hesaplama (Brüt: {_format_money(brut)}):",
            "\n  👷 İşçi Payı:",
            f"    SGK Primi (%14): {_format_money(isci_sgk)}",
            f"    İşsizlik (%1): {_format_money(isci_issizlik)}",
            f"    Toplam: {_format_money(isci_sgk + isci_issizlik)}",
            "\n  🏢 İşveren Payı:",
            f"    SGK Primi (%20.5): {_format_money(isveren_sgk)}",
            f"    İşsizlik (%2): {_format_money(isveren_issizlik)}",
            f"    Toplam: {_format_money(isveren_sgk + isveren_issizlik)}",
            f"\n  💰 Toplam SGK Maliyeti: {_format_money(isci_sgk + isci_issizlik + isveren_sgk + isveren_issizlik)}",
        ]
        return "\n".join(lines)

    elif action == "bordro" or action == "maas" or action == "net_maas":
        brut = float(params.get("brut", 0))
        if brut <= 0:
            return "❌ Brüt maaş belirtilmedi."

        result = _calc_net_salary(brut)

        lines = [
            f"💰 Maaş Bordrosu (Brüt: {_format_money(result['brüt'])}):",
            "\n  Kesintiler:",
            f"    SGK Primi (%14): -{_format_money(result['sgk_primi'])}",
            f"    İşsizlik (%1): -{_format_money(result['issizlik'])}",
            f"    Gelir Vergisi: -{_format_money(result['gelir_vergisi'])}",
            f"    Damga Vergisi: -{_format_money(result['damga_vergisi'])}",
            "    ────────────────────",
            f"  ✅ Net Maaş: {_format_money(result['net'])}",
            f"\n  🏢 İşveren Toplam Maliyeti: {_format_money(result['isveren_maliyeti'])}",
        ]
        return "\n".join(lines)

    elif action == "beyanname_hatirla" or action == "beyanname":
        now = datetime.now()
        month = now.month
        day = now.day

        events = TAX_CALENDAR.get(month, [])
        upcoming = []
        for date_range, desc in events:
            # Son günü parse et
            import re
            match = re.search(r"(\d+)\s+\w+$", date_range)
            if match:
                deadline_day = int(match.group(1))
                if deadline_day >= day:
                    remaining = deadline_day - day
                    upcoming.append((remaining, deadline_day, desc))

        if not upcoming:
            return f"✅ Bu ay kalan beyanname yok. ({now.strftime('%d.%m.%Y')})"

        upcoming.sort()
        lines = [f"⏰ Yaklaşan Beyannameler ({now.strftime('%d.%m.%Y')}):"]
        for remaining, deadline, desc in upcoming:
            icon = "🔴" if remaining <= 3 else "🟡" if remaining <= 7 else "🟢"
            lines.append(f"  {icon} {desc}")
            lines.append(f"     Son gün: {deadline}.{month:02d} ({remaining} gün kaldı)")

        return "\n".join(lines)

    elif action == "gecikme_faizi" or action == "faiz":
        amount = float(params.get("amount", 0))
        days = int(params.get("days", 0))
        rate_type = params.get("rate_type", "yasal").lower()

        if amount <= 0 or days <= 0:
            return "❌ Tutar ve gün sayısı gerekli."

        result = _calc_late_interest(amount, days, rate_type)

        lines = [
            f"📊 Gecikme Faizi Hesaplama ({rate_type.title()}):",
            f"  💰 Anapara: {_format_money(result['anapara'])}",
            f"  📅 Gecikme: {result['gün']} gün",
            f"  📈 Yıllık oran: %{result['oran_yıllık']:.1f}",
            f"  💸 Faiz tutarı: {_format_money(result['faiz'])}",
            f"  💵 Toplam: {_format_money(result['toplam'])}",
        ]
        return "\n".join(lines)

    elif action == "kidem" or action == "kidem_tazminati":
        years = float(params.get("years", 0))
        salary = float(params.get("salary", 0))

        if years <= 0 or salary <= 0:
            return "❌ Çalışma yılı ve son brüt maaş gerekli."

        result = _calc_severance(years, salary)
        lines = [
            "⚖️ Kıdem Tazminatı Hesaplama:",
            f"  📅 Çalışma süresi: {result['yıl']:.1f} yıl",
            f"  💰 Son brüt maaş: {_format_money(result['son_maaş'])}",
            f"  📊 Tavan: {_format_money(result['tavan'])}",
            f"  💵 Tazminat: {_format_money(result['toplam'])}",
            "\n  ℹ️ Kıdem tazminatı tavanı her 6 ayda güncellenir.",
        ]
        return "\n".join(lines)

    elif action == "status":
        return (
            "🧮 Muhasebeci Araçları:\n"
            "  • kdv — KDV hesaplama (dahil/hariç)\n"
            "  • vergi_takvimi — Aylık beyanname takvimi\n"
            "  • sgk_prim — SGK prim hesaplama\n"
            "  • bordro — Brüt→net maaş hesaplama\n"
            "  • beyanname_hatirla — Yaklaşan beyannameler\n"
            "  • gecikme_faizi — Gecikme faizi hesaplama\n"
            "  • kidem — Kıdem tazminatı hesaplama"
        )

    return "Geçersiz komut. Kullanılabilir: kdv, vergi_takvimi, sgk_prim, bordro, beyanname_hatirla, gecikme_faizi, kidem"
