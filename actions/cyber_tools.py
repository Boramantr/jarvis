"""
Cyber Tools Action — Siber güvenlik araçları.
CVE sorgusu, zafiyet takvimi, güvenlik haberleri, ağ cihaz tarama.
Kullanım: "CVE-2024-1234 nedir?", "Son güvenlik haberleri", "Ağıma bağlı cihazları göster"
"""
import json
import os
import re
import socket
import subprocess
import winreg
from datetime import datetime

_UNDO_STACK = []
_PENDING_ACTION = None

def _add_undo(action_type: str, data: dict, description: str):
    _UNDO_STACK.append({"type": action_type, "data": data, "desc": description})

def _undo_last_action() -> str:
    if not _UNDO_STACK:
        return "❌ Geri alınacak bir işlem bulunamadı."

    last = _UNDO_STACK.pop()
    atype = last["type"]
    data = last["data"]

    try:
        if atype == "panic_lockdown":
            subprocess.run(["powershell", "-Command", "Enable-NetAdapter -Name * -Confirm:$false"], capture_output=True)
            return f"✅ Geri Alındı: {last['desc']} (Ağ bağlantıları tekrar aktif edildi)"

        elif atype == "block_ip":
            rule_name = data["rule_name"]
            subprocess.run(["powershell", "-Command", f"Remove-NetFirewallRule -Name '{rule_name}'"], capture_output=True)
            return f"✅ Geri Alındı: {last['desc']} (IP engeli kaldırıldı)"

        elif atype == "quarantine":
            orig_path = data["orig_path"]
            quar_path = data["quar_path"]
            import shutil
            shutil.move(quar_path, orig_path)
            return f"✅ Geri Alındı: {last['desc']} (Dosya karantinadan çıkarıldı)"

        elif atype == "hosts_restore":
            orig_path = data["orig_path"]
            bak_path = data["bak_path"]
            import shutil
            shutil.copy(bak_path, orig_path)
            return f"✅ Geri Alındı: {last['desc']} (Hosts dosyası eski haline getirildi)"

        return f"⚠️ Bilinmeyen geri alma işlemi: {atype}"
    except Exception as e:
        return f"❌ Geri alma başarısız oldu: {e}"

try:
    import requests
    _REQ = True
except ImportError:
    _REQ = False

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


def _cve_lookup(cve_id: str) -> str:
    """CVE bilgisi sorgula — NVD API."""
    if not _REQ:
        return "❌ requests kütüphanesi gerekli."

    cve_id = cve_id.upper().strip()
    if not re.match(r"CVE-\d{4}-\d+", cve_id):
        return f"❌ Geçersiz CVE formatı: {cve_id}. Doğru format: CVE-YYYY-NNNNN"

    try:
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "JARVIS-Security/1.0"})

        if resp.status_code == 200:
            data = resp.json()
            vulns = data.get("vulnerabilities", [])
            if not vulns:
                return f"❌ {cve_id} bulunamadı."

            cve = vulns[0].get("cve", {})
            descriptions = cve.get("descriptions", [])
            desc = next((d["value"] for d in descriptions if d["lang"] == "en"), "Açıklama yok")

            # CVSS skoru
            metrics = cve.get("metrics", {})
            cvss_score = "?"
            severity = "?"
            for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if key in metrics:
                    cvss_data = metrics[key][0].get("cvssData", {})
                    cvss_score = cvss_data.get("baseScore", "?")
                    severity = cvss_data.get("baseSeverity", "?")
                    break

            published = cve.get("published", "?")[:10]

            # Severity icon
            sev_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(str(severity).upper(), "⚪")

            lines = [
                f"🛡️ {cve_id}",
                f"  {sev_icon} CVSS: {cvss_score}/10 ({severity})",
                f"  📅 Yayın: {published}",
                f"  📝 {desc[:300]}{'...' if len(desc) > 300 else ''}",
            ]
            return "\n".join(lines)

        return f"❌ NVD API hatası: HTTP {resp.status_code}"
    except Exception as e:
        return f"❌ CVE sorgusu başarısız: {e}"


