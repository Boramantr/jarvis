"""
Process Guard Action — Şüpheli process tespiti ve sistem güvenlik denetimi.
Kullanım: "Şüpheli processler var mı?", "Yüksek CPU kullanan ne?", "Başlangıç programlarını denetle"
"""
import subprocess

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

# Bilinen güvenli processler (whitelist)
SAFE_PROCESSES = {
    "svchost.exe", "explorer.exe", "csrss.exe", "lsass.exe", "services.exe",
    "smss.exe", "wininit.exe", "winlogon.exe", "dwm.exe", "taskhostw.exe",
    "RuntimeBroker.exe", "SearchHost.exe", "StartMenuExperienceHost.exe",
    "ShellExperienceHost.exe", "sihost.exe", "fontdrvhost.exe",
    "TextInputHost.exe", "ctfmon.exe", "conhost.exe", "dllhost.exe",
    "WmiPrvSE.exe", "spoolsv.exe", "SecurityHealthSystray.exe",
    "SecurityHealthService.exe", "MsMpEng.exe", "NisSrv.exe",
    "System", "Registry", "System Idle Process", "Idle",
    "python.exe", "pythonw.exe", "Code.exe", "chrome.exe", "msedge.exe",
    "firefox.exe", "spotify.exe", "discord.exe", "Teams.exe",
}

# Şüpheli konum patternleri
SUSPICIOUS_PATHS = [
    "\\temp\\", "\\tmp\\", "\\appdata\\local\\temp",
    "\\downloads\\", "\\public\\",
    "\\programdata\\", "\\users\\public",
]


def _get_process_info():
    """Tüm processlerin detaylı bilgisini al."""
    if not _PSUTIL:
        return []

    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info",
                                      "exe", "username", "create_time", "status"]):
        try:
            info = proc.info
            info["memory_mb"] = info["memory_info"].rss / (1024 * 1024) if info.get("memory_info") else 0
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes


def _calculate_risk(proc: dict) -> tuple[int, list[str]]:
    """Process için risk skoru hesapla (0-100)."""
    risk = 0
    reasons = []
    name = proc.get("name", "")
    exe = proc.get("exe", "") or ""
    cpu = proc.get("cpu_percent", 0) or 0
    mem_mb = proc.get("memory_mb", 0)

    # Bilinmeyen process
    if name not in SAFE_PROCESSES:
        risk += 15
        reasons.append("Bilinen güvenli listede değil")

    # Şüpheli konum
    exe_lower = exe.lower()
    for path in SUSPICIOUS_PATHS:
        if path in exe_lower:
            risk += 25
            reasons.append(f"Şüpheli konum: {path.strip(chr(92))}")
            break

    # Yüksek CPU
    if cpu > 80:
        risk += 20
        reasons.append(f"Yüksek CPU: %{cpu:.0f}")
    elif cpu > 50:
        risk += 10

    # Yüksek bellek
    if mem_mb > 1000:
        risk += 15
        reasons.append(f"Yüksek RAM: {mem_mb:.0f}MB")
    elif mem_mb > 500:
        risk += 5

    # Executable yolu yok
    if not exe and name not in ("System", "Registry", "Idle", "System Idle Process"):
        risk += 20
        reasons.append("Çalıştırılabilir yolu bulunamadı")

    return min(risk, 100), reasons


