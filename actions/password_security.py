"""
Password Security Action — Güvenli şifre üretimi ve şifre gücü analizi.
Kullanım: "Şifre üret", "Bu şifre güvenli mi?", "Passphrase üret"
"""
import math
import re
import secrets
import string

# Yaygın zayıf şifreler (top 100)
COMMON_PASSWORDS = {
    "123456", "password", "12345678", "qwerty", "123456789", "12345", "1234",
    "111111", "1234567", "dragon", "123123", "baseball", "abc123", "football",
    "monkey", "letmein", "shadow", "master", "666666", "qwertyuiop",
    "123321", "mustang", "1234567890", "michael", "654321", "superman",
    "1qaz2wsx", "7777777", "121212", "000000", "qazwsx", "123qwe",
    "killer", "trustno1", "jordan", "jennifer", "zxcvbnm", "asdfgh",
    "hunter", "buster", "soccer", "harley", "batman", "andrew", "tigger",
    "sunshine", "iloveyou", "2000", "charlie", "robert", "thomas", "hockey",
    "ranger", "daniel", "starwars", "klaster", "112233", "george", "computer",
    "michelle", "jessica", "pepper", "1111", "zxcvbn", "555555", "11111111",
    "131313", "freedom", "777777", "pass", "maggie", "159753", "aaaaaa",
    "ginger", "princess", "joshua", "cheese", "amanda", "summer", "love",
    "ashley", "nicole", "chelsea", "biteme", "matthew", "access", "yankees",
    "987654321", "dallas", "austin", "thunder", "taylor", "matrix", "mobilemail",
    "admin", "passwd", "root", "toor", "welcome", "login", "passw0rd",
}

# Passphrase kelime listesi (Türkçe + İngilizce karışık)
WORDLIST = [
    "deniz", "bulut", "yıldız", "orman", "nehir", "dağ", "güneş", "rüzgar",
    "ateş", "toprak", "çiçek", "kuş", "balık", "aslan", "kaplan", "kartal",
    "gemi", "köprü", "kale", "bahçe", "kitap", "müzik", "renk", "ışık",
    "zaman", "yolcu", "kaptan", "pilot", "robot", "uzay", "gezegen", "yörünge",
    "fırtına", "şimşek", "volkan", "okyanus", "ada", "orman", "çöl", "kutup",
    "tiger", "eagle", "storm", "river", "cloud", "flame", "ocean", "forest",
    "crystal", "shadow", "phoenix", "thunder", "dragon", "falcon", "wolf",
    "silver", "golden", "cosmic", "quantum", "binary", "cipher", "matrix",
    "beacon", "anchor", "summit", "harbor", "voyage", "orbit", "prism",
    "cobalt", "ember", "frost", "spark", "bloom", "swift", "brave", "noble",
]


def _generate_password(length: int = 16, pw_type: str = "all") -> str:
    """Kriptografik güvenli şifre üret."""
    length = max(8, min(int(length), 128))

    if pw_type == "pin":
        chars = string.digits
    elif pw_type == "alpha":
        chars = string.ascii_letters
    elif pw_type == "numeric":
        chars = string.digits + string.punctuation
    else:  # all
        chars = string.ascii_letters + string.digits + string.punctuation

    # En az her tipten bir karakter garanti et
    if pw_type == "all" and length >= 4:
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(string.punctuation),
        ]
        password += [secrets.choice(chars) for _ in range(length - 4)]
        # Karıştır
        result = list(password)
        secrets.SystemRandom().shuffle(result)
        return "".join(result)

    return "".join(secrets.choice(chars) for _ in range(length))


def _generate_passphrase(word_count: int = 4) -> str:
    """Hatırlanabilir kelime bazlı şifre üret."""
    word_count = max(3, min(int(word_count), 8))
    words = [secrets.choice(WORDLIST) for _ in range(word_count)]
    separator = secrets.choice(["-", "_", ".", "+"])
    # Rastgele bir kelimeyi büyük harf yap ve bir sayı ekle
    idx = secrets.randbelow(word_count)
    words[idx] = words[idx].capitalize()
    number = secrets.randbelow(100)
    return f"{separator.join(words)}{separator}{number}"