def _vulnerability_calendar() -> str:
    """Bu ayki güvenlik yamaları ve zafiyet takvimi."""
    now = datetime.now()
    # Patch Tuesday = Ayın ikinci Salısı
    day = 1
    tuesdays = 0
    import calendar
    for d in range(1, 29):
        if calendar.weekday(now.year, now.month, d) == 1:  # Salı
            tuesdays += 1
            if tuesdays == 2:
                patch_tuesday = d
                break

    lines = [
        f"📅 Güvenlik Takvimi — {now.strftime('%B %Y')}:",
        f"  🔧 Microsoft Patch Tuesday: {now.strftime('%Y-%m')}-{patch_tuesday:02d}",
        "  📋 Kontrol Listesi:",
        "    ☐ Windows Update kontrol et",
        "    ☐ Tarayıcı güncellemelerini kontrol et (Chrome/Edge/Firefox)",
        "    ☐ Antivirüs tanımlamalarını güncelle",
        "    ☐ Üçüncü parti yazılım güncellemeleri (Adobe, Java, Python)",
        "    ☐ Firmware güncellemeleri (BIOS/UEFI, router)",
        "  🔗 Detay: https://msrc.microsoft.com/update-guide",
    ]
    return "\n".join(lines)


def _security_news() -> str:
    """Güncel siber güvenlik haberleri."""
    if not _REQ:
        return "❌ requests kütüphanesi gerekli."

    try:
        # The Hacker News RSS
        headers = {"User-Agent": "JARVIS-Security/1.0"}
        resp = requests.get("https://feeds.feedburner.com/TheHackersNews", headers=headers, timeout=10)

        if resp.status_code == 200:
            # Basit XML parse
            items = re.findall(r"<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?</item>", resp.text, re.DOTALL)

            if items:
                lines = ["🛡️ Son Siber Güvenlik Haberleri:"]
                for i, (title, link) in enumerate(items[:7], 1):
                    title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
                    lines.append(f"  {i}. {title}")
                    lines.append(f"     🔗 {link}")
                return "\n".join(lines)

        return "⚠️ Güvenlik haberleri şu anda alınamıyor."
    except Exception as e:
        return f"❌ Haber çekme hatası: {e}"


def _scan_network() -> str:
    """Ağdaki cihazları tara (ARP tablosu)."""
    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return "❌ ARP taraması başarısız."

        lines_raw = result.stdout.strip().split("\n")
        devices = []

        for line in lines_raw:
            # IP ve MAC adreslerini parse et
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)\s+([\da-f-]{17})\s+(\w+)", line, re.IGNORECASE)
            if match:
                ip = match.group(1)
                mac = match.group(2)
                dtype = match.group(3)
                if ip != "255.255.255.255" and not ip.startswith("224."):
                    # MAC vendor'ı belirle (ilk 3 oktet)
                    vendor = _mac_vendor_hint(mac)
                    devices.append({"ip": ip, "mac": mac, "type": dtype, "vendor": vendor})

        if not devices:
            return "✅ Ağda başka cihaz bulunamadı."

        lines = [f"🌐 Ağ Cihazları ({len(devices)} cihaz):"]
        for d in devices:
            vendor_str = f" ({d['vendor']})" if d['vendor'] else ""
            lines.append(f"  📡 {d['ip']:16s} | {d['mac']}{vendor_str}")

        return "\n".join(lines)
    except Exception as e:
        return f"❌ Ağ tarama hatası: {e}"


def _mac_vendor_hint(mac: str) -> str:
    """MAC adresinden üretici tahmini (yaygın olanlar)."""
    prefix = mac[:8].upper().replace("-", ":")
    vendors = {
        "00:50:56": "VMware", "00:0C:29": "VMware", "00:1C:42": "Parallels",
        "DC:A6:32": "Raspberry Pi", "B8:27:EB": "Raspberry Pi",
        "3C:22:FB": "Apple", "A4:83:E7": "Apple", "F0:18:98": "Apple",
        "88:36:6C": "Apple", "AC:DE:48": "Apple",
        "30:B5:C2": "TP-Link", "EC:08:6B": "TP-Link",
        "FC:F5:28": "ZyXEL", "00:1D:7E": "Cisco",
        "00:1A:2B": "Ayecom", "00:E0:4C": "Realtek",
        "AC:84:C6": "TP-Link", "70:4D:7B": "Asus",
        "00:15:5D": "Hyper-V",
    }
    return vendors.get(prefix, "")


