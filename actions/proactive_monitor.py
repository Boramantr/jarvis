"""
Proactive Monitor — Arka planda çalışan sistem izleme ve bildirim sistemi.
CPU, RAM, batarya, çalışma süresi, hava durumu gibi metrikleri izler.
"""
import threading
import time
from datetime import datetime

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False


class ProactiveMonitor:
    """Arka planda çalışan proaktif izleme sistemi."""

    def __init__(self, speak_callback=None, ui_callback=None):
        self.speak = speak_callback  # JARVIS'e konuşturtmak için
        self.ui = ui_callback        # UI'a bildirim göndermek için
        self._running = False
        self._thread = None
        self._last_alerts = {}       # Son alert zamanları (flood koruma)
        self._boot_greeted = False
        self._session_start = datetime.now()

        # Eşik değerleri
        self.thresholds = {
            "cpu_high": 90,           # CPU %90 üzeri uyar
            "ram_high": 85,           # RAM %85 üzeri uyar
            "battery_low": 15,        # Batarya %15 altı uyar
            "battery_critical": 5,    # Batarya %5 altı acil uyar
            "work_break_mins": 90,    # 90 dakikada bir mola öner
            "temp_high": 85,          # CPU sıcaklık uyarısı
        }

        # Kontrol aralıkları (saniye)
        self.intervals = {
            "system": 30,
            "battery": 300,
            "work_break": 900,    # 15 dakikada kontrol
            "weather": 21600,     # 6 saatte bir
        }

    def _can_alert(self, alert_key: str, cooldown_seconds: int = 300) -> bool:
        """Aynı uyarıyı tekrar tekrar vermemek için."""
        now = datetime.now()
        last = self._last_alerts.get(alert_key)
        if last and (now - last).total_seconds() < cooldown_seconds:
            return False
        self._last_alerts[alert_key] = now
        return True

    def _notify(self, message: str, priority: str = "normal"):
        """Bildirim gönder."""
        if self.speak:
            try:
                self.speak(message)
            except Exception:
                pass
        if self.ui:
            try:
                self.ui.write_log(f"[Proactive] {message}")
            except Exception:
                pass

    def _check_system(self):
        """CPU ve RAM kontrolü."""
        if not _PSUTIL:
            return

        try:
            # Non-blocking: ilk çağrı 0.0 döner; sonraki çağrılarda son aralığın ortalaması
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()

            if cpu > self.thresholds["cpu_high"] and self._can_alert("cpu_high"):
                self._notify(
                    f"Efendim, CPU kullanımı çok yüksek: %{cpu:.0f}. "
                    f"Ağır processleri kapatmamı ister misiniz?",
                    priority="high"
                )

            if ram.percent > self.thresholds["ram_high"] and self._can_alert("ram_high"):
                self._notify(
                    f"RAM kullanımı yüksek: %{ram.percent:.0f}. "
                    f"Gereksiz uygulamaları kapatmanızı öneririm.",
                    priority="high"
                )
        except Exception:
            pass

    def _check_battery(self):
        """Batarya kontrolü."""
        if not _PSUTIL:
            return

        try:
            battery = psutil.sensors_battery()
            if not battery:
                return

            if not battery.power_plugged:
                if battery.percent <= self.thresholds["battery_critical"] and self._can_alert("battery_critical", 120):
                    self._notify(
                        f"⚠️ KRİTİK: Batarya %{battery.percent}! Hemen şarj edin efendim!",
                        priority="critical"
                    )
                elif battery.percent <= self.thresholds["battery_low"] and self._can_alert("battery_low"):
                    self._notify(
                        f"Batarya %{battery.percent} kaldı. Şarj etmenizi öneririm.",
                        priority="high"
                    )
        except Exception:
            pass

    def _check_work_break(self):
        """Çalışma süresi ve mola kontrolü."""
        elapsed = (datetime.now() - self._session_start).total_seconds() / 60

        if elapsed >= self.thresholds["work_break_mins"] and self._can_alert("work_break", 2700):
            hours = int(elapsed // 60)
            mins = int(elapsed % 60)
            self._notify(
                f"{hours} saat {mins} dakikadır çalışıyorsunuz. "
                f"Kısa bir mola vermenizi öneririm efendim. Gözlerinizi dinlendirin.",
                priority="normal"
            )

    def _morning_briefing(self):
        """Sabah selamlaması (bir kez)."""
        if self._boot_greeted:
            return

        hour = datetime.now().hour
        if 6 <= hour <= 11:
            self._boot_greeted = True
            if self._can_alert("morning", 43200):
                self._notify(
                    "Günaydın efendim! Brifing ister misiniz? 'Brifingimi ver' demeniz yeterli.",
                    priority="low"
                )

    def _monitor_loop(self):
        """Ana izleme döngüsü."""
        counters = {key: 0 for key in self.intervals}

        while self._running:
            try:
                # Sistem kontrolü
                if counters["system"] >= self.intervals["system"]:
                    self._check_system()
                    counters["system"] = 0

                # Batarya kontrolü
                if counters["battery"] >= self.intervals["battery"]:
                    self._check_battery()
                    counters["battery"] = 0

                # Mola kontrolü
                if counters["work_break"] >= self.intervals["work_break"]:
                    self._check_work_break()
                    counters["work_break"] = 0

                # Sabah selamı
                self._morning_briefing()

                # 10 saniyede bir döngü (RAM/CPU tasarrufu)
                time.sleep(10)
                for key in counters:
                    counters[key] += 10

            except Exception:
                time.sleep(15)

    def start(self):
        """Monitor'ü başlat."""
        if self._running:
            return
        self._running = True
        self._session_start = datetime.now()
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ProactiveMonitor"
        )
        self._thread.start()

    def stop(self):
        """Monitor'ü durdur."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def get_status(self) -> str:
        """Monitor durumunu döndür."""
        uptime = datetime.now() - self._session_start
        hours = int(uptime.total_seconds() // 3600)
        mins = int((uptime.total_seconds() % 3600) // 60)
        alerts = len(self._last_alerts)
        return (
            f"📡 Proaktif Monitor: {'Aktif ✅' if self._running else 'Devre dışı ❌'}\n"
            f"  Çalışma süresi: {hours}s {mins}dk\n"
            f"  Gönderilen uyarı: {alerts}"
        )


def proactive_monitor_action(parameters: dict = None, player=None) -> str:
    """Tool olarak çağrılabilir monitor kontrol action'ı."""
    params = parameters or {}
    action = params.get("action", "status")

    if action == "status":
        return "Proaktif monitor durumu sorgulanıyor... (Monitor main.py'dan başlatılır)"
    elif action == "thresholds":
        return (
            "⚙️ Mevcut Eşikler:\n"
            "  CPU yüksek: %90\n"
            "  RAM yüksek: %85\n"
            "  Batarya düşük: %15\n"
            "  Batarya kritik: %5\n"
            "  Çalışma molası: 90 dk"
        )
    return "Kullanılabilir: status, thresholds"
