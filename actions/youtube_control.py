import re
import time
import urllib.parse
import urllib.request
import webbrowser

import keyboard


def youtube_control_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "")
    query = params.get("query", "")
    value = params.get("value", "")

    if player: player.write_log(f"[YouTube] Komut: {action}")

    # --- 1. VİDEO ARAMA VE OTO-OYNATMA ---
    if action == "play":
        if not query: return "Efendim, ne çalmamı veya açmamı istersiniz?"
        try:
            query_string = urllib.parse.urlencode({"search_query": query})
            html_content = urllib.request.urlopen("https://www.youtube.com/results?" + query_string)
            search_results = re.findall(r'watch\?v=(\S{11})', html_content.read().decode())
            if search_results:
                video_url = "https://www.youtube.com/watch?v=" + search_results[0]
                webbrowser.open(video_url)
                return f"'{query}' YouTube'da açılıyor efendim."
            else:
                return "Bununla ilgili bir video bulamadım."
        except Exception as e:
            return f"Video aranırken bir sorun oluştu: {e}"

    elif action == "search":
        if not query: return "Ne aramamı istersiniz?"
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(url)
        return f"YouTube'da '{query}' için sonuçlar listelendi."

    # --- 2. SAYFA YÖNLENDİRMELERİ ---
    elif action == "home":
        webbrowser.open("https://www.youtube.com")
        return "YouTube ana sayfası açıldı."
    elif action == "shorts":
        webbrowser.open("https://www.youtube.com/shorts")
        return "YouTube Shorts bölümüne geçildi."
    elif action == "subscriptions":
        webbrowser.open("https://www.youtube.com/feed/subscriptions")
        return "Abonelikleriniz açıldı efendim."
    elif action == "trending":
        webbrowser.open("https://www.youtube.com/feed/trending")
        return "Şu an trend olan videolar açıldı."

    # --- 3. DİNAMİK SÜRE KONTROLLERİ ---
    elif action in ["forward", "backward"]:
        try:
            seconds = int(value) if str(value).isdigit() else 10
        except:
            seconds = 10
        presses_10s = seconds // 10
        remainder_5s = (seconds % 10) >= 5
        main_key = "l" if action == "forward" else "j"
        fine_key = "right" if action == "forward" else "left"
        for _ in range(presses_10s):
            keyboard.send(main_key)
            time.sleep(0.05)
        if remainder_5s:
            keyboard.send(fine_key)
        yön = "ileri" if action == "forward" else "geri"
        return f"Video {seconds} saniye {yön} sarıldı efendim."

    # --- 4. DİNAMİK SES KONTROLLERİ ---
    elif action == "volume_set":
        try:
            target_vol = int(value) if str(value).isdigit() else 50
            target_vol = max(0, min(100, target_vol))
            presses = target_vol // 5
            for _ in range(20):
                keyboard.send("down")
                time.sleep(0.02)
            for _ in range(presses):
                keyboard.send("up")
                time.sleep(0.02)
            return f"YouTube sesi %{target_vol} olarak ayarlandı efendim."
        except:
            return "Ses seviyesi anlaşılamadı."

    elif action == "volume_up":
        for _ in range(3): keyboard.send("up")
        return "YouTube sesi artırıldı."
    elif action == "volume_down":
        for _ in range(3): keyboard.send("down")
        return "YouTube sesi azaltıldı."

    # --- 5. EKSTRA MEDYA KONTROLLERİ ---
    elif action in ["pause", "play_pause"]:
        keyboard.send("k")
        return "Video durduruldu veya başlatıldı."
    elif action == "fullscreen":
        keyboard.send("f")
        return "Tam ekran moduna geçildi."
    elif action == "theater":
        keyboard.send("t")
        return "Sinema moduna geçildi efendim."
    elif action == "captions":
        keyboard.send("c")
        return "Altyazılar değiştirildi."
    elif action == "mute":
        keyboard.send("m")
        return "Videonun sesi kapatıldı/açıldı."
    elif action == "speed_up":
        keyboard.send("shift+.")
        return "Video oynatma hızı artırıldı."
    elif action == "speed_down":
        keyboard.send("shift+,")
        return "Video oynatma hızı azaltıldı."

    # --- 6. BEĞENME ---
    elif action == "like":
        keyboard.send("l")
        time.sleep(0.1)
        return "Video beğenildi efendim."

    elif action == "dislike":
        keyboard.send("d")
        time.sleep(0.1)
        return "Video beğenilmedi olarak işaretlendi."

    # --- 7. SONRAKİ/ÖNCEKİ VİDEO ---
    elif action == "next_video":
        keyboard.send("shift+n")
        return "Sonraki videoya geçildi."

    elif action == "previous_video":
        keyboard.send("shift+p")
        return "Önceki videoya dönüldü."

    # --- 8. MİNİ PLAYER ---
    elif action == "miniplayer":
        keyboard.send("i")
        return "Mini player modu değiştirildi."

    # --- 9. PLAYLIST ---
    elif action == "playlist":
        if not query:
            webbrowser.open("https://www.youtube.com/feed/library")
            return "YouTube kütüphaneniz açıldı."
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query + ' playlist')}"
        webbrowser.open(url)
        return f"'{query}' playlistleri aranıyor."

    # --- 10. KANAL ---
    elif action == "channel":
        if not query:
            return "Hangi kanalı açmamı istersiniz?"
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query + ' channel')}&sp=EgIQAg%253D%253D"
        webbrowser.open(url)
        return f"'{query}' kanalı aranıyor."

    # --- 11. STATS FOR NERDS ---
    elif action == "stats":
        keyboard.send("ctrl+shift+d")
        return "Video istatistikleri gösterildi."

    # --- 12. LOOP ---
    elif action == "loop":
        # Sağ tık menüsüyle loop — keyboard shortcut yok, alternatif
        return "YouTube'da loop için videoya sağ tıklayıp 'Döngü' seçeneğini kullanabilirsiniz."

    return "Geçersiz bir YouTube komutu efendim."