def _rogue_process_hunter() -> str:
    """Arka planda çalışan şüpheli işlemleri tespit eder."""
    if not _PSUTIL:
        return "❌ psutil kütüphanesi gerekli."

    suspicious = []
    suspicious_paths = [r"\\Temp\\", r"\\AppData\\Local\\Temp\\", r"\\Downloads\\"]
    suspicious_names = ["svch0st.exe", "winlog0n.exe", "exploror.exe", "taskmgr.exe.exe"]

    try:
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                name = (proc.info['name'] or "").lower()
                exe = (proc.info['exe'] or "")

                is_sus = False
                reason = ""

                if name in suspicious_names:
                    is_sus = True
                    reason = "Sahte İsim"
                elif any(p.lower() in exe.lower() for p in suspicious_paths):
                    is_sus = True
                    reason = "Şüpheli Dizin"

                if is_sus:
                    suspicious.append({"pid": proc.info['pid'], "name": proc.info['name'], "exe": exe, "reason": reason})
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if not suspicious:
            return "✅ Sistem temiz: Şüpheli çalışan işlem bulunamadı."

        lines = [f"⚠️ {len(suspicious)} Şüpheli İşlem Tespit Edildi!"]
        for s in suspicious:
            lines.append(f"  🔴 [PID: {s['pid']}] {s['name']} ({s['reason']})\n     📍 {s['exe']}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ İşlem taraması başarısız: {e}"


def _persistence_detector() -> str:
    """Kayıt defterindeki (Registry) başlangıç anahtarlarını kontrol eder."""
    keys_to_check = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run")
    ]

    suspicious = []
    lines = ["🔍 Başlangıç (Persistence) Taraması:"]

    for hkey, subkey in keys_to_check:
        try:
            key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
            count = winreg.QueryInfoKey(key)[1]
            for i in range(count):
                name, value, _ = winreg.EnumValue(key, i)
                val_lower = str(value).lower()

                # Basit anomali tespiti
                is_sus = False
                if "temp" in val_lower or "appdata\\local\\temp" in val_lower or value.startswith("http") or "powershell -enc" in val_lower:
                    is_sus = True

                icon = "🔴" if is_sus else "🟢"
                hkey_str = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                lines.append(f"  {icon} [{hkey_str}] {name}: {value}")

                if is_sus:
                    suspicious.append(value)
            winreg.CloseKey(key)
        except Exception:
            lines.append(f"  ⚠️ Erişim reddedildi veya bulunamadı: {subkey}")

    if suspicious:
        lines.append(f"\n⚠️ {len(suspicious)} adet potansiyel tehlikeli başlangıç öğesi tespit edildi!")
    else:
        lines.append("\n✅ Başlangıç öğeleri temiz görünüyor.")

    return "\n".join(lines)


def _network_anomaly() -> str:
    """Dışa açık şüpheli ağ bağlantılarını tespit eder."""
    if not _PSUTIL:
        return "❌ psutil kütüphanesi gerekli."

    try:
        conns = psutil.net_connections(kind='inet')
        established = [c for c in conns if c.status == 'ESTABLISHED' and c.raddr]

        external_conns = []
        for c in established:
            ip = c.raddr.ip
            port = c.raddr.port
            # Yerel ağ dışındaki IP'leri filtrele
            if not ip.startswith(("192.168.", "10.", "172.16.", "127.")):
                external_conns.append((ip, port, c.pid))

        if not external_conns:
            return "✅ Dışarıya şüpheli/aktif bir bağlantı bulunamadı."

        lines = [f"🌐 {len(external_conns)} Aktif Dış Bağlantı Tespit Edildi:"]

        # Sadece ilk 10'unu gösterelim çok kalabalık olmasın
        for ip, port, pid in external_conns[:10]:
            pname = "?"
            try:
                if pid:
                    pname = psutil.Process(pid).name()
            except Exception:
                pass
            lines.append(f"  📡 {ip}:{port} (PID: {pid} - {pname})")

        if len(external_conns) > 10:
            lines.append(f"  ...ve {len(external_conns) - 10} bağlantı daha.")

        return "\n".join(lines)
    except Exception as e:
        return f"❌ Ağ taraması başarısız: {e}"


