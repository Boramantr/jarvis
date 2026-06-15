import os
import time

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


def task_manager_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "")
    target = params.get("target", "")

    if player: player.write_log(f"[Sistem] Görev: {action} - Hedef: {target}")

    # --- 1. PROGRAMLARI ZORLA KAPATMA (KILL) ---
    if action == "kill":
        if not target:
            return "Hangi uygulamayı kapatmamı istersiniz efendim?"

        app_exe = target.lower()

        if "chrome" in app_exe or "google" in app_exe: app_exe = "chrome.exe"
        elif "spotify" in app_exe: app_exe = "spotify.exe"
        elif "discord" in app_exe: app_exe = "discord.exe"
        elif "word" in app_exe: app_exe = "winword.exe"
        elif "excel" in app_exe: app_exe = "excel.exe"
        elif "code" in app_exe or "vs" in app_exe: app_exe = "code.exe"
        elif "telegram" in app_exe: app_exe = "telegram.exe"
        elif "steam" in app_exe: app_exe = "steam.exe"
        elif "epic" in app_exe: app_exe = "EpicGamesLauncher.exe"
        elif "firefox" in app_exe: app_exe = "firefox.exe"
        elif "edge" in app_exe: app_exe = "msedge.exe"
        elif "brave" in app_exe: app_exe = "brave.exe"
        elif "obs" in app_exe: app_exe = "obs64.exe"

        if not app_exe.endswith(".exe"):
            app_exe += ".exe"

        result = os.system(f'taskkill /F /IM "{app_exe}" /T')

        if result == 0:
            return f"Görev tamamlandı efendim. {target} zorla kapatıldı."
        else:
            return f"{target} adlı programı bulamadım veya zaten kapalı."

    # --- 2. GÖREV YÖNETİCİSİ VE PERFORMANS EKRANI ---
    elif action == "open_performance":
        os.system("start taskmgr")
        os.system("start perfmon /res")
        return "Görev Yöneticisi ve Performans İzleyici ekranlarını açtım efendim."

    elif action == "open":
        os.system("start taskmgr")
        return "Görev Yöneticisi açıldı efendim."

    # --- 3. SİSTEM BİLGİSİ ---
    elif action == "system_info":
        if not _PSUTIL:
            return "psutil yüklü değil. pip install psutil"
        try:
            import platform
            cpu_count = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            cpu_percent = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)

            lines = [
                "💻 Sistem Bilgisi:",
                f"  🖥️ OS: {platform.system()} {platform.release()}",
                f"  ⚙️ CPU: {cpu_count} çekirdek, {cpu_freq.current:.0f} MHz" if cpu_freq else f"  ⚙️ CPU: {cpu_count} çekirdek",
                f"  📊 CPU Kullanım: %{cpu_percent}",
                f"  🧠 RAM: {ram.used // (1024**3)}/{ram.total // (1024**3)} GB (%{ram.percent})",
                f"  💾 Disk: {disk.used // (1024**3)}/{disk.total // (1024**3)} GB (%{disk.percent})",
                f"  ⏱️ Açık Süre: {uptime_hours}s {uptime_minutes}dk",
            ]

            battery = psutil.sensors_battery()
            if battery:
                plug = "🔌 Şarjda" if battery.power_plugged else "🔋 Pilde"
                lines.append(f"  🔋 Batarya: %{battery.percent} {plug}")

            return "\n".join(lines)
        except Exception as e:
            return f"Sistem bilgisi alınamadı: {e}"

    # --- 4. EN ÇOK KAYNAK KULLANAN PROCESSLER ---
    elif action == "list_processes":
        if not _PSUTIL:
            return "psutil yüklü değil."
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    if info['memory_percent'] and info['memory_percent'] > 0.1:
                        processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # RAM'e göre sırala
            processes.sort(key=lambda p: p.get('memory_percent', 0), reverse=True)
            top = processes[:10]

            lines = ["📊 En Çok Kaynak Kullanan 10 Process:"]
            for p in top:
                lines.append(f"  {p['name']}: RAM %{p['memory_percent']:.1f}, CPU %{p.get('cpu_percent', 0):.1f}")
            return "\n".join(lines)
        except Exception as e:
            return f"Process listesi alınamadı: {e}"

    # --- 5. DİSK KULLANIMI ---
    elif action == "disk_usage":
        if not _PSUTIL:
            return "psutil yüklü değil."
        try:
            partitions = psutil.disk_partitions()
            lines = ["💾 Disk Kullanımı:"]
            for p in partitions:
                try:
                    usage = psutil.disk_usage(p.mountpoint)
                    lines.append(
                        f"  {p.device} ({p.mountpoint}): "
                        f"{usage.used // (1024**3)}/{usage.total // (1024**3)} GB "
                        f"(%{usage.percent}) — {usage.free // (1024**3)} GB boş"
                    )
                except PermissionError:
                    pass
            return "\n".join(lines)
        except Exception as e:
            return f"Disk bilgisi alınamadı: {e}"

    # --- 6. AĞ BİLGİSİ ---
    elif action == "network_info":
        if not _PSUTIL:
            return "psutil yüklü değil."
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            net_io = psutil.net_io_counters()
            sent_gb = net_io.bytes_sent / (1024**3)
            recv_gb = net_io.bytes_recv / (1024**3)

            lines = [
                "🌐 Ağ Bilgisi:",
                f"  🖥️ Hostname: {hostname}",
                f"  📡 Yerel IP: {local_ip}",
                f"  📤 Gönderilen: {sent_gb:.2f} GB",
                f"  📥 Alınan: {recv_gb:.2f} GB",
            ]

            addrs = psutil.net_if_addrs()
            for iface, addr_list in addrs.items():
                for addr in addr_list:
                    if addr.family == socket.AF_INET and addr.address != "127.0.0.1":
                        lines.append(f"  🔗 {iface}: {addr.address}")
                        break

            return "\n".join(lines)
        except Exception as e:
            return f"Ağ bilgisi alınamadı: {e}"

    # --- 7. BATARYA ---
    elif action == "battery":
        if not _PSUTIL:
            return "psutil yüklü değil."
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return "Batarya bulunamadı — masaüstü bilgisayar olabilir."

            plug = "🔌 Şarjda" if battery.power_plugged else "🔋 Pilde"
            secs_left = battery.secsleft
            if secs_left == psutil.POWER_TIME_UNLIMITED:
                time_left = "∞"
            elif secs_left == psutil.POWER_TIME_UNKNOWN:
                time_left = "Bilinmiyor"
            else:
                hours = secs_left // 3600
                minutes = (secs_left % 3600) // 60
                time_left = f"{hours}s {minutes}dk"

            return (
                f"🔋 Batarya Durumu:\n"
                f"  Şarj: %{battery.percent}\n"
                f"  Durum: {plug}\n"
                f"  Kalan Süre: {time_left}"
            )
        except Exception as e:
            return f"Batarya bilgisi alınamadı: {e}"

    return "Geçersiz bir görev komutu."

