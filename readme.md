<div align="center">

**🇹🇷 Türkçe** · [🇬🇧 English](README.en.md)

# 🤖 JARVIS

### Sesli, Araç-Kullanan, Hafızalı Kişisel AI Asistan

Gemini Live (native audio) üzerine kurulu masaüstü yapay zekâ asistanı.
Konuşur, dinler, **49+ araçla** bilgisayarını kontrol eder, geçmişini hatırlar
ve gerektiğinde **kendi yeni yeteneğini yazar.**

`Python 3.12+` · `Gemini 2.5 Flash` · `PyQt6` · `SQLite` · `FastAPI`

</div>

---

## ✨ Neler Yapabilir?

| | |
|---|---|
| 🎙️ **Gerçek zamanlı sesli diyalog** | Native audio, akıcı konuşma — **sözünü kesebilirsin** (barge-in) |
| 🛠️ **49+ araç** | Spotify, YouTube, sistem kontrolü, dosya, takvim, hava, çeviri, siber güvenlik, muhasebe, mimari hesaplar... |
| 🧠 **Çok katmanlı hafıza** | Şifreli kalıcı tercihler + semantik (vektör) geri çağırma + episodik geçmiş + konuşma transkriptleri |
| 🤖 **Kendini geliştirme** | `architect` ile yeni araç yazar; `plan_and_execute` ile çok adımlı görevleri planlayıp yürütür |
| 💻 **Jenerik kod yürütme** | Hazır araç yetmezse Python/PowerShell yazıp çalıştırır — "yapamam" demez |
| 🌐 **Tarayıcı kontrolü** | Playwright ile sayfa gez, form doldur, veri çek |
| 🔒 **Güvenlik** | Yıkıcı işlemlerde onay, şifreli hafıza, kod sandbox |
| 📊 **Web panosu** | `localhost:8765` — canlı istatistik, telemetri, log, transkript |

---

## 🚀 Kurulum

```bash
# 1. Bağımlılıklar
pip install -r requirements.txt

# 2. Tarayıcı motoru (browser_agent için)
playwright install chromium
```

### API Anahtarı

İki yoldan biri yeterli:

```jsonc
// config/api_keys.json
{ "gemini_api_key": "AIza..." }
```

```bash
# veya .env (.env.example'ı kopyala)
JARVIS_GEMINI_API_KEY=AIza...
```

> [Gemini API anahtarını ücretsiz al →](https://aistudio.google.com/apikey)

### Çalıştır

```bash
python main.py        # veya JARVIS.bat (Windows)
```

İlk açılışta `~/.jarvis/` dizini oluşur (hafıza, log, şifreleme anahtarı).

### 📦 Bağımsız .exe (Python kurulu olmadan)

```bash
build_exe.bat          # veya: pyinstaller jarvis.spec --noconfirm --clean
```

Çıktı: `dist/JARVIS/JARVIS.exe`. Tüm `dist/JARVIS/` klasörünü taşıyabilirsin —
`_internal/` ve `config/` exe ile birlikte olmalı. API anahtarını
`dist/JARVIS/config/api_keys.json` içine koy.

---

## 🎯 Örnek Komutlar

| Dersin... | JARVIS... |
|-----------|-----------|
| *"Masaüstündeki PDF'leri say"* | `code_runner` ile Python yazar, çalıştırır |
| *"Hacker News'in ilk 5 başlığını oku"* | `web_fetch` ile sayfayı çeker |
| *"Bana bir özet hazırla, rapor.docx olarak kaydet"* | `file_write` ile Word dosyası üretir |
| *"Bu PDF'i özetle"* | `analyze_file` ile multimodal analiz yapar |
| *"Şunu unutma: bana patron diye seslen"* | `update_memory` ile kalıcı kaydeder |
| *"Geçen sefer ne konuşmuştuk?"* | `vector_memory` ile semantik geri çağırır |
| *"Hava durumuna bak, takvime ekle, mail at"* | `plan_and_execute` ile çok adımlı plan |
| *"Dosya sayan bir araç yaz"* | `architect` ile kalıcı yeni yetenek doğurur |

---

## ⚙️ Yapılandırma

Tüm ayarlar [`core/config.py`](core/config.py)'de; `.env` veya `JARVIS_*` ortam
değişkenleriyle override edilir. Bkz. [`.env.example`](.env.example).

| Ayar | Varsayılan | Açıklama |
|------|-----------|----------|
| `JARVIS_SAFE_MODE` | `true` | Yıkıcı araçlarda onay iste |
| `JARVIS_VOICE_NAME` | `Charon` | TTS sesi |
| `JARVIS_INTERRUPT_RMS` | `0.18` | Barge-in eşiği (yükselt = daha zor kesilir) |
| `JARVIS_DASHBOARD_PORT` | `8765` | Web panosu portu |
| `JARVIS_CTX_TOTAL_CAP` | `6000` | Prompt context bütçesi (karakter) |
| `SENTRY_DSN` | — | Hata izleme (opsiyonel) |

---

## 🏗️ Mimari

```
Mikrofon → Gemini Live → ┬─ AUDIO → hoparlör (barge-in destekli)
                          └─ tool_call → action_registry → araç → sonuç
```

Tek `qasync` event loop'unda çalışır (Qt UI + asyncio aynı thread).

| Katman | İçerik |
|--------|--------|
| **main.py** | `JarvisLive` orchestrator — audio I/O, tool yürütme, context, reconnect |
| **actions/** | Her dosya bir araç (`<isim>_action`), lazy import + AST keşif |
| **memory/** | vault (şifreleme), vector_memory (RAG), episodic (SQLite), transcripts |
| **core/** | config, logging, kişilik/duygu motorları, prompt |
| **dashboard/** | FastAPI web panosu |

Detaylar → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🧪 Geliştirme

```bash
pip install -e ".[dev]"

pytest                                      # 37 test
ruff check . --fix                          # lint + format
py-spy record -o profile.svg --pid <pid>    # canlı profil
```

---

## 🔐 Veri & Gizlilik

- **Her şey yerel** — veriler `~/.jarvis/` altında, bulut yok.
- **Şifreli hafıza** — kalıcı tercihler Fernet (AES-128) ile şifreli.
- ⚠️ **Anahtarını yedekle** — `~/.jarvis/.key` kaybolursa şifreli hafıza geri açılamaz.
- **Kod sandbox** — `code_runner` kök silme, disk format, fork-bomb gibi yıkıcı kalıpları reddeder.

---

## 📜 Köken & Lisans

[FatihMakes / MARK XXXIX](https://www.youtube.com/@FatihMakes) tabanı üzerine
inşa edilmiş; mimari, performans, güvenlik ve gözlemlenebilirlik katmanları
eklenmiş özelleştirilmiş bir sürüm. Değişiklikler → [CHANGELOG.md](CHANGELOG.md)

Kişisel ve ticari olmayan kullanım — [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

---

<div align="center">
<sub>⚡ Yerel çalışır · Abonelik yok · Tam kontrol sende</sub>
</div>