def _open_directory(filepath: str) -> str:
    """Verilen dosyanın bulunduğu dizini açar ve dosyayı seçer."""
    if not os.path.exists(filepath):
        return f"❌ Dosya bulunamadı: {filepath}"
    try:
        # Popen is non-blocking so JARVIS won't freeze
        subprocess.Popen(f'explorer /select,"{filepath}"')
        return f"📂 Dizin açıldı ve dosya seçildi: {filepath}"
    except Exception as e:
        return f"❌ Dizin açılamadı: {e}"

def _panic_lockdown() -> str:
    try:
        subprocess.run(["powershell", "-Command", "Disable-NetAdapter -Name * -Confirm:$false"], capture_output=True)
        _add_undo("panic_lockdown", {}, "Ağ İzolasyon Modu")
        return "🚨 PANİK MODU AKTİF! Tüm ağ bağlantıları donanımsal olarak kesildi."
    except Exception as e:
        return f"❌ Panik modu hatası (Yönetici izni gerekebilir): {e}"

def _block_ip(ip: str) -> str:
    if not ip: return "❌ Engellenecek IP belirtilmedi."
    rule_name = f"JARVIS_Block_{ip.replace('.', '_')}"
    cmd = f"New-NetFirewallRule -DisplayName '{rule_name}' -Direction Inbound -Action Block -RemoteAddress {ip}; New-NetFirewallRule -DisplayName '{rule_name}_Out' -Direction Outbound -Action Block -RemoteAddress {ip}"
    try:
        subprocess.run(["powershell", "-Command", cmd], capture_output=True)
        _add_undo("block_ip", {"rule_name": rule_name}, f"IP Engellendi: {ip}")
        return f"🛡️ IP adresi başarıyla engellendi: {ip}"
    except Exception as e:
        return f"❌ IP engelleme hatası (Yönetici izni gerekebilir): {e}"

def _quarantine_process(pid: int) -> str:
    try:
        pid = int(pid)
        proc = psutil.Process(pid)
        exe_path = proc.exe()
        name = proc.name()

        proc.kill()

        import shutil
        import tempfile
        quar_dir = os.path.join(tempfile.gettempdir(), "JARVIS_Quarantine")
        os.makedirs(quar_dir, exist_ok=True)

        quar_path = os.path.join(quar_dir, name + ".quarantined")
        shutil.move(exe_path, quar_path)

        _add_undo("quarantine", {"orig_path": exe_path, "quar_path": quar_path}, f"Karantina: {name}")
        return f"☣️ İŞLEM YOK EDİLDİ: {name} (PID: {pid}) sonlandırıldı ve karantinaya alındı."
    except Exception as e:
        return f"❌ Karantina hatası: {e}"

def _defender_scan(path: str = "") -> str:
    try:
        if path:
            cmd = f"Start-MpScan -ScanType CustomScan -ScanPath '{path}'"
            msg = f"🔍 {path} için özel tarama başlatıldı."
        else:
            cmd = "Start-MpScan -ScanType QuickScan"
            msg = "🔍 Windows Defender Hızlı Tarama tetiklendi."

        subprocess.Popen(["powershell", "-Command", cmd])
        return msg
    except Exception as e:
        return f"❌ Defender tetikleme hatası: {e}"

