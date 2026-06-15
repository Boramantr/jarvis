import os
import time

import keyboard
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# --- SPOTIFY API AYARLARI ---
SPOTIPY_CLIENT_ID = "435af5a1d6c94a9ab4363fffeaf8588f"
SPOTIPY_CLIENT_SECRET = "583b5b2d724b41b7bb2221879bb5a9bc"
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

def get_spotify_client():
    if SPOTIPY_CLIENT_ID == "BURAYA_CLIENT_ID_GELECEK" or "KENDİ_CLIENT" in SPOTIPY_CLIENT_ID:
        return None
    try:
        return spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope="user-modify-playback-state user-read-playback-state user-library-modify"
        ))
    except Exception:
        return None

def spotify_control_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "")
    query = params.get("query", "")
    value = params.get("value", "")

    if player: player.write_log(f"[Müzik] Komut: {action}")

    sp = get_spotify_client()

    # --- 1. UYGULAMA AÇMA ---
    if action == "open":
        os.system("start spotify:")
        time.sleep(1.5)
        return "Spotify başlatıldı efendim."

    # --- 2. BEĞENİLENLERE EKLEME ---
    elif action in ["like", "like_song"]:
        if not sp: return "Efendim, bu özellik için API anahtarlarınızı girmelisiniz."
        try:
            playback = sp.current_playback()
            if playback and playback.get('item'):
                track_id = playback['item']['id']
                track_name = playback['item']['name']
                sp.current_user_saved_tracks_add([track_id])
                return f"Halledildi efendim. '{track_name}' Beğenilenler listenize eklendi."
            else:
                return "Şu anda aktif olarak çalan bir şarkı bulamadım efendim."
        except Exception as e:
            return f"Şarkıyı kaydederken bir sorun oluştu: {e}"

    # --- 3. SES KONTROLLERİ ---
    elif action in ["volume_up", "volume_down", "volume_set"]:
        if sp:
            try:
                playback = sp.current_playback()
                if playback and playback.get('device'):
                    current_vol = playback['device']['volume_percent']
                    if action == "volume_up": new_vol = min(100, current_vol + 15)
                    elif action == "volume_down": new_vol = max(0, current_vol - 15)
                    else: new_vol = int(value) if str(value).isdigit() else 50
                    sp.volume(new_vol)
                    return f"Ses seviyesi %{new_vol} yapıldı efendim."
            except: pass
        if action == "volume_up":
            for _ in range(10): keyboard.send("volume up")
        elif action == "volume_down":
            for _ in range(10): keyboard.send("volume down")
        return "Sistem sesi ayarlandı."

    # --- 4. SONRAKİ / ÖNCEKİ ---
    elif action in ["next", "previous", "prev"]:
        if sp:
            try:
                if action == "next": sp.next_track()
                else: sp.previous_track()
                return "Şarkı değiştirildi."
            except: pass
        keyboard.send("next track" if action == "next" else "previous track")
        return "Şarkı değiştirildi."

    # --- 5. OYNAT / DURDUR ---
    elif action in ["play", "play_pause", "pause"]:
        if sp:
            try:
                devices = sp.devices()
                active_device = None
                if devices and devices.get('devices'):
                    for d in devices['devices']:
                        if d['is_active']: active_device = d['id']
                    if not active_device: active_device = devices['devices'][0]['id']

                playback = sp.current_playback()
                is_playing = playback['is_playing'] if playback else False

                if action == "pause" or (action == "play_pause" and is_playing):
                    if is_playing: sp.pause_playback(device_id=active_device)
                    return "Müzik durduruldu."
                else:
                    sp.start_playback(device_id=active_device)
                    return "Müzik başlatıldı."
            except Exception:
                pass
        keyboard.send("play/pause media")
        return "Müzik komutu gönderildi."

    # --- 6. ARAMA VE ÇALMA ---
    elif action in ["search_play", "search_playlist", "search"]:
        if not query: return "Efendim, kimi veya neyi aramamı istersiniz?"
        if not sp:
            os.system(f"start spotify:search:{query.replace(' ', '%20')}")
            return f"Ekranda {query} aramasını açtım."
        try:
            results = sp.search(q=query, type='track,playlist', limit=1)
            devices = sp.devices()
            active_device = None
            if devices and devices.get('devices'):
                active_device = devices['devices'][0]['id']

            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                track_name = results['tracks']['items'][0]['name']
                if active_device:
                    sp.start_playback(device_id=active_device, uris=[track_uri])
                    return f"'{track_name}' çalınıyor efendim."

            elif results['playlists']['items']:
                playlist_uri = results['playlists']['items'][0]['uri']
                playlist_name = results['playlists']['items'][0]['name']
                if active_device:
                    sp.start_playback(device_id=active_device, context_uri=playlist_uri)
                    return f"'{playlist_name}' listesi başlatıldı."

            os.system(f"start spotify:search:{query.replace(' ', '%20')}")
            return "Arama ekranını açtım efendim."
        except Exception:
            os.system(f"start spotify:search:{query.replace(' ', '%20')}")
            return "Arama sonuçlarını ekrana getirdim efendim."

    # --- 7. SHUFFLE (KARIŞTIRMA) ---
    elif action == "shuffle":
        if sp:
            try:
                playback = sp.current_playback()
                current_shuffle = playback.get("shuffle_state", False) if playback else False
                sp.shuffle(not current_shuffle)
                state = "açıldı" if not current_shuffle else "kapatıldı"
                return f"Karıştırma {state} efendim."
            except Exception:
                pass
        return "Karıştırma ayarı değiştirilemedi."

    # --- 8. REPEAT (TEKRAR) ---
    elif action == "repeat":
        if sp:
            try:
                playback = sp.current_playback()
                current_repeat = playback.get("repeat_state", "off") if playback else "off"
                cycle = {"off": "context", "context": "track", "track": "off"}
                new_state = cycle.get(current_repeat, "off")
                sp.repeat(new_state)
                states_tr = {"off": "kapalı", "context": "liste tekrarı", "track": "şarkı tekrarı"}
                return f"Tekrar modu: {states_tr.get(new_state, new_state)}"
            except Exception:
                pass
        return "Tekrar ayarı değiştirilemedi."

    # --- 9. ŞU AN ÇALAN ---
    elif action in ("current", "now_playing", "what"):
        if sp:
            try:
                playback = sp.current_playback()
                if playback and playback.get("item"):
                    item = playback["item"]
                    name = item.get("name", "Bilinmeyen")
                    artists = ", ".join(a["name"] for a in item.get("artists", []))
                    album = item.get("album", {}).get("name", "")
                    duration_ms = item.get("duration_ms", 0)
                    progress_ms = playback.get("progress_ms", 0)
                    duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
                    progress = f"{progress_ms // 60000}:{(progress_ms % 60000) // 1000:02d}"
                    is_playing = "▶️" if playback.get("is_playing") else "⏸️"
                    return (
                        f"{is_playing} Şu An Çalıyor:\n"
                        f"  🎵 {name}\n"
                        f"  🎤 {artists}\n"
                        f"  💿 {album}\n"
                        f"  ⏱️ {progress} / {duration}"
                    )
                return "Şu anda çalan bir şarkı yok efendim."
            except Exception:
                pass
        return "Spotify bilgisi alınamadı."

    # --- 10. KUYRUK ---
    elif action == "queue":
        if sp:
            try:
                queue = sp.queue()
                tracks = queue.get("queue", [])[:5]
                if not tracks:
                    return "Kuyrukta şarkı yok."
                lines = ["🎶 Sıradaki Şarkılar:"]
                for i, t in enumerate(tracks, 1):
                    artist = t.get("artists", [{}])[0].get("name", "?")
                    lines.append(f"  {i}. {t.get('name', '?')} — {artist}")
                return "\n".join(lines)
            except Exception:
                pass
        return "Kuyruk bilgisi alınamadı."

    # --- 11. SON DİNLENENLER ---
    elif action == "recently_played":
        if sp:
            try:
                recent = sp.current_user_recently_played(limit=8)
                items = recent.get("items", [])
                if not items:
                    return "Son dinlenen şarkı bulunamadı."
                lines = ["🕐 Son Dinlenenler:"]
                for item in items:
                    track = item.get("track", {})
                    name = track.get("name", "?")
                    artist = track.get("artists", [{}])[0].get("name", "?")
                    lines.append(f"  🎵 {name} — {artist}")
                return "\n".join(lines)
            except Exception:
                pass
        return "Son dinlenenler alınamadı."

    return "Bilinmeyen bir müzik komutu verdiniz."
