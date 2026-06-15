"""
Google Workspace & Browser Integration — JARVIS Google Asistanı
Chrome kontrolü, YouTube deşifre, Çeviri, Takvim ve Drive
"""
import urllib.parse
import webbrowser

try:
    import pyautogui
    _PYAUTO = True
except ImportError:
    _PYAUTO = False

try:
    import pyperclip
    _PYCLIP = True
except ImportError:
    _PYCLIP = False

try:
    from deep_translator import GoogleTranslator
    _TRANS = True
except ImportError:
    _TRANS = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    _YT = True
except ImportError:
    _YT = False


def _gmail_assistant(query: str) -> str:
    """Gmail'de arama yapar ve açar."""
    safe_query = urllib.parse.quote(query)
    url = f"https://mail.google.com/mail/u/0/#search/{safe_query}"
    webbrowser.open(url)
    return f"📧 Gmail açıldı ve şu arama yapıldı: '{query}'"


def _youtube_summarizer(video_url: str) -> str:
    """YouTube videosunun deşifresini (transcript) çeker."""
    if not _YT:
        return "❌ youtube-transcript-api kütüphanesi eksik."

    try:
        video_id = ""
        if "v=" in video_url:
            video_id = video_url.split("v=")[1][:11]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("youtu.be/")[1][:11]
        else:
            return "❌ Geçersiz YouTube linki."

        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['tr', 'en'])
        full_text = " ".join([t['text'] for t in transcript_list])

        summary = full_text[:1500] + ("...\n[Metin çok uzun, özetlendi]" if len(full_text) > 1500 else "")
        return f"📺 YouTube Video Deşifresi (Video ID: {video_id}):\n\n{summary}\n\n🤖 Not: Ben JARVIS olarak bu metnin tamamını görüp sana özetini çıkarabilirim."
    except Exception as e:
        return f"❌ YouTube deşifre hatası (Video altyazısı kapalı veya geçersiz olabilir): {e}"


def _chrome_controller(action: str) -> str:
    """Chrome sekmelerini pyautogui ile kontrol eder."""
    if not _PYAUTO:
        return "❌ pyautogui eksik."

    try:
        if action == "new_tab":
            pyautogui.hotkey('ctrl', 't')
            return "🌐 Chrome: Yeni sekme açıldı."
        elif action == "close_tab":
            pyautogui.hotkey('ctrl', 'w')
            return "🌐 Chrome: Geçerli sekme kapatıldı."
        elif action == "next_tab":
            pyautogui.hotkey('ctrl', 'tab')
            return "🌐 Chrome: Sonraki sekmeye geçildi."
        elif action == "scroll_down":
            pyautogui.scroll(-500)
            return "🌐 Chrome: Sayfa aşağı kaydırıldı."
        else:
            return "❌ Bilinmeyen Chrome eylemi."
    except Exception as e:
        return f"❌ Chrome kontrol hatası: {e}"


def _google_calendar(title: str, date: str) -> str:
    """Google Takvim'e randevu ekleme sayfasını açar."""
    safe_title = urllib.parse.quote(title)
    url = f"https://calendar.google.com/calendar/r/eventedit?text={safe_title}"
    webbrowser.open(url)
    return f"📅 Takvim eklentisi açıldı: '{title}' - Lütfen kaydedin."


def _google_drive(query: str) -> str:
    """Google Drive'da arama yapar."""
    safe_query = urllib.parse.quote(query)
    url = f"https://drive.google.com/drive/search?q={safe_query}"
    webbrowser.open(url)
    return f"☁️ Google Drive açıldı ve arandı: '{query}'"


def _translate_clipboard() -> str:
    """Panodaki metni İngilizce/Türkçe'ye çevirir."""
    if not _PYCLIP or not _TRANS:
        return "❌ pyperclip veya deep-translator kütüphaneleri eksik."

    try:
        text = pyperclip.paste()
        if not text:
            return "⚠️ Panoda (Clipboard) çevrilecek metin bulunamadı."

        tr_chars = "şğüöç"
        if any(c in text.lower() for c in tr_chars):
            target = "en"
            lang_str = "İngilizce"
        else:
            target = "tr"
            lang_str = "Türkçe"

        translated = GoogleTranslator(source='auto', target=target).translate(text)
        return f"🌍 Panodaki Metin ({lang_str} Çevirisi):\n\n{translated}"
    except Exception as e:
        return f"❌ Çeviri hatası: {e}"


def google_workspace_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "status")

    if player:
        player.write_log(f"[Google] Komut: {action}")

    if action == "gmail_search":
        query = params.get("query", "is:unread")
        return _gmail_assistant(query)

    elif action == "youtube_summary":
        url = params.get("url", "")
        if not url: return "❌ YouTube URL'si belirtilmedi."
        return _youtube_summarizer(url)

    elif action == "chrome_control":
        ctrl = params.get("control", "new_tab")
        return _chrome_controller(ctrl)

    elif action == "calendar_add":
        title = params.get("title", "Yeni Randevu")
        return _google_calendar(title, "")

    elif action == "drive_search":
        query = params.get("query", "")
        if not query: return "❌ Aranacak kelime belirtilmedi."
        return _google_drive(query)

    elif action == "translate_clipboard":
        return _translate_clipboard()

    elif action == "status":
        return (
            "🌐 Google Workspace Araçları:\n"
            "  • gmail_search       — Gmail'de arama yapar\n"
            "  • youtube_summary    — YT videosu altyazısını çeker\n"
            "  • chrome_control     — Tarayıcı sekmelerini yönetir\n"
            "  • calendar_add       — Takvime etkinlik ekler\n"
            "  • drive_search       — Drive dosyalarında arama yapar\n"
            "  • translate_clipboard — Panodaki metni anında çevirir"
        )

    return "Geçersiz komut. Kullanılabilir: gmail_search, youtube_summary, chrome_control, calendar_add, drive_search, translate_clipboard"