def _hosts_defender() -> str:
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    try:
        with open(hosts_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.split("\n")
        suspicious = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if "localhost" not in line and "127.0.0.1" not in line and "::1" not in line:
                    suspicious.append(line)

        if suspicious:
            bak_path = hosts_path + ".bak"
            import shutil
            shutil.copy(hosts_path, bak_path)

            default_hosts = "# JARVIS Restored Hosts File\n127.0.0.1 localhost\n::1 localhost\n"
            try:
                with open(hosts_path, "w", encoding="utf-8") as f:
                    f.write(default_hosts)
                _add_undo("hosts_restore", {"orig_path": hosts_path, "bak_path": bak_path}, "Hosts Dosyası Temizliği")
                return f"⚠️ Hosts dosyasında {len(suspicious)} yabancı kayıt bulundu ve temizlendi! Geri almak istersen söyle."
            except PermissionError:
                return "⚠️ Hosts dosyasında şüpheli kayıtlar var ancak temizlemek için Yönetici (Admin) izni gerekiyor:\n" + "\n".join(suspicious)

        return "✅ Hosts dosyası temiz."
    except Exception as e:
        return f"❌ Hosts tarama hatası: {e}"

def _hidden_admin_hunter() -> str:
    try:
        user_res = subprocess.run(["net", "user"], capture_output=True, text=True)
        users = []
        for line in user_res.stdout.split("\n"):
            if "Kullanıcı hesapları" in line or "----" in line or "komut başarıyla" in line.lower() or not line.strip():
                continue
            parts = line.split()
            users.extend(parts)

        share_res = subprocess.run(["powershell", "-Command", "Get-SmbShare | Select-Object Name | ConvertTo-Json"], capture_output=True, text=True)
        shares = []
        if share_res.stdout.strip():
            share_data = json.loads(share_res.stdout)
            if isinstance(share_data, dict):
                share_data = [share_data]
            shares = [s.get("Name") for s in share_data if s.get("Name")]

        lines = ["🕵️ Gizli Kullanıcı ve Paylaşım Taraması:"]
        lines.append(f"  👤 Kullanıcılar ({len(users)}): {', '.join(users)}")

        suspicious_shares = [s for s in shares if s and s.endswith("$") and s not in ("IPC$", "ADMIN$", "C$")]
        if suspicious_shares:
            lines.append(f"  ⚠️ Şüpheli Paylaşımlar Bulundu: {', '.join(suspicious_shares)}")
        else:
            lines.append("  ✅ Ağ paylaşımları güvenli.")

        return "\n".join(lines)
    except Exception as e:
        return f"❌ Yönetici/Paylaşım tarama hatası: {e}"

def _bruteforce_detect() -> str:
    try:
        cmd = "Get-EventLog -LogName Security -InstanceId 4625 -Newest 10 -ErrorAction SilentlyContinue | Select-Object TimeGenerated, Message | ConvertTo-Json"
        res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True)
        if not res.stdout.strip():
            return "✅ Son zamanlarda başarısız giriş denemesi (Brute-Force) saptanmadı."

        data = json.loads(res.stdout)
        if isinstance(data, dict): data = [data]
        return f"⚠️ Dikkat! Son zamanlarda {len(data)} başarısız Windows giriş (Oturum Açma) denemesi tespit edildi."
    except Exception as e:
        return f"❌ EventLog okuma hatası (Yönetici izni gerekebilir): {e}"

def _privacy_guard() -> str:
    try:
        hkey = winreg.HKEY_CURRENT_USER
        subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"

        key = winreg.OpenKey(hkey, subkey, 0, winreg.KEY_READ)
        count = winreg.QueryInfoKey(key)[0]

        active_apps = []
        for i in range(count):
            app_name = winreg.EnumKey(key, i)
            app_key = winreg.OpenKey(key, app_name)
            try:
                last_used, _ = winreg.QueryValueEx(app_key, "LastUsedTimeStop")
                if last_used == 0:
                    active_apps.append(app_name)
            except Exception:
                pass
            winreg.CloseKey(app_key)
        winreg.CloseKey(key)

        if active_apps:
            return "⚠️ DİKKAT: Şu anda kameranı kullanan uygulamalar var:\n  " + "\n  ".join(active_apps)
        return "✅ Kameranı gizlice kullanan bir Windows uygulaması tespit edilmedi."
    except Exception as e:
        return f"❌ Gizlilik tarama hatası: {e}"


