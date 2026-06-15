<div align="center">

**🇹🇷 Türkçe** · [🇬🇧 English](README.en.md)

<img src="assets/logo.png" alt="JARVIS" width="180" />

# JARVIS

### Konuşan, Dinleyen, Hatırlayan Kişisel Yapay Zekâ Asistanı

Bilgisayarına yerleşen, mikrofonla seninle gerçek zamanlı konuşan, programları
açıp kapatan, dosyalarını yöneten, internetten araştırma yapan ve sana özel
hatıralar tutan bir masaüstü AI asistanı.

`Windows` · `Python 3.12+` · `Gemini 2.5 Flash` · `PyQt6` · `SQLite` · `FastAPI`

</div>

---

## 🤔 Bu Nedir? (Hızlı Özet)

JARVIS, **Iron Man filmlerindeki yapay zekâ asistanından** ilham alan bir
masaüstü programıdır. Onunla **yazışmak yerine konuşursun** — mikrofona söylersin,
o sesli cevap verir. Tek farkı: gerçekten **bilgisayarını kullanabilir**.

> 🗣️ *"Spotify'da chill bir şeyler aç, masaüstündeki rapor.pdf'yi özetle ve
> ozet.docx olarak masaüstüne kaydet."*
>
> JARVIS Spotify'ı açar, PDF'yi okur, özetler, Word dosyası oluşturur, sana
> sesli olarak "tamamdır" der.

Sıfırdan kendin yazmak zorunda değilsin: hazır **49+ aracı** var. Bir şey
eksikse, **kendi yeni aracını kendisi yazıp** ekleyebilir.

---

## 🚀 En Hızlı Kurulum (Önerilen)

Python kurmak, terminal açmak yok. Tek tıkla kurulum:

1. 👉 **[Son sürümü buradan indir](https://github.com/Boramantr/jarvis/releases/latest)**
2. `JARVIS-Setup-1.0.0.exe` dosyasını indirip çalıştır
3. Kurulum sihirbazını takip et (İleri → İleri → Kur)
4. Başlat menüsünden veya masaüstü kısayolundan JARVIS'i aç
5. İlk açılışta sana **Gemini API anahtarı** soracak →
   [buradan ücretsiz al](https://aistudio.google.com/apikey) (Google hesabı yeter)

✅ **Hepsi bu.** Konuş, dinlesin.

---

## ✨ Neler Yapabilir?

| | |
|---|---|
| 🎙️ **Sesli sohbet** | Yazmadan konuşursun. Sözünü kesebilirsin — robot gibi durup beklemez |
| 🛠️ **49+ hazır araç** | Spotify, YouTube, dosya, takvim, hava durumu, çeviri, e-posta, web araması, kod yazma... |
| 🧠 **Seni hatırlar** | "Bana patron de", "ben vejetaryenim" — bir kez söyle, ömür boyu unutmaz |
| 🤖 **Kendini geliştirir** | İhtiyacın olan araç yoksa, *kendisi yazıp* sisteme ekler |
| 💻 **Bilgisayarı kontrol eder** | Program açar/kapatır, dosya oluşturur, taşır, siler (önce sorar) |
| 🌐 **İnternette araştırma** | Site açar, formu doldurur, veri çeker, sana özetler |
| 🔒 **Güvenli** | Önemli işlemlerde onay ister. Hafızası şifrelidir |
| 📊 **Anlık panel** | `localhost:8765` → ne yaptığını canlı izleyebilirsin |

---

## 🎯 Örnek Komutlar

Bunları **doğal Türkçe** söyle, JARVIS yapsın:

| Sen söylersin... | JARVIS şunu yapar... |
|------------------|----------------------|
| *"Masaüstündeki PDF'leri say"* | Python kodu yazar, çalıştırır, sayıyı söyler |
| *"Hacker News'in ilk 5 başlığını oku"* | Siteye girer, başlıkları çeker, okur |
| *"Bana bir özet hazırla, rapor.docx olarak kaydet"* | Word dosyası üretir |
| *"Bu PDF'i özetle"* | Multimodal analiz yapar |
| *"Şunu unutma: bana patron diye seslen"* | Kalıcı hafızaya kaydeder |
| *"Geçen sefer ne konuşmuştuk?"* | Eski konuşmalardan semantik arama yapar |
| *"Havaya bak, takvime ekle, mail at"* | 3 adımlı planı sırayla yürütür |
| *"Dosya sayan bir araç yaz"* | Kendi kodunu yazıp sisteme yeni yetenek ekler |
| *"Spotify'da odaklanma müziği aç"* | Spotify'ı açar, çalmaya başlar |
| *"Ekran kartım kaç derece?"* | Sistem sensörlerini okur, söyler |

---

## 👨‍💻 Geliştirici Kurulumu (Kaynak Koddan)

Kendi geliştirmek isteyenler için:

```bash
# 1. Repoyu klonla
git clone https://github.com/Boramantr/jarvis.git
cd jarvis

# 2. Bağımlılıklar
pip install -r requirements.txt

# 3. Tarayıcı motoru (browser_agent için)
playwright install chromium

# 4. API anahtarı: config/api_keys.json yarat
# { "gemini_api_key": "AIza..." }

# 5. Çalıştır
python main.py
```

İlk açılışta `~/.jarvis/` dizini oluşur (hafıza, log, şifreleme anahtarı).

### 📦 Kendi .exe'ni Üret

```bash
build_exe.bat   # veya: pyinstaller jarvis.spec --noconfirm --clean
```

Çıktı: `dist/JARVIS/JARVIS.exe` — tüm `dist/JARVIS/` klasörünü taşıyabilirsin.

### 📥 Kendi Kurulum (Setup) Dosyanı Üret

[Inno Setup](https://jrsoftware.org/isdl.php) gerekli:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

Çıktı: `installer_out/JARVIS-Setup-1.0.0.exe`

---

## ⚙️ Yapılandırma

Tüm ayarlar [`core/config.py`](core/config.py) içinde. `.env` dosyasıyla veya
`JARVIS_*` ortam değişkenleriyle değiştirebilirsin. Örnek: [`.env.example`](.env.example).

| Ayar | Varsayılan | Ne işe yarar? |
|------|-----------|---------------|
| `JARVIS_SAFE_MODE` | `true` | Yıkıcı işlemlerde "emin misin?" diye sorar |
| `JARVIS_VOICE_NAME` | `Charon` | Konuşma sesi (`Charon`, `Aoede`, `Puck`...) |
| `JARVIS_INTERRUPT_RMS` | `0.18` | Sözünü kesme eşiği (yüksek = daha zor kesilir) |
| `JARVIS_DASHBOARD_PORT` | `8765` | Web paneli portu |
| `JARVIS_CTX_TOTAL_CAP` | `6000` | Hafıza bütçesi (karakter) |
| `SENTRY_DSN` | — | Hata izleme (opsiyonel) |

---

## 🏗️ Nasıl Çalışıyor?

```
🎙️  Mikrofon ──► Gemini Live ──┬── 🔊 Hoparlör (konuşur)
                                └── 🛠️  Araç çağrısı ──► Sonuç
```

Tek bir `qasync` event döngüsünde çalışır (Qt arayüzü + asyncio aynı thread).

| Katman | İçerik |
|--------|--------|
| **main.py** | `JarvisLive` orkestratör — ses I/O, araç yürütme, bağlam, reconnect |
| **actions/** | Her dosya bir araç (`<isim>_action`), lazy import + AST keşif |
| **memory/** | vault (şifreleme), vector_memory (RAG), episodic (SQLite), transkriptler |
| **core/** | config, logging, kişilik/duygu motorları, prompt |
| **dashboard/** | FastAPI web paneli |

Detaylı mimari için → [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🧪 Test & Geliştirme

```bash
pip install -e ".[dev]"

pytest                                      # 37 test
ruff check . --fix                          # lint + format
py-spy record -o profile.svg --pid <pid>    # canlı profil
```

---

## 🔐 Veriler ve Gizlilik

- 🏠 **Her şey bilgisayarında** — veriler `~/.jarvis/` altında, bulut yok
- 🔐 **Şifreli hafıza** — kalıcı bilgiler Fernet (AES-128) ile şifrelidir
- ⚠️ **Anahtarını yedekle** — `~/.jarvis/.key` kaybolursa hafızan açılamaz
- 🛡️ **Kod sandbox'ı** — `code_runner` kök silme, disk format gibi yıkıcı kalıpları reddeder
- 📡 **Sadece Gemini'ye ses/metin gider** — başka hiçbir servise veri akışı yoktur

---

## ❓ Sık Sorulanlar

**Mac veya Linux'ta çalışır mı?**
Kaynak koddan (Python ile) çalışır. Hazır kurulum dosyası şu an sadece Windows için.

**Ücretli mi?**
Hayır. Gemini API'nin **cömert ücretsiz kotası** kişisel kullanım için fazlasıyla yeter.

**Verilerim Google'a gidiyor mu?**
Sadece konuştuğun an o anki ses Gemini'ye iletilir. Kalıcı hafıza, dosyalar,
geçmiş — hepsi senin bilgisayarında kalır.

**İnternetsiz çalışır mı?**
Hayır, Gemini'ye bağlanmak gerekiyor. Tamamen offline bir alternatif planlanıyor.

**Sesimi tanır mı?**
Şu an konuşmacı tanıma yok — ortamdaki herkes konuşabilir.

---

## 📜 Köken & Lisans

**Geliştiren:** [Bora Mantar](https://github.com/Boramantr) — © 2026

Tamamen sıfırdan tasarlanıp geliştirilmiş; mimari, ses pipeline'ı, araç sistemi,
şifreli çok katmanlı hafıza, güvenlik kontrolleri, web paneli ve gözlemlenebilirlik
katmanları tek tek elden geçirilmiş, özelleştirilmiş bir sürümdür.
Değişiklik geçmişi → [CHANGELOG.md](CHANGELOG.md)

**Lisans:** Kişisel ve ticari olmayan kullanım için —
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

Ticari kullanım için lütfen iletişime geç.

---

<div align="center">
<sub>⚡ Yerel çalışır · Abonelik yok · Kontrol tamamen sende</sub>
<br><br>
⭐ Beğendiysen yıldız bırakmayı unutma!
</div>