def process_guard_action(parameters: dict = None, player=None) -> str:
    params = parameters or {}
    action = params.get("action", "scan")

    if not _PSUTIL:
        return "❌ psutil kütüphanesi gerekli. pip install psutil"

    if player:
        player.write_log(f"[ProcessGuard] Komut: {action}")

    if action == "scan":
        processes = _get_process_info()
        suspicious = []

        for proc in processes:
            risk, reasons = _calculate_risk(proc)
            if risk >= 30:
                suspicious.append({
                    "name": proc.get("name", "?"),
                    "pid": proc.get("pid", 0),
                    "cpu": proc.get("cpu_percent", 0) or 0,
                    "memory_mb": proc.get("memory_mb", 0),
                    "exe": proc.get("exe", "Bilinmiyor") or "Bilinmiyor",
                    "risk": risk,
                    "reasons": reasons,
                })

        suspicious.sort(key=lambda x: x["risk"], reverse=True)

        lines = ["🛡️ Process Güvenlik Taraması:"]
        lines.append(f"  ✅ {len(processes)} process tarandı")

        if not suspicious:
            lines.append("  ✅ Şüpheli process bulunamadı. Sistem temiz görünüyor.")
        else:
            lines.append(f"  ⚠️ {len(suspicious)} şüpheli process bulundu:\n")
            for s in suspicious[:8]:
                icon = "🔴" if s["risk"] >= 70 else "🟡" if s["risk"] >= 50 else "🟠"
                lines.append(f"  {icon} Risk: {s['risk']}/100 — {s['name']}")
                lines.append(f"     PID: {s['pid']} | CPU: %{s['cpu']:.0f} | RAM: {s['memory_mb']:.0f}MB")
                lines.append(f"     Konum: {s['exe'][:80]}")
                lines.append(f"     Sebep: {', '.join(s['reasons'])}")
                lines.append("")

        return "\n".join(lines)

    elif action == "high_cpu":
        threshold = float(params.get("threshold", 30))
        processes = _get_process_info()
        high = [p for p in processes if (p.get("cpu_percent") or 0) > threshold]
        high.sort(key=lambda x: x.get("cpu_percent", 0) or 0, reverse=True)

        if not high:
            return f"✅ %{threshold:.0f} üzerinde CPU kullanan process yok."

        lines = [f"🔥 Yüksek CPU Kullanan Processler (>{threshold:.0f}%):"]
        for p in high[:10]:
            lines.append(f"  {p['name']} — PID: {p['pid']} | CPU: %{p.get('cpu_percent', 0):.0f} | RAM: {p['memory_mb']:.0f}MB")
        return "\n".join(lines)

    elif action == "high_memory":
        threshold = float(params.get("threshold", 500))
        processes = _get_process_info()
        high = [p for p in processes if p.get("memory_mb", 0) > threshold]
        high.sort(key=lambda x: x.get("memory_mb", 0), reverse=True)

        if not high:
            return f"✅ {threshold:.0f}MB üzerinde RAM kullanan process yok."

        lines = [f"🧠 Yüksek RAM Kullanan Processler (>{threshold:.0f}MB):"]
        for p in high[:10]:
            lines.append(f"  {p['name']} — PID: {p['pid']} | RAM: {p['memory_mb']:.0f}MB | CPU: %{p.get('cpu_percent', 0):.0f}")
        return "\n".join(lines)

    elif action == "network":
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED' and conn.raddr:
                try:
                    proc = psutil.Process(conn.pid)
                    connections.append({
                        "name": proc.name(),
                        "pid": conn.pid,
                        "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                        "remote": f"{conn.raddr.ip}:{conn.raddr.port}",
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        if not connections:
            return "✅ Aktif ağ bağlantısı bulunamadı."

        # Benzersiz process bazlı grupla
        seen = {}
        for c in connections:
            key = c["name"]
            if key not in seen:
                seen[key] = {"name": c["name"], "pid": c["pid"], "remotes": []}
            seen[key]["remotes"].append(c["remote"])

        lines = [f"🌐 Aktif Ağ Bağlantıları ({len(connections)} bağlantı):"]
        for app in sorted(seen.values(), key=lambda x: len(x["remotes"]), reverse=True):
            lines.append(f"  📡 {app['name']} (PID: {app['pid']}) — {len(app['remotes'])} bağlantı")
            for r in app["remotes"][:3]:
                lines.append(f"     → {r}")
            if len(app["remotes"]) > 3:
                lines.append(f"     ... +{len(app['remotes'])-3} daha")
        return "\n".join(lines)

    elif action == "startup":
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10
            )
            import json
            items = json.loads(result.stdout) if result.stdout.strip() else []
            if isinstance(items, dict):
                items = [items]

            if not items:
                return "✅ Başlangıç programı bulunamadı."

            lines = [f"🚀 Başlangıç Programları ({len(items)} adet):"]
            for item in items:
                name = item.get("Name", "?")
                cmd = item.get("Command", "?")
                loc = item.get("Location", "?")
                # Basit risk değerlendirmesi
                is_known = any(safe.lower() in cmd.lower() for safe in
                             ["microsoft", "google", "nvidia", "realtek", "intel", "amd", "logitech"])
                icon = "✅" if is_known else "⚠️"
                lines.append(f"  {icon} {name}")
                lines.append(f"     Komut: {cmd[:80]}")
                lines.append(f"     Konum: {loc}")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Başlangıç programları okunamadı: {e}"

    elif action == "kill":
        target = params.get("name") or params.get("target", "")
        pid = params.get("pid")

        if pid:
            try:
                proc = psutil.Process(int(pid))
                name = proc.name()
                proc.terminate()
                return f"✅ Process sonlandırıldı: {name} (PID: {pid})"
            except Exception as e:
                return f"❌ Process sonlandırılamadı: {e}"
        elif target:
            killed = 0
            for proc in psutil.process_iter(["name"]):
                try:
                    if target.lower() in proc.info["name"].lower():
                        proc.terminate()
                        killed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed:
                return f"✅ {killed} '{target}' process'i sonlandırıldı."
            return f"❌ '{target}' adlı process bulunamadı."

        return "Process adı veya PID belirtilmeli."

    return "Geçersiz komut. Kullanılabilir: scan, high_cpu, high_memory, network, startup, kill"