def cyber_tools_action(parameters: dict = None, player=None) -> str:
    global _PENDING_ACTION
    params = parameters or {}
    action = params.get("action", "status")

    if player:
        player.write_log(f"[CyberTools] Komut: {action}")

    if action == "audit_mode_start":
        if player:
            player.set_mood("focused", rgb=(255, 30, 30), intensity=1.0, pulse_speed=3.0)
        return "🚨 KIRMIZI ALARM: Görsel Audit modu aktif! Çekirdek kırmızı savunma moduna geçirildi."

    elif action == "audit_mode_stop":
        if player:
            player.set_mood("neutral", rgb=(0, 220, 255), intensity=0.5, pulse_speed=1.0)
        return "✅ Güvenlik taraması bitti. Sistem normale dönüyor."

    elif action == "rogue_process_hunter":
        return _rogue_process_hunter()

    elif action == "persistence_detector":
        return _persistence_detector()

    elif action == "network_anomaly":
        return _network_anomaly()

    elif action == "open_directory":
        filepath = params.get("filepath", "")
        if not filepath:
            return "❌ Açılacak dosya dizini (filepath) belirtilmedi."
        return _open_directory(filepath)

    elif action == "undo":
        return _undo_last_action()

    elif action == "panic_lockdown":
        _PENDING_ACTION = {"type": "panic_lockdown"}
        if player: player.set_mood("focused", rgb=(255, 100, 0), intensity=1.0, pulse_speed=3.0)
        return "⚠️ DİKKAT: Panik modunu (Ağ İzolasyonu) başlatmak üzeresiniz. Tüm internet bağlantısı kesilecektir. Onaylıyor musunuz? (Lütfen 'onaylıyorum' veya 'confirm_action' diyin)"

    elif action == "block_ip":
        ip = params.get("ip", "")
        return _block_ip(ip)

    elif action == "quarantine_process":
        pid = params.get("pid", 0)
        _PENDING_ACTION = {"type": "quarantine_process", "pid": pid}
        if player: player.set_mood("focused", rgb=(255, 100, 0), intensity=1.0, pulse_speed=3.0)
        return f"⚠️ DİKKAT: PID {pid} nolu işlemi sonlandırıp karantinaya almak üzeresiniz. Bu işlem programın çökmesine neden olabilir. Onaylıyor musunuz? (Lütfen 'onaylıyorum' diyin)"

    elif action == "confirm_action":
        if not _PENDING_ACTION:
            return "❌ Onaylanacak bekleyen bir işlem yok."

        atype = _PENDING_ACTION["type"]
        data = _PENDING_ACTION
        _PENDING_ACTION = None

        if player: player.set_mood("focused", rgb=(255, 30, 30), intensity=1.0)
        if atype == "panic_lockdown":
            return _panic_lockdown()
        elif atype == "quarantine_process":
            return _quarantine_process(data.get("pid", 0))

    elif action == "cancel_action":
        _PENDING_ACTION = None
        if player: player.set_mood("neutral", rgb=(0, 220, 255), intensity=0.5)
        return "✅ İşlem iptal edildi."

    elif action == "defender_scan":
        path = params.get("path", "")
        return _defender_scan(path)

    elif action == "hosts_defender":
        return _hosts_defender()

    elif action == "hidden_admin_hunter":
        return _hidden_admin_hunter()

    elif action == "bruteforce_detect":
        return _bruteforce_detect()

    elif action == "privacy_guard":
        return _privacy_guard()

    elif action == "cve_lookup":
        cve_id = params.get("cve_id", "") or params.get("query", "")
        if not cve_id:
            return "❌ CVE ID belirtilmedi. Örnek: CVE-2024-3094"
        return _cve_lookup(cve_id)

    elif action == "vulnerability_calendar" or action == "vuln_calendar":
        return _vulnerability_calendar()

    elif action == "security_news" or action == "news":
        return _security_news()

    elif action == "network_scan" or action == "scan_network":
        return _scan_network()

    elif action == "port_scan":
        target = params.get("target", "127.0.0.1")
        common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
                       993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443]

        lines = [f"🔍 Port Taraması: {target}"]
        open_ports = []

        for port in common_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((target, port))
                if result == 0:
                    service = {
                        21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
                        80: "HTTP", 110: "POP3", 135: "RPC", 139: "NetBIOS", 143: "IMAP",
                        443: "HTTPS", 445: "SMB", 993: "IMAPS", 995: "POP3S",
                        1433: "MSSQL", 1521: "Oracle", 3306: "MySQL", 3389: "RDP",
                        5432: "PostgreSQL", 5900: "VNC", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
                    }.get(port, "?")
                    open_ports.append(f"  🟢 Port {port:5d} — {service}")
                sock.close()
            except Exception:
                pass

        if open_ports:
            lines.append(f"  {len(open_ports)} açık port bulundu:")
            lines.extend(open_ports)
        else:
            lines.append("  ✅ Taranan portlarda açık port bulunamadı.")

        return "\n".join(lines)

    elif action == "dns_check":
        domain = params.get("domain", "google.com")
        try:
            ip = socket.gethostbyname(domain)
            lines = [
                f"🌐 DNS Sorgusu: {domain}",
                f"  📍 IP: {ip}",
            ]
            # Reverse DNS
            try:
                hostname = socket.gethostbyaddr(ip)
                lines.append(f"  🔄 Reverse DNS: {hostname[0]}")
            except Exception:
                pass
            return "\n".join(lines)
        except socket.gaierror:
            return f"❌ DNS çözümlenemedi: {domain}"

    elif action == "firewall_status":
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-NetFirewallProfile | Select-Object Name, Enabled | ConvertTo-Json"],
                capture_output=True, text=True, timeout=10
            )
            profiles = json.loads(result.stdout) if result.stdout.strip() else []
            if isinstance(profiles, dict):
                profiles = [profiles]

            lines = ["🔥 Windows Firewall Durumu:"]
            for p in profiles:
                status = "✅ Aktif" if p.get("Enabled") else "❌ Kapalı"
                lines.append(f"  {p.get('Name', '?')}: {status}")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Firewall durumu alınamadı: {e}"

    elif action == "wifi_info":
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                lines = ["📶 WiFi Bilgileri:"]
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if any(k in line for k in ["SSID", "Signal", "Auth", "Cipher", "Band", "Channel", "Speed"]):
                        lines.append(f"  {line}")
                return "\n".join(lines) if len(lines) > 1 else "❌ WiFi bilgisi bulunamadı."
            return "❌ WiFi bilgisi alınamadı."
        except Exception as e:
            return f"❌ WiFi sorgusu hatası: {e}"

    elif action == "status":
        lines = ["🛡️ Siber Güvenlik Araçları:"]
        lines.append("  Kullanılabilir komutlar:")
        lines.append("  • cve_lookup    — CVE veritabanı sorgusu")
        lines.append("  • vuln_calendar — Zafiyet/yama takvimi")
        lines.append("  • security_news — Güncel güvenlik haberleri")
        lines.append("  • network_scan  — Ağ cihazları tarama")
        lines.append("  • port_scan     — Port tarama")
        lines.append("  • dns_check     — DNS sorgusu")
        lines.append("  • firewall_status — Firewall durumu")
        lines.append("  • wifi_info     — WiFi güvenlik bilgisi")
        lines.append("  • rogue_process_hunter — Şüpheli işlem tarayıcı")
        lines.append("  • persistence_detector — Registry başlangıç tarayıcı")
        lines.append("  • network_anomaly      — Canlı dış bağlantı tarayıcı")
        lines.append("  • open_directory       — Şüpheli dosya dizinini açar")
        lines.append("  • audit_mode_start/stop — Arayüzü Kırmızı Alarm moduna alır")
        lines.append("  • panic_lockdown       — Ağ izolasyonunu başlatır")
        lines.append("  • block_ip             — IP engeller")
        lines.append("  • quarantine_process   — İşlemi sonlandırır ve karantinaya alır")
        lines.append("  • defender_scan        — Defender taraması tetikler")
        lines.append("  • hosts_defender       — Hosts dosyasını denetler")
        lines.append("  • hidden_admin_hunter  — Gizli kullanıcı/paylaşım tarar")
        lines.append("  • bruteforce_detect    — Kaba kuvvet saldırılarını tarar")
        lines.append("  • privacy_guard        — Kamera kullanımını tarar")
        lines.append("  • undo                 — Son aktif güvenlik işlemini geri alır")
        lines.append("  • confirm_action       — Bekleyen kritik güvenlik işlemini onaylar")
        lines.append("  • cancel_action        — Bekleyen işlemi iptal eder")
        return "\n".join(lines)

    return "Geçersiz komut. Kullanılabilir güvenlik komutları için 'status' parametresiyle çalıştırın."
