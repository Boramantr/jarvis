"""
JARVIS HUD
Minimal, Iron Man-inspired overlay. Subtle arc reactor aesthetic.
Auto-hides during gaming/video. Eye-friendly dark design.
"""
import math
import random
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

try:
    import pygetwindow as gw
    _GW = True
except ImportError:
    _GW = False

# ─── Renk Paleti: Iron Man J.A.R.V.I.S. ───
CYAN       = QColor(0, 220, 255, 180)      # J.A.R.V.I.S. Classic Cyan
CYAN_DIM   = QColor(0, 160, 200, 90)       # Kısık mavi
GOLD       = QColor(255, 180, 30, 180)     # Iron Man Gold
GOLD_DIM   = QColor(200, 140, 20, 90)      # Kısık altın
GOLD_GLOW  = QColor(255, 180, 30, 50)      # Altın glow
DARK_BG    = QColor(20, 35, 55, 180)       # Daha parlak arka plan
DARK_PANEL = QColor(25, 40, 65, 200)       # Panel arka planı
AMBER      = QColor(255, 120, 0, 160)      # Uyarı/accent
TEXT_DIM   = QColor(160, 180, 200, 220)    # Kısık metin (daha parlak)
TEXT_LIGHT = QColor(220, 235, 255, 255)    # Normal metin
BORDER     = QColor(100, 180, 255, 120)    # Gök mavisi kenar
RED_ALERT  = QColor(255, 60, 60, 180)      # Kritik uyarı
MAGENTA    = QColor(180, 50, 255, 180)     # Thinking


# Oyun/medya processlerini algıla (auto-hide)
GAMING_KEYWORDS = [
    "valorant", "cs2", "csgo", "league", "fortnite", "minecraft",
    "pubg", "gta", "apex", "overwatch", "roblox", "steam",
    "fifa", "rocket league", "rainbow", "tarkov", "elden",
]
MEDIA_KEYWORDS = [
    "netflix", "disney+", "hbo", "prime video", "vlc media",
    "mpv", "mpc-hc", "plex",
]