def _check_strength(password: str) -> dict:
    """Şifre gücünü analiz et."""
    score = 0
    reasons = []
    warnings = []

    length = len(password)

    # Uzunluk puanı
    if length >= 16:
        score += 30
        reasons.append("Uzunluk mükemmel (16+ karakter)")
    elif length >= 12:
        score += 25
        reasons.append("Uzunluk iyi (12+ karakter)")
    elif length >= 8:
        score += 15
        reasons.append("Uzunluk yeterli (8+ karakter)")
    else:
        score += 5
        warnings.append("Çok kısa! En az 8 karakter olmalı")

    # Karakter çeşitliliği
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;/~`]', password))

    variety = sum([has_upper, has_lower, has_digit, has_special])
    score += variety * 10
    if variety == 4:
        reasons.append("Tüm karakter tipleri mevcut")
    else:
        missing = []
        if not has_upper:
            missing.append("büyük harf")
        if not has_lower:
            missing.append("küçük harf")
        if not has_digit:
            missing.append("rakam")
        if not has_special:
            missing.append("özel karakter")
        warnings.append(f"Eksik: {', '.join(missing)}")

    # Tekrar kontrolü
    if re.search(r'(.)\1{2,}', password):
        score -= 10
        warnings.append("Tekrarlanan karakterler var")

    # Sıralı karakter kontrolü
    sequential = "abcdefghijklmnopqrstuvwxyz0123456789"
    for i in range(len(password) - 2):
        chunk = password[i:i+3].lower()
        if chunk in sequential or chunk in sequential[::-1]:
            score -= 5
            warnings.append("Sıralı karakterler var (abc, 123...)")
            break

    # Yaygın şifre kontrolü
    if password.lower() in COMMON_PASSWORDS:
        score = 5
        warnings = ["Bu şifre yaygın şifre listesinde!"]

    # Entropi hesabı
    charset_size = 0
    if has_lower:
        charset_size += 26
    if has_upper:
        charset_size += 26
    if has_digit:
        charset_size += 10
    if has_special:
        charset_size += 32
    entropy = length * math.log2(charset_size) if charset_size > 0 else 0

    if entropy >= 80:
        score += 10
        reasons.append(f"Yüksek entropi ({entropy:.0f} bit)")
    elif entropy >= 50:
        score += 5

    score = max(0, min(score, 100))

    # Derecelendirme
    if score >= 80:
        grade = "Çok Güçlü 🟢"
    elif score >= 60:
        grade = "Güçlü 🟡"
    elif score >= 40:
        grade = "Orta 🟠"
    elif score >= 20:
        grade = "Zayıf 🔴"
    else:
        grade = "Çok Zayıf ⛔"

    return {
        "score": score,
        "grade": grade,
        "entropy": entropy,
        "reasons": reasons,
        "warnings": warnings,
    }


def password_security_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "generate")

    if player:
        player.write_log(f"[PasswordSecurity] Komut: {action}")

    if action == "generate":
        length = int(params.get("length", 16))
        pw_type = params.get("type", "all")
        password = _generate_password(length, pw_type)
        strength = _check_strength(password)

        # Clipboard'a kopyala
        try:
            import pyperclip
            pyperclip.copy(password)
            clipboard_msg = "📋 Panoya kopyalandı!"
        except Exception:
            clipboard_msg = ""

        bar = "█" * (strength["score"] // 10) + "░" * (10 - strength["score"] // 10)
        lines = [
            f"🔐 Üretilen Şifre: {password}",
            f"   Uzunluk: {length} karakter | Tip: {pw_type}",
            f"   Güç: [{bar}] {strength['score']}/100 ({strength['grade']})",
        ]
        if clipboard_msg:
            lines.append(f"   {clipboard_msg}")
        return "\n".join(lines)

    elif action == "generate_passphrase":
        words = int(params.get("words", 4))
        passphrase = _generate_passphrase(words)
        strength = _check_strength(passphrase)

        try:
            import pyperclip
            pyperclip.copy(passphrase)
            clipboard_msg = "📋 Panoya kopyalandı!"
        except Exception:
            clipboard_msg = ""

        bar = "█" * (strength["score"] // 10) + "░" * (10 - strength["score"] // 10)
        lines = [
            f"🔑 Passphrase: {passphrase}",
            f"   Kelime sayısı: {words}",
            f"   Güç: [{bar}] {strength['score']}/100 ({strength['grade']})",
        ]
        if clipboard_msg:
            lines.append(f"   {clipboard_msg}")
        return "\n".join(lines)

    elif action == "strength":
        password = params.get("password", "")
        if not password:
            return "Analiz edilecek şifre belirtilmedi."

        result = _check_strength(password)
        bar = "█" * (result["score"] // 10) + "░" * (10 - result["score"] // 10)

        lines = [
            "🔍 Şifre Güç Analizi:",
            f"   Skor: [{bar}] {result['score']}/100 ({result['grade']})",
            f"   Entropi: {result['entropy']:.1f} bit",
        ]
        if result["reasons"]:
            lines.append("   ✅ " + " | ".join(result["reasons"]))
        if result["warnings"]:
            lines.append("   ⚠️ " + " | ".join(result["warnings"]))
        return "\n".join(lines)

    elif action == "bulk":
        count = min(int(params.get("count", 5)), 20)
        length = int(params.get("length", 16))
        lines = [f"🔐 {count} Adet Şifre (Uzunluk: {length}):"]
        for i in range(count):
            pw = _generate_password(length)
            lines.append(f"  {i+1}. {pw}")
        return "\n".join(lines)

    return "Geçersiz komut. Kullanılabilir: generate, generate_passphrase, strength, bulk"