class JarvisUI(QMainWindow):
    state_signal = pyqtSignal(str)
    log_signal   = pyqtSignal(str)
    audio_signal = pyqtSignal(float)
    mute_signal  = pyqtSignal(bool)
    mood_signal  = pyqtSignal(str)

    # ── Modlar ──
    MODE_COMPACT  = "compact"     # Sadece arc reactor core (60x60)
    MODE_EXPANDED = "expanded"    # Core + bilgi paneli (280x140)

    def __init__(self, image_path="face.png"):
        self.app = QApplication.instance()
        if not self.app:
            self.app = QApplication(sys.argv)

        super().__init__()
        self.image_path = image_path
        self.muted = False
        self.on_text_command = None

        # ── Pencere Ayarları ──
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("QMainWindow { background: transparent; border: none; }")

        # ── Boyut & Konum (sağ üst köşe) ──
        screen = QApplication.primaryScreen().size()
        self._mode = self.MODE_COMPACT
        self._compact_size = (64, 64)
        self._expanded_size = (280, 120)
        self._margin = 16

        # Sağ üst köşe
        self._pos_x = screen.width() - self._compact_size[0] - self._margin
        self._pos_y = self._margin
        self.setGeometry(self._pos_x, self._pos_y, *self._compact_size)

        # ── Fotoğraf ──
        self.face_pixmap = QPixmap(self.image_path) if image_path else QPixmap()

        # ── Durum Değişkenleri ──
        self.audio_level = 0.0
        self._target_audio = 0.0
        self.time_counter = 0
        self._state = "LISTENING"       # LISTENING, SPEAKING, THINKING
        self._auto_hidden = False       # Oyun/medya algılandığında True
        self._hover = False
        self._cpu_percent = 0.0
        self._ram_percent = 0.0
        self._last_log = ""

        # ── Vital Signs (Yaşam Belirtileri) ──
        self._mood = "neutral"
        self._mood_rgb = (0, 220, 255)     # Varsayılan mood rengi (Cyan)
        self._mood_intensity = 0.5
        self._mood_pulse_speed = 1.0
        self._breath_phase = 0.0           # Nefes alma fazı (0-2π)
        self._bond_level = 0               # Bağ seviyesi (0-100)

        # ── Yıldızlar (Evrensel Renkler) ──
        self.stars = []
        star_colors = [
            (255, 255, 255),  # Beyaz
            (150, 200, 255),  # Açık Mavi
            (255, 220, 150),  # Açık Altın
            (200, 150, 255),  # Açık Mor
            (0, 220, 255)     # Cyan
        ]
        import random
        for _ in range(60):
            c = random.choice(star_colors)
            self.stars.append({
                "x": random.uniform(0, 280),
                "y": random.uniform(0, 120),
                "size": random.uniform(0.5, 2.5),
                "r": c[0], "g": c[1], "b": c[2],
                "alpha": random.randint(50, 220),
                "vx": random.uniform(-0.15, 0.15),
                "vy": random.uniform(-0.15, 0.15)
            })

        # ── Animasyon Başlangıç Seviyesi ──
        self._boot_progress = 0.0
        self._core_heat = 0.0
        self._glitch_intensity = 0.0
        self._ripple_pos = None
        self._ripple_radius = 0.0
        self._ripple_alpha = 0
        self._comets = []
        for _ in range(2):
            self._comets.append({"x": random.uniform(0, 280), "y": random.uniform(0, 120), "vx": random.uniform(4.0, 8.0), "alpha": random.randint(100, 200)})

        # ── Timer: 30fps animasyon ──
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._tick)
        self.anim_timer.start(33)

        # ── Timer: Sistem metrikleri (5 saniyede bir) ──
        self._sys_timer = QTimer()
        self._sys_timer.timeout.connect(self._update_sys_metrics)
        self._sys_timer.start(5000)

        # ── Timer: Auto-hide kontrolü (10 saniyede bir) ──
        self._hide_timer = QTimer()
        self._hide_timer.timeout.connect(self._check_auto_hide)
        self._hide_timer.start(10000)

        # ── Sinyaller ──
        self.state_signal.connect(self._safe_set_state)
        self.log_signal.connect(self._safe_write_log)
        self.audio_signal.connect(self._set_audio_target)
        self.mute_signal.connect(self.set_mute_state)
        self.mood_signal.connect(self._safe_set_mood)

        self._update_sys_metrics()
        self.show()

    # ═══════════════════════════════════════════
    #  STATE & DATA
    # ═══════════════════════════════════════════

    def _tick(self):
        self.time_counter += 1

        # 1. Boot-up ilerlemesi
        if self._boot_progress < 1.0:
            self._boot_progress = min(1.0, self._boot_progress + 0.015)

        # Kuantum Isınması (Heat)
        if self._state == "THINKING" or self.audio_level > 0.4:
            self._core_heat = min(1.0, self._core_heat + 0.02)
        else:
            self._core_heat = max(0.0, self._core_heat - 0.01)

        # Glitch sönümlemesi
        if self._glitch_intensity > 0:
            self._glitch_intensity = max(0.0, self._glitch_intensity - 0.1)

        # Dalga (Ripple) Genişlemesi
        if self._ripple_radius > 0:
            self._ripple_radius += 10.0
            self._ripple_alpha = max(0, self._ripple_alpha - 15)
            if self._ripple_alpha <= 0:
                self._ripple_radius = 0

        # Yumuşak ses geçişi
        self.audio_level += (self._target_audio - self.audio_level) * 0.25
        # Nefes alma döngüsü
        self._breath_phase += 0.025 * self._mood_pulse_speed
        if self._breath_phase > 2 * math.pi:
            self._breath_phase -= 2 * math.pi

        # Yıldızları güncelle ve Kütleçekim (Mouse Magnetism)
        from PyQt6.QtGui import QCursor
        cursor_pos = self.mapFromGlobal(QCursor.pos())
        cx, cy = cursor_pos.x(), cursor_pos.y()

        for i, s in enumerate(self.stars):
            vx, vy = s["vx"], s["vy"]

            # Kütleçekimi: Eğer Expanded moddaysa ve fare pencere içindeyse
            if self._mode == self.MODE_EXPANDED and 0 <= cx <= self.width() and 0 <= cy <= self.height():
                dx = cx - s["x"]
                dy = cy - s["y"]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 150 and dist > 5:
                    pull = (150 - dist) / 150.0 * 0.25 # Çekim gücü
                    vx += (dx / dist) * pull
                    vy += (dy / dist) * pull

            s["x"] += vx
            s["y"] += vy
            if s["x"] < 0: s["x"] = 280
            elif s["x"] > 280: s["x"] = 0
            if s["y"] < 0: s["y"] = 120
            elif s["y"] > 120: s["y"] = 0

            # Kuantum Çarpışmaları (Particle Colliders)
            for j in range(i + 1, len(self.stars)):
                s2 = self.stars[j]
                cdx, cdy = s["x"] - s2["x"], s["y"] - s2["y"]
                if cdx*cdx + cdy*cdy < 16: # mesafe < 4
                    s["vx"], s["vy"] = -s["vx"], -s["vy"]
                    s2["vx"], s2["vy"] = -s2["vx"], -s2["vy"]
                    s["alpha"] = 255
                    s2["alpha"] = 255

        # Kuyruklu Yıldızları Güncelle
        for c in self._comets:
            c["x"] += c["vx"]
            if c["x"] > 350:
                c["x"] = -50
                c["y"] = random.uniform(0, 120)
                c["vx"] = random.uniform(4.0, 9.0)

        self.update()

    def _set_audio_target(self, level):
        self._target_audio = min(max(level, 0.0), 1.0)

    def set_audio_level(self, level):
        self.audio_signal.emit(level)

    def set_mute_state(self, is_muted):
        self.muted = is_muted
        if is_muted:
            self.hide()
        else:
            self.show()

    def _update_sys_metrics(self):
        if _PSUTIL:
            try:
                self._cpu_percent = psutil.cpu_percent(interval=0)
                self._ram_percent = psutil.virtual_memory().percent
            except Exception:
                pass

    def _safe_set_mood(self, mood_str: str):
        """Mood sinyalini işle — format: 'mood:r:g:b:intensity:pulse_speed'"""
        try:
            parts = mood_str.split(":")
            self._mood = parts[0]
            if len(parts) >= 4:
                self._mood_rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
            if len(parts) >= 5:
                self._mood_intensity = float(parts[4])
            if len(parts) >= 6:
                self._mood_pulse_speed = float(parts[5])
        except Exception:
            pass

    def set_mood(self, mood: str, rgb: tuple = None, intensity: float = 0.5, pulse_speed: float = 1.0):
        """Thread-safe mood güncellemesi."""
        r, g, b = rgb or (0, 220, 255)
        self.mood_signal.emit(f"{mood}:{r}:{g}:{b}:{intensity}:{pulse_speed}")

    def set_bond_level(self, level: int):
        self._bond_level = level

    def _check_auto_hide(self):
        """Oyun veya fullscreen medya açıkken otomatik gizlen."""
        if not _GW:
            return
        try:
            active = gw.getActiveWindow()
            if active and active.title:
                title = active.title.lower()
                # Oyun veya medya algıla
                is_game = any(k in title for k in GAMING_KEYWORDS)
                is_media = any(k in title for k in MEDIA_KEYWORDS)

                # Fullscreen kontrolü
                screen = QApplication.primaryScreen().size()
                is_fullscreen = (
                    active.width >= screen.width() - 10 and
                    active.height >= screen.height() - 40
                )

                should_hide = is_game or (is_media and is_fullscreen)

                if should_hide and not self._auto_hidden:
                    self._auto_hidden = True
                    self.hide()
                elif not should_hide and self._auto_hidden:
                    self._auto_hidden = False
                    if not self.muted:
                        self.show()
        except Exception:
            pass

    # ═══════════════════════════════════════════
    #  MOD GEÇİŞİ
    # ═══════════════════════════════════════════

    def _switch_mode(self, mode):
        if mode == self._mode:
            return
        self._mode = mode
        screen = QApplication.primaryScreen().size()

        if mode == self.MODE_EXPANDED:
            w, h = self._expanded_size
            x = screen.width() - w - self._margin
            self.setGeometry(x, self._pos_y, w, h)
        else:
            w, h = self._compact_size
            x = screen.width() - w - self._margin
            self.setGeometry(x, self._pos_y, w, h)

    # ═══════════════════════════════════════════
    #  MOUSE EVENTLERİ
    # ═══════════════════════════════════════════

    def enterEvent(self, event):
        self._hover = True
        self._switch_mode(self.MODE_EXPANDED)

    def leaveEvent(self, event):
        self._hover = False
        # Konuşurken veya düşünürken açık kalsın
        if self._state not in ("SPEAKING", "THINKING"):
            QTimer.singleShot(800, self._maybe_compact)

    def _maybe_compact(self):
        if not self._hover and self._state not in ("SPEAKING", "THINKING"):
            self._switch_mode(self.MODE_COMPACT)

    def mousePressEvent(self, event):
        # Enerji Kalkanı Dalgalanması (Ripple)
        self._ripple_pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        self._ripple_radius = 1.0
        self._ripple_alpha = 200

        if event.button() == Qt.MouseButton.LeftButton:
            # Toggle mod
            if self._mode == self.MODE_COMPACT:
                self._switch_mode(self.MODE_EXPANDED)
            else:
                self._switch_mode(self.MODE_COMPACT)
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def _show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0f121c;
                color: #b4c8dc;
                border: 1px solid #283c50;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #1a2840;
            }
        """)

        mute_action = QAction("🔇 Mikrofonu Kapat" if not self.muted else "🎤 Mikrofonu Aç", self)
        mute_action.triggered.connect(lambda: self.mute_signal.emit(not self.muted))
        menu.addAction(mute_action)

        quit_action = QAction("❌ JARVIS'i Kapat", self)
        quit_action.triggered.connect(lambda: sys.exit(0))
        menu.addAction(quit_action)

        menu.exec(pos)

    # ═══════════════════════════════════════════
    #  PAINT — ARC REACTOR HUD
    # ═══════════════════════════════════════════

    def paintEvent(self, event):
        if self.muted or self._auto_hidden:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._mode == self.MODE_COMPACT:
            self._draw_compact(painter)
        else:
            self._draw_expanded(painter)

        painter.end()

    def _draw_compact(self, painter: QPainter):
        """Minimal arc reactor core — 64x64 + yaşam belirtileri."""
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        center = QPointF(cx, cy)
        mr, mg, mb = self._mood_rgb

        # ── Nefes alma efekti ve Boot Easing ──
        breath = math.sin(self._breath_phase) * 0.5 + 0.5  # 0—1 arası
        boot_ease = 1.0 - (1.0 - self._boot_progress)**3
        breath_scale = (1.0 + breath * 0.08) * boot_ease
        breath_alpha = int(10 + breath * 20)

        # ── 1. Uzay Yarığı (Kara Delik & Event Horizon) ──
        # Konuşurken (audio_level arttığında) tüm çekirdek büyür
        bh_r = (20.0 + self.audio_level * 10.0) * breath_scale
        bh_bg = QRadialGradient(center, bh_r)
        bh_bg.setColorAt(0.0, QColor(0, 0, 0, 255))
        bh_bg.setColorAt(0.7, QColor(0, 0, 0, 255))
        bh_bg.setColorAt(1.0, QColor(mr, mg, mb, 180)) # Event Horizon Glow
        painter.setBrush(QBrush(bh_bg))
        painter.setPen(QPen(QColor(mr, mg, mb, 220), 1.5))
        painter.drawEllipse(center, bh_r, bh_r)

        # ── 2. Yörünge Halkaları (Dyson Sphere & Atomik Yörüngeler) ──
        painter.save()
        painter.translate(center)

        # İç Yörünge (Hızlı Dönen Noktalı Halka)
        painter.rotate(self.time_counter * 2.5)
        pen_inner = QPen(GOLD, 1.2)
        pen_inner.setDashPattern([2, 4])
        painter.setPen(pen_inner)
        painter.drawEllipse(QPointF(0,0), bh_r * 0.9, bh_r * 0.9)

        # Dış Yörünge (Ters Yönde Dönen, Eğimli Elipsler)
        painter.rotate(-self.time_counter * 3.5)
        orbit_pen = QPen(QColor(mr, mg, mb, 120), 1.0)
        painter.setPen(orbit_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0,0), bh_r * 1.4, bh_r * 0.4)

        painter.rotate(60)
        painter.drawEllipse(QPointF(0,0), bh_r * 1.4, bh_r * 0.4)

        painter.rotate(60)
        painter.drawEllipse(QPointF(0,0), bh_r * 1.4, bh_r * 0.4)

        # ── 3. Yörünge Uyduları (Veri Paketleri) ──
        sat_r = bh_r * 1.5 + self.audio_level * 5.0
        sat_angle = math.radians(self.time_counter * -1.5)
        painter.setBrush(QBrush(GOLD))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(math.cos(sat_angle)*sat_r, math.sin(sat_angle)*sat_r), 2.5, 2.5)

        sat_angle2 = math.radians(self.time_counter * 2.0 + 180)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(math.cos(sat_angle2)*(bh_r*1.1), math.sin(sat_angle2)*(bh_r*1.1)), 1.5, 1.5)
        painter.restore()

        # ── Yumuşak Holografik Ses Dalgası (SPEAKING) ──
        if self._state == "SPEAKING" and self.audio_level > 0.02:
            painter.save()
            painter.translate(center)

            # Altın sarısı, dalgalı dış halka
            wave_path = QPainterPath()
            pts = 60
            base_r = bh_r * 1.15
            for n in range(pts + 1):
                angle = n * (360.0 / pts)
                rad = math.radians(angle)
                ripple = math.sin(rad * 4 + self.time_counter * 0.3) * math.cos(rad * 3 - self.time_counter * 0.2)
                r = base_r + ripple * self.audio_level * 10.0
                px = math.cos(rad) * r
                py = math.sin(rad) * r
                if n == 0:
                    wave_path.moveTo(px, py)
                else:
                    wave_path.lineTo(px, py)
            painter.setPen(QPen(QColor(255, 200, 100, 150), 1.2))
            painter.drawPath(wave_path)

            # Gök mavisi (Cyan), ters dalgalı daha şeffaf gölge halkası
            wave_path2 = QPainterPath()
            for n in range(pts + 1):
                angle = n * (360.0 / pts)
                rad = math.radians(angle)
                ripple2 = math.cos(rad * 5 - self.time_counter * 0.4)
                r = base_r + 2.0 + ripple2 * self.audio_level * 7.0
                px = math.cos(rad) * r
                py = math.sin(rad) * r
                if n == 0:
                    wave_path2.moveTo(px, py)
                else:
                    wave_path2.lineTo(px, py)
            painter.setPen(QPen(QColor(0, 220, 255, 100), 0.8))
            painter.drawPath(wave_path2)

            painter.restore()

        # ── 4. Pulsar Jetleri (Ses Tepkisi) ──
        if self.audio_level > 0.05:
            jet_length = bh_r * 1.5 + self.audio_level * 15.0
            jet_pen = QPen(QColor(mr, mg, mb, int(150 * self.audio_level)), 2.0)
            painter.setPen(jet_pen)
            painter.drawLine(QPointF(cx, cy - bh_r), QPointF(cx, cy - jet_length))
            painter.drawLine(QPointF(cx, cy + bh_r), QPointF(cx, cy + jet_length))

        # ── Hedefleme ve Tarama Kilitleri (THINKING) ──
        if self._state == "THINKING":
            painter.save()
            painter.translate(center)
            painter.rotate(self.time_counter * 3.0)
            target_r = bh_r * 1.6
            bracket_len = 6.0
            painter.setPen(QPen(QColor(180, 50, 255, 200), 1.5))
            for angle in [45, 135, 225, 315]:
                rad = math.radians(angle)
                px = math.cos(rad) * target_r
                py = math.sin(rad) * target_r
                painter.drawLine(QPointF(px, py), QPointF(px - math.cos(rad)*bracket_len, py))
                painter.drawLine(QPointF(px, py), QPointF(px, py - math.sin(rad)*bracket_len))
            painter.restore()

        # ── Düşünme Dalgaları (Thinking waves) ──
        if self._state == "THINKING":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            wave_rad = (self.time_counter * 0.8) % 30.0
            wave_alpha = int(255 * (1.0 - wave_rad / 30.0))
            painter.setPen(QPen(QColor(180, 50, 255, wave_alpha), 1.5))
            painter.drawEllipse(center, bh_r + wave_rad, bh_r + wave_rad)

        # ── Durum göstergesi (LED) ──
        led_x = cx + 18.0
        led_y = cy + 18.0
        if self._state == "SPEAKING":
            led_color = QColor(255, 180, 30, 220) # Gold
        elif self._state == "THINKING":
            pulse = int(120 + 80 * math.sin(self.time_counter * 0.15))
            led_color = QColor(180, 50, 255, pulse) # Magenta
        else:
            led_color = QColor(mr, mg, mb, int(80 + breath * 40))
        painter.setBrush(QBrush(led_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(led_x, led_y), 3.5, 3.5)

    def _draw_expanded(self, painter: QPainter):
        """Genişletilmiş HUD paneli — arc reactor + bilgi + yaşam belirtileri."""
        w, h = self.width(), self.height()
        mr, mg, mb = self._mood_rgb
        breath = math.sin(self._breath_phase) * 0.5 + 0.5
        boot_ease = 1.0 - (1.0 - self._boot_progress)**3
        breath_scale = (1.0 + breath * 0.06) * boot_ease

        # ── Panel arka planı (Koyu Uzay Siyahı) ──
        panel_path = QPainterPath()
        panel_path.addRoundedRect(QRectF(0, 0, w, h), 12, 12)
        painter.setClipPath(panel_path)

        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0.0, QColor(0, 0, 0, 220))
        bg.setColorAt(1.0, QColor(5, 5, 8, 240))
        painter.setBrush(QBrush(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, w, h), 12, 12)

        # ── Çevresel Aura (Ortam Yansıması) ──
        ambient_glow = QLinearGradient(0, 0, w, h)
        ambient_glow.setColorAt(0.0, QColor(0, 255, 120, 25))
        ambient_glow.setColorAt(1.0, QColor(180, 50, 255, 25))
        painter.setBrush(QBrush(ambient_glow))
        painter.drawRoundedRect(QRectF(0, 0, w, h), 12, 12)

        # ── Enerji Kalkanı Dalgalanması (Ripple) ──
        if self._ripple_radius > 0 and self._ripple_pos:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(mr, mg, mb, self._ripple_alpha), 2.0))
            painter.drawEllipse(QPointF(self._ripple_pos), self._ripple_radius, self._ripple_radius)

        # ── Yıldızlar (Evrensel Renkler) ──
        painter.setPen(Qt.PenStyle.NoPen)
        for s in self.stars:
            painter.setBrush(QBrush(QColor(s["r"], s["g"], s["b"], s["alpha"])))
            painter.drawEllipse(QPointF(s["x"], s["y"]), s["size"], s["size"])

        # ── Sinir Ağı Bağlantıları (Neural Bond Network) ──
        bond_thresh = 30.0 + (self._bond_level * 0.5)
        painter.setPen(QPen(QColor(mr, mg, mb, 40), 0.5))
        for i, s1 in enumerate(self.stars):
            for s2 in self.stars[i+1:]:
                dx = s1["x"] - s2["x"]
                dy = s1["y"] - s2["y"]
                if dx*dx + dy*dy < bond_thresh*bond_thresh:
                    painter.drawLine(QPointF(s1["x"], s1["y"]), QPointF(s2["x"], s2["y"]))

        # ── Kuyruklu Yıldızlar (Data Comets) ──
        for c in self._comets:
            painter.setPen(QPen(QColor(255, 255, 255, c["alpha"]), 1.5))
            painter.drawLine(QPointF(c["x"], c["y"]), QPointF(c["x"] - 25, c["y"]))

        # İnce kenar (mood renkli)
        painter.setClipping(False)
        border_pen = QPen(QColor(mr, mg, mb, 90), 1.0)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 12, 12)

        # ── Holografik Tarama Çizgileri (Scanlines) ──
        painter.setPen(QPen(QColor(0, 0, 0, 35), 1.0))
        for y in range(0, int(h), 4):
            offset_y = (y + self.time_counter * 0.5) % h
            painter.drawLine(QPointF(0, offset_y), QPointF(w, offset_y))

        # ── Sol: Mini Arc Reactor (nefes alan) ──
        core_cx, core_cy = 44.0, h / 2.0
        core_center = QPointF(core_cx, core_cy)
        # Konuşurken (audio_level arttığında) tüm çekirdek büyür
        core_r = (22.0 + self.audio_level * 12.0) * breath_scale

        # ── 1. Uzay Yarığı (Kara Delik & Event Horizon) ──
        bh_r = core_r

        # Kromatik Glitch Offsets
        gx = random.uniform(-2.0, 2.0) * self._glitch_intensity
        gy = random.uniform(-2.0, 2.0) * self._glitch_intensity

        # Kuantum Isınması (Quantum Overdrive) Rengi
        heat_r = int(mr + (255 - mr) * self._core_heat)
        heat_g = int(mg + (220 - mg) * self._core_heat)
        heat_b = int(mb + (100 - mb) * self._core_heat)

        bh_bg = QRadialGradient(core_center, bh_r)
        bh_bg.setColorAt(0.0, QColor(0, 0, 0, 255))
        bh_bg.setColorAt(0.7, QColor(0, 0, 0, 255))
        bh_bg.setColorAt(1.0, QColor(heat_r, heat_g, heat_b, 180)) # Isınan Event Horizon

        painter.setBrush(QBrush(bh_bg))
        painter.setPen(QPen(QColor(heat_r, heat_g, heat_b, 220), 1.5))

        painter.save()
        painter.translate(gx, gy) # Glitch offset

        # Şekil Değiştiren Çekirdek (Morphing Topology)
        if self._state == "THINKING":
            poly = QPolygonF()
            for i in range(6):
                angle = math.radians(i * 60 + self.time_counter)
                poly.append(QPointF(core_cx + math.cos(angle)*bh_r, core_cy + math.sin(angle)*bh_r))
            painter.drawPolygon(poly)
        elif self._state == "SPEAKING":
            poly = QPolygonF()
            for i in range(4):
                angle = math.radians(i * 90 + self.time_counter * 2)
                poly.append(QPointF(core_cx + math.cos(angle)*bh_r, core_cy + math.sin(angle)*bh_r))
            painter.drawPolygon(poly)
        else:
            painter.drawEllipse(core_center, bh_r, bh_r)

        painter.restore()

        # Glitch RGB Ayrışması (Kromatik Sapma)
        if self._glitch_intensity > 0.2:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(255, 0, 0, int(150 * self._glitch_intensity)), 1.5))
            painter.drawEllipse(QPointF(core_cx - 4*self._glitch_intensity, core_cy), bh_r, bh_r)
            painter.setPen(QPen(QColor(0, 220, 255, int(150 * self._glitch_intensity)), 1.5))
            painter.drawEllipse(QPointF(core_cx + 4*self._glitch_intensity, core_cy), bh_r, bh_r)

        # ── 2. Yörünge Halkaları (Dyson Sphere & Atomik Yörüngeler) ──
        painter.save()
        painter.translate(core_center)

        # İç Yörünge (Hızlı Dönen Noktalı Halka)
        painter.rotate(self.time_counter * 2.5)
        pen_inner = QPen(GOLD, 1.2)
        pen_inner.setDashPattern([2, 4])
        painter.setPen(pen_inner)
        painter.drawEllipse(QPointF(0,0), bh_r * 0.9, bh_r * 0.9)

        # Dış Yörünge (Ters Yönde Dönen, Eğimli Elipsler)
        painter.rotate(-self.time_counter * 3.5)
        orbit_pen = QPen(QColor(mr, mg, mb, 120), 1.0)
        painter.setPen(orbit_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(0,0), bh_r * 1.4, bh_r * 0.4)

        painter.rotate(60)
        painter.drawEllipse(QPointF(0,0), bh_r * 1.4, bh_r * 0.4)

        painter.rotate(60)
        painter.drawEllipse(QPointF(0,0), bh_r * 1.4, bh_r * 0.4)

        # ── 3. Yörünge Uyduları (Veri Paketleri) ──
        sat_r = bh_r * 1.5 + self.audio_level * 5.0
        sat_angle = math.radians(self.time_counter * -1.5)
        painter.setBrush(QBrush(GOLD))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(math.cos(sat_angle)*sat_r, math.sin(sat_angle)*sat_r), 2.5, 2.5)

        sat_angle2 = math.radians(self.time_counter * 2.0 + 180)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(math.cos(sat_angle2)*(bh_r*1.1), math.sin(sat_angle2)*(bh_r*1.1)), 1.5, 1.5)
        painter.restore()

        # ── Yumuşak Holografik Ses Dalgası (SPEAKING) ──
        if self._state == "SPEAKING" and self.audio_level > 0.02:
            painter.save()
            painter.translate(core_center)

            # Altın sarısı, dalgalı dış halka
            wave_path = QPainterPath()
            pts = 60
            base_r = bh_r * 1.15
            for n in range(pts + 1):
                angle = n * (360.0 / pts)
                rad = math.radians(angle)
                ripple = math.sin(rad * 4 + self.time_counter * 0.3) * math.cos(rad * 3 - self.time_counter * 0.2)
                r = base_r + ripple * self.audio_level * 10.0
                px = math.cos(rad) * r
                py = math.sin(rad) * r
                if n == 0:
                    wave_path.moveTo(px, py)
                else:
                    wave_path.lineTo(px, py)
            painter.setPen(QPen(QColor(255, 200, 100, 150), 1.2))
            painter.drawPath(wave_path)

            # Gök mavisi (Cyan), ters dalgalı daha şeffaf gölge halkası
            wave_path2 = QPainterPath()
            for n in range(pts + 1):
                angle = n * (360.0 / pts)
                rad = math.radians(angle)
                ripple2 = math.cos(rad * 5 - self.time_counter * 0.4)
                r = base_r + 2.0 + ripple2 * self.audio_level * 7.0
                px = math.cos(rad) * r
                py = math.sin(rad) * r
                if n == 0:
                    wave_path2.moveTo(px, py)
                else:
                    wave_path2.lineTo(px, py)
            painter.setPen(QPen(QColor(0, 220, 255, 100), 0.8))
            painter.drawPath(wave_path2)

            painter.restore()

        # ── 4. Pulsar Jetleri (Ses Tepkisi) ──
        if self.audio_level > 0.05:
            jet_length = bh_r * 1.5 + self.audio_level * 15.0
            jet_pen = QPen(QColor(mr, mg, mb, int(150 * self.audio_level)), 2.0)
            painter.setPen(jet_pen)
            painter.drawLine(QPointF(core_cx, core_cy - bh_r), QPointF(core_cx, core_cy - jet_length))
            painter.drawLine(QPointF(core_cx, core_cy + bh_r), QPointF(core_cx, core_cy + jet_length))

        # ── Hedefleme ve Tarama Kilitleri (THINKING) ──
        if self._state == "THINKING":
            painter.save()
            painter.translate(core_center)
            painter.rotate(self.time_counter * 3.0)
            target_r = bh_r * 1.6
            bracket_len = 8.0
            painter.setPen(QPen(QColor(180, 50, 255, 200), 1.5))
            for angle in [45, 135, 225, 315]:
                rad = math.radians(angle)
                px = math.cos(rad) * target_r
                py = math.sin(rad) * target_r
                painter.drawLine(QPointF(px, py), QPointF(px - math.cos(rad)*bracket_len, py))
                painter.drawLine(QPointF(px, py), QPointF(px, py - math.sin(rad)*bracket_len))
            painter.restore()

        # ── Düşünme Dalgaları (Thinking waves) ──
        if self._state == "THINKING":
            painter.setBrush(Qt.BrushStyle.NoBrush)
            wave_rad = (self.time_counter * 0.8) % 30.0
            wave_alpha = int(255 * (1.0 - wave_rad / 30.0))
            painter.setPen(QPen(QColor(180, 50, 255, wave_alpha), 1.5))
            painter.drawEllipse(core_center, bh_r + wave_rad, bh_r + wave_rad)

        # ── Sağ: Bilgi Paneli ──
        text_x = 80.0
        font_title = QFont("Segoe UI", 9, QFont.Weight.Bold)
        font_data = QFont("Consolas", 8)
        font_small = QFont("Segoe UI", 7)

        # Başlık
        painter.setFont(font_title)
        painter.setPen(QPen(GOLD, 1.0))
        painter.drawText(QRectF(text_x, 8, w - text_x - 8, 18), Qt.AlignmentFlag.AlignLeft, "J.A.R.V.I.S")

        # Mood emoji
        mood_emoji = {
            "happy": "😊", "excited": "⚡", "focused": "🎯", "curious": "🔍",
            "neutral": "●", "tired": "😴", "stressed": "⚠", "sad": "💙",
        }.get(self._mood, "●")

        # Durum göstergesi (mood renkli)
        state_text = {
            "LISTENING": f"{mood_emoji} LISTENING",
            "SPEAKING": f"{mood_emoji} SPEAKING",
            "THINKING": "◌ PROCESSING",
        }.get(self._state, f"{mood_emoji} IDLE")

        state_color = {
            "LISTENING": QColor(mr, mg, mb, 180),
            "SPEAKING": QColor(255, 180, 30, 200), # Gold
            "THINKING": MAGENTA,
        }.get(self._state, TEXT_DIM)

        painter.setFont(font_small)
        painter.setPen(QPen(state_color, 1.0))
        painter.drawText(QRectF(text_x, 26, w - text_x - 8, 14), Qt.AlignmentFlag.AlignLeft, state_text)

        # Ayırıcı çizgi
        painter.setPen(QPen(QColor(40, 70, 100, 60), 0.5))
        painter.drawLine(QPointF(text_x, 42), QPointF(w - 12, 42))

        # CPU & RAM
        painter.setFont(font_data)
        painter.setPen(QPen(TEXT_DIM, 1.0))

        cpu_color = RED_ALERT if self._cpu_percent > 85 else AMBER if self._cpu_percent > 60 else TEXT_DIM
        ram_color = RED_ALERT if self._ram_percent > 85 else AMBER if self._ram_percent > 60 else TEXT_DIM

        # CPU bar
        self._draw_mini_bar(painter, text_x, 48, 80, 8, self._cpu_percent / 100.0, cpu_color, "CPU")
        # RAM bar
        self._draw_mini_bar(painter, text_x, 62, 80, 8, self._ram_percent / 100.0, ram_color, "RAM")

        # Saat (mood renkli)
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M")
        painter.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(mr, mg, mb, 80), 1.0))
        painter.drawText(QRectF(text_x + 100, 44, 90, 30), Qt.AlignmentFlag.AlignRight, time_str)

        # Batarya (varsa)
        if _PSUTIL:
            try:
                bat = psutil.sensors_battery()
                if bat:
                    bat_icon = "⚡" if bat.power_plugged else "🔋"
                    painter.setFont(font_small)
                    painter.setPen(QPen(TEXT_DIM, 1.0))
                    painter.drawText(
                        QRectF(text_x, 78, w - text_x - 8, 14),
                        Qt.AlignmentFlag.AlignLeft,
                        f"{bat_icon} {bat.percent:.0f}%"
                    )
            except Exception:
                pass

        # Son log (kısa)
        if self._last_log:
            painter.setFont(font_small)
            painter.setPen(QPen(QColor(100, 130, 160, 120), 1.0))
            truncated = self._last_log[:40] + "…" if len(self._last_log) > 40 else self._last_log
            painter.drawText(
                QRectF(text_x, h - 22, w - text_x - 8, 16),
                Qt.AlignmentFlag.AlignLeft,
                truncated
            )

    def _draw_mini_bar(self, painter: QPainter, x, y, w, h, fraction, color, label):
        """Minimal progress bar."""
        painter.setFont(QFont("Consolas", 7))
        painter.setPen(QPen(TEXT_DIM, 1.0))
        painter.drawText(QRectF(x, y, 28, h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)

        bar_x = x + 30
        bar_w = w - 30

        painter.setBrush(QBrush(QColor(30, 40, 55, 100)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(bar_x, y + 1, bar_w, h - 2), 2, 2)

        fill_w = bar_w * min(fraction, 1.0)
        if fill_w > 0:
            fill_color = QColor(color)
            fill_color.setAlpha(140)
            painter.setBrush(QBrush(fill_color))
            painter.drawRoundedRect(QRectF(bar_x, y + 1, fill_w, h - 2), 2, 2)

        painter.setFont(QFont("Consolas", 7))
        painter.setPen(QPen(TEXT_LIGHT, 1.0))
        painter.drawText(
            QRectF(bar_x + bar_w + 4, y, 30, h),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            f"{fraction * 100:.0f}%"
        )

    # ═══════════════════════════════════════════
    #  UYUMLULUK METOTLARı
    # ═══════════════════════════════════════════

    def write_log(self, text):
        self.log_signal.emit(text)

    def set_state(self, state):
        self.state_signal.emit(state)

    def _safe_write_log(self, text):
        self._last_log = text.replace("[CORE LOG]: ", "").replace("SYS: ", "")
        print(f"[CORE LOG]: {text}")

    def _safe_set_state(self, state):
        if getattr(self, "_state", None) != state:
            self._glitch_intensity = 1.0 # State değiştiğinde glitch tetikle
        self._state = state
        if state in ("SPEAKING", "THINKING"):
            self._switch_mode(self.MODE_EXPANDED)

    def wait_for_api_key(self):
        pass

    class _MockRoot:
        def mainloop(self):
            app = QApplication.instance()
            sys.exit(app.exec())

    @property
    def root(self):
        return self._MockRoot()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisUI()
    sys.exit(app.exec())
