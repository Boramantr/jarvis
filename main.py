import asyncio
import audioop as _audioop  # audioop-lts paketi 3.13+ için aynı API'yi sağlar
import importlib
import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

from core.logging_setup import setup_logging

log = setup_logging()

import sounddevice as sd
from google import genai
from google.genai import types

from actions.context_awareness import ContextAwareness
from actions.health_guardian import HealthGuardian
from actions.proactive_monitor import ProactiveMonitor
from agent.initiative_engine import InitiativeEngine
from config.tool_declarations import TOOL_DECLARATIONS
from core import live_state
from core.circadian import CircadianEngine
from core.emotion_engine import EmotionEngine
from core.personality import get_personality_context, get_profession_context, set_profession, start_work_session
from core.personality_evolution import PersonalityEvolution
from memory.deep_bond import DeepBond
from memory.episodic import get_recent_context, get_tool_hints, log_command, log_event
from memory.goals_engine import GoalsEngine
from memory.memory_manager import (
    format_memory_for_prompt,
    load_memory,
)
from memory.routines import get_routine_context, track_activity
from memory.routines import track_command as track_routine_command
from memory.social_graph import SocialGraph
from memory.usage_tracker import track_command as track_usage_command
from memory.usage_tracker import track_error
from ui import JarvisUI


# --- AYARLAR ---
def get_base_dir():
    # Frozen (PyInstaller): paketlenmiş kaynaklar _MEIPASS (onedir'de _internal) altında.
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent

def get_exe_dir() -> Path:
    """Kullanıcının düzenleyebileceği dosyalar (api_keys.json, .env) için exe komşu dizini."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

from core.config import settings

BASE_DIR        = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH     = BASE_DIR / "core" / "prompt.txt"
LIVE_MODEL          = settings.live_model
CHANNELS            = settings.channels
SEND_SAMPLE_RATE    = settings.send_sample_rate
RECEIVE_SAMPLE_RATE = settings.receive_sample_rate
CHUNK_SIZE          = settings.chunk_size

sys.path.append(str(BASE_DIR / "actions"))

def _get_api_key() -> str:
    key = settings.resolve_api_key()
    if not key:
        raise RuntimeError("Gemini API key bulunamadı (JARVIS_GEMINI_API_KEY veya config/api_keys.json)")
    return key

def _load_system_prompt() -> str:
    try:
        return PROMPT_PATH.read_text(encoding="utf-8")
    except Exception:
        return "You are JARVIS. You have full control over the system. Assist the user concisely."


class JarvisLive:
    def __init__(self, ui: JarvisUI):
        self.ui             = ui
        self.session        = None
        self.audio_in_queue = None
        self.out_queue      = None
        self._loop          = None
        self._is_speaking   = False
        self._speaking_lock = threading.Lock()
        self.ui.on_text_command = self._on_text_command
        self._turn_done_event: asyncio.Event | None = None
        self.safe_mode = settings.safe_mode   # destructive tool'larda kullanıcı onayı şart
        self.actions = {}
        self.load_all_actions()

        # Phase 2: Background systems
        self.proactive_monitor = ProactiveMonitor(speak_callback=self.speak, ui_callback=self.ui)
        self.context_awareness = ContextAwareness()
        start_work_session()

        # Phase 3: Living Organism systems
        self.emotion_engine = EmotionEngine()
        self.deep_bond = DeepBond()

        # Phase 4: Gelişen İlişki systems
        self.circadian = CircadianEngine()
        self.personality_evo = PersonalityEvolution()
        self.goals_engine = GoalsEngine()
        self.health_guardian = HealthGuardian()
        self.social_graph = SocialGraph()

        self.initiative_engine = InitiativeEngine(
            speak_callback=self.speak,
            emotion_engine=self.emotion_engine,
            deep_bond=self.deep_bond,
            context_awareness=self.context_awareness,
            goals_engine=self.goals_engine,
        )
        self._sync_mood_to_ui()
        # Circadian ritmini routines verisinden öğren
        try:
            from memory.routines import _load as load_routines
            self.circadian.learn_from_routines(load_routines())
        except Exception:
            log.exception("Circadian routines yüklenemedi")

        # Tool prewarm: en sık kullanılan 5 tool'u arka planda lazy import et
        # (Cold-start tool latency'sini saklar; ilk çağrı anında saniyeler.)
        threading.Thread(target=self._prewarm_top_tools, daemon=True, name="tool-prewarm").start()

        # Web dashboard'u arka planda başlat
        # (/reactor sayfası http://127.0.0.1:8765/reactor adresinde erişilebilir)
        if settings.dashboard_enabled:
            threading.Thread(target=self._start_dashboard, daemon=True, name="dashboard").start()

        self._overlay_proc = None  # geriye dönük uyum için tutulur, kullanılmıyor

    def _start_dashboard(self):
        try:
            time.sleep(2.0)
            from dashboard.server import serve
            log.info("Dashboard: http://%s:%d", settings.dashboard_host, settings.dashboard_port)
            serve(host=settings.dashboard_host, port=settings.dashboard_port)
        except Exception:
            log.exception("Dashboard başlatılamadı")

    def _prewarm_top_tools(self):
        try:
            time.sleep(3.0)   # uygulama önce ayağa kalksın
            from memory.episodic import get_tool_hints as _h
            hints = _h(days=14) or ""
            # hints satırlarındaki tool isimlerini ayıkla
            tops = []
            for line in hints.splitlines():
                line = line.strip()
                if line.startswith("✓"):
                    parts = line[1:].split("—", 1)[0].strip().split()
                    if parts:
                        tops.append(parts[0])
                if len(tops) >= 5:
                    break
            warmed = 0
            for tool in tops:
                if tool in self.action_registry and tool not in self._action_fn_cache:
                    if self._resolve_action(tool):
                        warmed += 1
            log.info("Tool prewarm: %d/%d hazır (%s)", warmed, len(tops), ", ".join(tops))
        except Exception:
            log.exception("Tool prewarm başarısız")

    def load_all_actions(self):
        """Actions klasörünü TARAR — gerçek import'u ilk çağrıya bırakır.

        Her .py dosyası AST ile parse edilip `def XXX_action(...)` fonksiyon adları
        çıkarılır. Sonuç: {tool_key: (module_name, fn_name)} kayıt defteri.
        İlk komutta modül lazy import edilir ve sonuç cache'lenir.

        Bu sayede ~45 modülün top-level dev import'ları (cv2, mss, playwright,
        pyautogui, spotipy, BeautifulSoup, vs.) başlangıçta RAM'e yüklenmez.
        """
        import ast as _ast
        self.action_registry: dict[str, tuple[str, str]] = {}
        self._action_fn_cache: dict[str, object] = {}
        actions_path = BASE_DIR / "actions"
        for filename in os.listdir(actions_path):
            if not filename.endswith(".py") or filename.startswith("__"):
                continue
            module_name = filename[:-3]
            try:
                source = (actions_path / filename).read_text(encoding="utf-8")
                tree = _ast.parse(source, filename=filename)
                for node in tree.body:
                    if isinstance(node, _ast.FunctionDef) and node.name.endswith("_action") and not node.name.startswith("_"):
                        tool_key = node.name[: -len("_action")]
                        self.action_registry[tool_key] = (module_name, node.name)
            except Exception as e:
                log.warning("Action keşif başarısız (%s): %s", filename, e)
        # Geriye dönük uyumluluk: self.actions hala var; lazy bir proxy değil ama
        # _execute_tool artık registry üzerinden çalışır.
        self.actions = {}
        log.info("Aksiyon keşfi: %d tool (lazy import)", len(self.action_registry))

    def _resolve_action(self, tool_key: str):
        """tool_key için gerçek fonksiyonu döndürür. İlk çağrıda import eder."""
        if tool_key in self._action_fn_cache:
            return self._action_fn_cache[tool_key]
        entry = self.action_registry.get(tool_key)
        if not entry:
            return None
        module_name, fn_name = entry
        try:
            module = importlib.import_module(module_name)
            fn = getattr(module, fn_name, None)
            if fn is None:
                return None
            self._action_fn_cache[tool_key] = fn
            self.actions[tool_key] = fn
            return fn
        except Exception:
            log.exception("Modül import edilemedi: %s", module_name)
            return None

    def _on_text_command(self, text: str):
        if not self._loop or not self.session: return
        # Metin girdisinden duygu ve kişilik analizi
        self.emotion_engine.analyze_text(text)
        self.personality_evo.evolve_from_text(text)
        self._sync_mood_to_ui()
        self._last_user_text = text  # semantik recall için
        # Transcript: kullanıcı turn'ü
        try:
            from memory.transcripts import log_turn
            log_turn("user", text)
        except Exception:
            pass
        # 30+ karakter girdiyi vektör belleğe at — sonra hatırlanabilsin
        if len(text) >= 30:
            try:
                from memory import vector_memory as _vm
                threading.Thread(target=_vm.remember, args=(text, "conversation"), daemon=True).start()
            except Exception:
                pass
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(turns={"parts": [{"text": text}]}, turn_complete=True),
            self._loop
        )

    _UI_MODE = {"SPEAKING": "speak", "LISTENING": "listen", "THINKING": "think"}

    def _push_mode(self, ui_state: str):
        """UI durumunu hem PyQt'ye hem web reaktörüne yansıt."""
        self.ui.set_state(ui_state)
        live_state.set_mode(self._UI_MODE.get(ui_state, "online"))

    def set_speaking(self, value: bool):
        with self._speaking_lock: self._is_speaking = value
        if value: self._push_mode("SPEAKING")
        elif not self.ui.muted: self._push_mode("LISTENING")

    def speak(self, text: str):
        if not self._loop or not self.session: return
        asyncio.run_coroutine_threadsafe(
            self.session.send_client_content(turns={"parts": [{"text": text}]}, turn_complete=True),
            self._loop
        )

    def _sync_mood_to_ui(self):
        """Emotion engine'deki mood'u UI'a ve web reaktörüne yansıt."""
        try:
            hints = self.emotion_engine.get_ui_hints()
            r, g, b = hints.get("rgb", (0, 191, 255))
            intensity = hints.get("intensity", 0.5)
            pulse = hints.get("pulse_speed", 1.0)
            self.ui.set_mood(
                self.emotion_engine.current_mood,
                rgb=(r, g, b), intensity=intensity, pulse_speed=pulse
            )
            live_state.set(mood=str(self.emotion_engine.current_mood), mood_rgb=[int(r), int(g), int(b)])
        except Exception:
            log.exception("Mood UI'a senkronlanamadı")

    _CTX_CACHE_TTL = settings.ctx_cache_ttl   # saniye
    _CTX_BLOCK_CAP = settings.ctx_block_cap   # her bloğun max karakter
    _CTX_TOTAL_CAP = settings.ctx_total_cap   # tüm dinamik bloklar toplamı

    @staticmethod
    def _trim_block(text: str, cap: int) -> str:
        if not text:
            return ""
        text = text.strip()
        if len(text) <= cap:
            return text
        return text[: cap - 15].rstrip() + " …[trim]"

    def _gather_context(self) -> str:
        """Tüm engine'lerden prompt bağlamlarını topla. 60sn cache'lenir.
        Token bütçesi: blok başına 500, toplam dinamik 4000 char.
        """
        now = time.monotonic()
        cached = getattr(self, "_ctx_cache", None)
        if cached and (now - cached[0]) < self._CTX_CACHE_TTL:
            return cached[1]

        mem_str = format_memory_for_prompt(load_memory())
        # Son kullanıcı sözüne göre semantik recall (boşsa atlanır)
        try:
            from memory.vector_memory import get_context_for_prompt as _vrecall
            semantic_ctx = _vrecall(getattr(self, "_last_user_text", "") or "", k=3) if getattr(self, "_last_user_text", "") else ""
        except Exception:
            semantic_ctx = ""
        raw_blocks = [
            ("semantic_recall", semantic_ctx),
            ("personality", get_personality_context()),
            ("profession", get_profession_context()),
            ("evolution", self.personality_evo.get_prompt_context()),
            ("circadian", self.circadian.get_prompt_context()),
            ("emotion", self.emotion_engine.get_prompt_context()),
            ("bond", self.deep_bond.get_bond_context()),
            ("goals", self.goals_engine.get_prompt_context()),
            ("health", self.health_guardian.get_prompt_context()),
            ("social", self.social_graph.get_prompt_context()),
            ("memory", mem_str),
            ("recent", get_recent_context(hours=2)),
            ("tool_hints", get_tool_hints(days=7)),
            ("routine", get_routine_context()),
            ("active_app", self.context_awareness.get_context_for_prompt()),
        ]
        # Blok başına trim + toplam tavanına ulaşınca fazlasını at
        kept = []
        running = 0
        for _name, text in raw_blocks:
            t = self._trim_block(text, self._CTX_BLOCK_CAP)
            if not t:
                continue
            if running + len(t) > self._CTX_TOTAL_CAP:
                break
            kept.append(t)
            running += len(t) + 2  # \n\n separator
        kept.append(_load_system_prompt())  # ana prompt hep en sonda, trim'siz
        ctx_body = "\n\n".join(kept)
        self._ctx_cache = (now, ctx_body)
        return ctx_body

    def _tick_living_state(self) -> None:
        """Yan etkili güncellemeler: kişilik evrimi, mood, bağlamsal analiz.
        _build_config'den ayrıldı ki cache'lenebilir context inşası saf kalsın.
        """
        try:
            self.personality_evo.evolve_from_bond(
                bond_level=self.deep_bond.data.get("bond_level", 0),
                daily_streak=self.deep_bond.data.get("daily_streak", 0),
                total_interactions=self.deep_bond.data.get("total_interactions", 0),
            )
            self.health_guardian.record_mood(self.emotion_engine.current_mood)
            work_mins = int((datetime.now() - self.proactive_monitor._session_start).total_seconds() / 60)
            try:
                app_cat = self.context_awareness.get_current_context().get("category", "other")
            except Exception:
                app_cat = "other"
            self.emotion_engine.analyze_context(
                hour=datetime.now().hour, work_minutes=work_mins, app_category=app_cat
            )
            self._sync_mood_to_ui()
        except Exception:
            log.exception("tick_living_state hatası")

    def _wake_word_policy(self) -> str:
        if not settings.wake_word_enabled:
            return ""
        w = settings.wake_word
        return (
            f"[ÇOK ÖNEMLİ — UYANDIRMA KELİMESİ POLİTİKASI]\n"
            f"Kullanıcı bir odada başkalarıyla da konuşuyor olabilir. SADECE sana doğrudan "
            f"'{w}' diye hitap ederek başlayan cümlelere yanıt ver.\n"
            f"- Cümle '{w}' ile başlamıyorsa: KESİNLİKLE SESSİZ KAL. Hiçbir ses çıkarma, "
            f"onay verme, 'efendim' deme. Sanki duymamış gibi davran.\n"
            f"- Cümle '{w}' ile başlıyorsa: normal şekilde yanıtla ve yardımcı ol.\n"
            f"- Kullanıcı uzun, çok cümleli konuşurken sözünü BÖLME; bitirmesini bekle, "
            f"sonra tek seferde yanıtla.\n"
        )

    def _build_config(self) -> types.LiveConnectConfig:
        self._tick_living_state()
        time_str = datetime.now().strftime("%A, %B %d, %Y — %H:%M")
        ctx = f"[TIME]: {time_str}\n\n{self._wake_word_policy()}\n{self._gather_context()}"
        cfg_kwargs = dict(
            response_modalities=["AUDIO"],
            system_instruction=ctx,
            tools=[{"function_declarations": TOOL_DECLARATIONS}],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=settings.voice_name)
                )
            ),
        )
        # Asistan çıkışının metin transkripti (transcript log için)
        try:
            cfg_kwargs["output_audio_transcription"] = types.AudioTranscriptionConfig()
        except Exception:
            pass
        # Kullanıcı girişinin transkripti — wake-word kontrolü için gerekli
        try:
            cfg_kwargs["input_audio_transcription"] = types.AudioTranscriptionConfig()
        except Exception:
            pass
        # VAD: uzun cümlelerde araya girmesin — sonu geç algıla, uzun sessizlik bekle
        try:
            end_sens = {
                "low": types.EndSensitivity.END_SENSITIVITY_LOW,
                "high": types.EndSensitivity.END_SENSITIVITY_HIGH,
            }.get(settings.vad_end_sensitivity.lower(), types.EndSensitivity.END_SENSITIVITY_LOW)
            cfg_kwargs["realtime_input_config"] = types.RealtimeInputConfig(
                automatic_activity_detection=types.AutomaticActivityDetection(
                    end_of_speech_sensitivity=end_sens,
                    silence_duration_ms=settings.vad_silence_ms,
                    prefix_padding_ms=settings.vad_prefix_padding_ms,
                ),
            )
        except Exception:
            log.exception("VAD config kurulamadı")
        return types.LiveConnectConfig(**cfg_kwargs)

    # Onay gerektiren tool'lar (safe_mode açıkken). Model `confirm=true` argümanı
    # geçtiğinde gerçekten yürütülür; ilk çağrıda kullanıcıya sorması istenir.
    _DESTRUCTIVE_TOOLS = frozenset({
        "system_power", "shutdown_jarvis", "file_master", "file_write",
        "send_message", "process_guard", "macro_automator", "task_manager",
        "code_runner", "architect",
    })

    def _needs_confirmation(self, name: str, args: dict) -> tuple[bool, str]:
        """Tool tehlikeli mi + soracağımız soru."""
        if not getattr(self, "safe_mode", True):
            return False, ""
        if name not in self._DESTRUCTIVE_TOOLS:
            return False, ""
        if str(args.get("confirm", "")).lower() in ("true", "1", "yes", "evet"):
            return False, ""
        # Bazı non-destructive eylemleri whitelist
        action = (args.get("action") or "").lower()
        if name == "task_manager" and action in ("open", "open_performance", "system_info",
                                                 "list_processes", "disk_usage", "network_info", "battery"):
            return False, ""
        if name == "process_guard" and action != "kill":
            return False, ""
        if name == "file_master" and action in ("open",):
            return False, ""
        if name == "file_write" and not args.get("overwrite"):
            return False, ""  # yeni dosya yazma — onay yok
        # Hedefi mesaja ekle
        target = args.get("target") or args.get("path") or args.get("app") or args.get("receiver") or ""
        return True, f"Bu işlem geri alınamayabilir. {name}({action or target}) onaylıyor musun?"

    async def _execute_tool(self, fc) -> types.FunctionResponse:
        name = fc.name
        args = dict(fc.args or {})
        print(f"[JARVIS] ⚙️ Otonom Yürütme: {name} {args}")
        self._push_mode("THINKING")
        live_state.set(tool=name, load=0.9)   # reaktör: çıkış göstergesi yükselir

        # ── Confirmation gate ──
        needs, question = self._needs_confirmation(name, args)
        if needs:
            return types.FunctionResponse(id=fc.id, name=name, response={
                "ok": False,
                "needs_confirmation": True,
                "question": question,
                "hint": "Kullanıcıya soruyu sor. Onay alınca aynı tool'u `confirm=true` ile tekrar çağır.",
            })

        # Phase 2: Aktivite takibi (komut log'u sonuca göre aşağıda yazılır)
        try:
            track_activity()
            track_usage_command(name)
            track_routine_command(name)
        except Exception:
            log.exception("Aktivite/usage takibi başarısız (%s)", name)
        loop = asyncio.get_event_loop()
        result = "Done."
        ok = True
        _t0 = time.perf_counter()

        err_type = None
        err_hint = None
        try:
            if name == "profession_mode":
                mode = args.get("mode", "normal")
                result = set_profession(mode)
            elif name in self.action_registry:
                fn = self._resolve_action(name)
                if fn is None:
                    result = f"Tool '{name}' could not be loaded."
                    err_type = "ImportFailed"
                    err_hint = "Bağımlılık eksik olabilir. Aynı işi code_runner ile dene veya başka bir tool seç."
                    ok = False
                else:
                    result = await loop.run_in_executor(None, lambda: fn(parameters=args, player=self.ui))
                # architect başarılıysa registry'yi taze tara — yeni tool anında erişilebilir
                if name == "architect" and isinstance(result, str) and result.startswith("✅"):
                    try:
                        self.load_all_actions()
                        log.info("Architect → registry refresh, toplam %d tool", len(self.action_registry))
                    except Exception:
                        log.exception("Architect sonrası registry refresh başarısız")
            elif name == "system_power":
                action_type = args.get("action", "")
                import subprocess
                _CREATE_NO_WINDOW = 0x08000000
                if action_type == "shutdown":
                    subprocess.Popen(["shutdown", "/s", "/t", "10"], creationflags=_CREATE_NO_WINDOW)
                elif action_type == "restart":
                    subprocess.Popen(["shutdown", "/r", "/t", "10"], creationflags=_CREATE_NO_WINDOW)
                elif action_type == "sleep":
                    subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], creationflags=_CREATE_NO_WINDOW)
                result = f"Power action {action_type} executed."
            elif name == "shutdown_jarvis":
                self.speak("Goodbye, sir.")
                def _graceful_exit():
                    time.sleep(1)
                    try:
                        self.shutdown()
                    except Exception:
                        log.exception("shutdown sırasında hata")
                    os._exit(0)
                threading.Thread(target=_graceful_exit, daemon=True).start()
            else:
                result = f"Tool '{name}' not found."
                err_type = "ToolNotFound"
                err_hint = f"Mevcut tool'lar: {sorted(self.action_registry.keys())[:10]}... code_runner ile manuel çözüm dene."
                ok = False
                print(f"[JARVIS] ❌ {result}")
        except Exception as e:
            result = str(e)
            err_type = type(e).__name__
            err_hint = "Parametreleri kontrol et veya code_runner ile alternatif yol dene."
            traceback.print_exc()
            ok = False
            try:
                track_error()
            except Exception:
                log.exception("track_error başarısız")

        # Sonuca göre tool log'u
        if isinstance(result, str) and result.lower().startswith(("error", "hata")) and ok:
            ok = False
            err_type = err_type or "ToolReturnedError"
            err_hint = err_hint or "Bu tool hata mesajı döndürdü. Farklı parametreler veya code_runner dene."
        _latency_ms = int((time.perf_counter() - _t0) * 1000)
        try:
            log_command(name, str(args)[:100], ok=ok, latency_ms=_latency_ms)
        except Exception:
            log.exception("log_command başarısız (%s)", name)

        live_state.set(tool="", load=0.42)   # reaktör: nominal çıkışa dön
        if not self.ui.muted: self._push_mode("LISTENING")

        # Yaşayan organizma: etkileşimi kaydet
        try:
            self.deep_bond.record_interaction(
                mood=self.emotion_engine.current_mood, tool_used=name
            )
            self.initiative_engine.mark_interaction()
        except Exception:
            log.exception("Bond/initiative kayıt başarısız (%s)", name)

        # Yapılandırılmış sonuç: hata varsa model net hint görür ve retry stratejisi seçer
        if ok:
            payload = {"result": result}
        else:
            payload = {
                "ok": False,
                "error_type": err_type or "Unknown",
                "message": str(result)[:600],
                "hint": err_hint or "Alternatif bir yol dene; pes etme.",
            }
        return types.FunctionResponse(id=fc.id, name=name, response=payload)

    async def _send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send_realtime_input(media=msg)

    @staticmethod
    def _fast_rms(buf) -> float:
        """Native C RMS (audioop-lts) — 5-10x daha hızlı, sıfır Python alloc."""
        try:
            # int16 PCM, 2 byte sample width
            data = buf if isinstance(buf, (bytes, bytearray)) else bytes(buf)
            return _audioop.rms(data, 2) / 4500.0
        except Exception:
            return 0.0

    def _emit_audio_level(self, level: float, force: bool = False) -> None:
        """UI'a ses seviyesi sinyalini throttle ederek gönder."""
        now = time.monotonic()
        last_t = getattr(self, "_last_lvl_t", 0.0)
        last_v = getattr(self, "_last_lvl_v", -1.0)
        if force or abs(level - last_v) >= 0.04 or (now - last_t) >= 0.05:
            self._last_lvl_t = now
            self._last_lvl_v = level
            self.ui.audio_signal.emit(float(level))
            live_state.set_audio(level)

    _INTERRUPT_RMS = settings.interrupt_rms       # mic seviyesi (0-1 normalized)
    _INTERRUPT_STREAK = settings.interrupt_streak # ardışık callback (~150ms)

    def _drain_tts_queue(self):
        """Konuşma kesildiğinde bekleyen TTS chunk'larını at — sessizliğe dön."""
        if self.audio_in_queue is None:
            return
        n = 0
        while not self.audio_in_queue.empty():
            try:
                self.audio_in_queue.get_nowait()
                n += 1
            except asyncio.QueueEmpty:
                break
        if n:
            log.info("Voice interrupt: %d TTS chunk dropped", n)
            self._emit_audio_level(0.0, force=True)

    async def _listen_audio(self):
        loop = asyncio.get_event_loop()
        self._interrupt_streak = 0
        def callback(indata, f, t, s):
            if self.ui.muted:
                return
            speaking = self._is_speaking
            rms = self._fast_rms(indata)
            if speaking:
                # Konuşma sırasında: sadece interrupt sezgisi için dinle
                if rms >= self._INTERRUPT_RMS:
                    self._interrupt_streak += 1
                    if self._interrupt_streak >= self._INTERRUPT_STREAK:
                        # Kullanıcı söze girdi — TTS'i kes, mic'i tekrar producer'a aç
                        self._interrupt_streak = 0
                        loop.call_soon_threadsafe(self._drain_tts_queue)
                        loop.call_soon_threadsafe(lambda: self.set_speaking(False))
                        loop.call_soon_threadsafe(
                            self.out_queue.put_nowait,
                            {"data": indata.tobytes(), "mime_type": "audio/pcm"},
                        )
                else:
                    self._interrupt_streak = 0
                return
            # Normal dinleme yolu
            self._interrupt_streak = 0
            loop.call_soon_threadsafe(self.out_queue.put_nowait, {"data": indata.tobytes(), "mime_type": "audio/pcm"})
            if (time.monotonic() - getattr(self, "_last_lvl_t", 0.0)) >= 0.05:
                self._emit_audio_level(rms)
        with sd.InputStream(samplerate=SEND_SAMPLE_RATE, channels=CHANNELS, dtype="int16", blocksize=CHUNK_SIZE, callback=callback):
            while True: await asyncio.sleep(0.1)

    def _is_addressed(self, text: str) -> bool:
        """Girdi cümlesi wake-word ile başlıyor mu?

        Temkinli: emin değilse True döner (susturma yapma, prompt politikası halleder).
        Sadece ilk 2 kelimeye bakar; STT varyantlarını (carvis/javis/jarvıs) esnek yakalar.
        """
        if not text:
            return True  # transkript yoksa karar verme, susturma
        import re as _re
        words = _re.findall(r"\w+", text.lower())[:2]
        if not words:
            return True
        w = settings.wake_word.lower()
        stem = w[:4]  # "jarv"
        for word in words:
            if (word == w or word.startswith(stem)
                    or "arvis" in word or "arvıs" in word
                    or word.startswith(("jar", "car", "jav"))):
                return True
        return False

    async def _receive_audio(self):
        self._assistant_buf = []
        self._input_buf = []
        self._turn_suppressed = False
        while True:
            async for response in self.session.receive():
                sc = response.server_content
                # Girdi transkripti — wake-word kontrolü
                if sc:
                    it = getattr(sc, "input_transcription", None)
                    if it and getattr(it, "text", None):
                        self._input_buf.append(it.text)
                        if settings.wake_word_enabled and not self._turn_suppressed:
                            joined = "".join(self._input_buf).strip()
                            if len(joined.split()) >= 1 and not self._is_addressed(joined):
                                # Hitap edilmedi → bu turn'ü sustur
                                self._turn_suppressed = True
                                self._drain_tts_queue()

                if response.data:
                    if self._turn_suppressed:
                        pass  # hitap edilmemiş → sesi çalma
                    else:
                        # Backpressure: queue doluysa playback bitene kadar await — DROP yok
                        await self.audio_in_queue.put(response.data)
                if sc:
                    # Asistan çıkış transkriptini biriktir
                    ot = getattr(sc, "output_transcription", None)
                    if ot and getattr(ot, "text", None):
                        self._assistant_buf.append(ot.text)
                    if sc.turn_complete:
                        self._turn_done_event.set()
                        # Girdi transkriptini kaydet
                        user_said = "".join(self._input_buf).strip()
                        self._input_buf = []
                        if user_said:
                            try:
                                from memory.transcripts import log_turn
                                log_turn("user", user_said)
                            except Exception:
                                pass
                        # Asistan yanıtını kaydet (susturulmadıysa)
                        if self._assistant_buf and not self._turn_suppressed:
                            full = "".join(self._assistant_buf).strip()
                            if full:
                                try:
                                    from memory.transcripts import log_turn
                                    log_turn("assistant", full)
                                except Exception:
                                    pass
                        self._assistant_buf = []
                        self._turn_suppressed = False  # sonraki turn için sıfırla
                if response.tool_call:
                    # Bağımsız tool çağrılarını paralel çalıştır
                    calls = list(response.tool_call.function_calls)
                    if len(calls) == 1:
                        fn_res = [await self._execute_tool(calls[0])]
                    else:
                        fn_res = await asyncio.gather(
                            *(self._execute_tool(fc) for fc in calls)
                        )
                    await self.session.send_tool_response(function_responses=fn_res)

    async def _play_audio(self):
        stream = sd.RawOutputStream(samplerate=RECEIVE_SAMPLE_RATE, channels=CHANNELS, dtype="int16", blocksize=CHUNK_SIZE)
        stream.start()
        while True:
            try: chunk = await asyncio.wait_for(self.audio_in_queue.get(), timeout=0.1)
            except TimeoutError:
                if self._turn_done_event.is_set() and self.audio_in_queue.empty():
                    self.set_speaking(False); self._turn_done_event.clear()
                    self._emit_audio_level(0.0, force=True)
                continue
            self.set_speaking(True)
            # RMS sadece emit zamanı geldiğinde hesaplanır
            if (time.monotonic() - getattr(self, "_last_lvl_t", 0.0)) >= 0.05:
                self._emit_audio_level(self._fast_rms(chunk))
            await asyncio.to_thread(stream.write, chunk)

    async def run(self):
        client = genai.Client(api_key=_get_api_key(), http_options={"api_version": "v1beta"})
        self._shutdown = False
        self._consecutive_fails = 0
        while not self._shutdown:
            try:
                self.ui.set_state("THINKING")
                async with client.aio.live.connect(model=LIVE_MODEL, config=self._build_config()) as session, asyncio.TaskGroup() as tg:
                    self.session = session; self._loop = asyncio.get_event_loop()
                    self._consecutive_fails = 0  # bağlantı kuruldu — sayaç sıfır
                    # audio_in_queue: TTS chunk'ları biriktirme. backpressure ile drop yok
                    self.audio_in_queue = asyncio.Queue(maxsize=settings.audio_queue_max)
                    self.out_queue = asyncio.Queue(maxsize=10)
                    self._turn_done_event = asyncio.Event()
                    self.ui.set_state("LISTENING"); self.ui.write_log("SYS: JARVIS online.")

                    # Arka plan sistemleri sadece ilk bağlantıda başlatılır
                    # (reconnect sırasında çift thread / çift sayaç önlenir).
                    if not getattr(self, "_bg_started", False):
                        self.proactive_monitor.start()
                        self.context_awareness.start()
                        self.initiative_engine.start()
                        self._bg_started = True
                        self.deep_bond.log_evolution("Session started")
                        log_event("JARVIS session started", category="system")
                    else:
                        log_event("JARVIS reconnected", category="system")

                    self.ui.set_bond_level(self.deep_bond.data.get("bond_level", 0))
                    live_state.set(bond=int(self.deep_bond.data.get("bond_level", 0)), mode="online")

                    tg.create_task(self._send_realtime()); tg.create_task(self._listen_audio())
                    tg.create_task(self._receive_audio()); tg.create_task(self._play_audio())
                    tg.create_task(self._context_prefetch_loop())
                self._reconnect_backoff = 1  # başarılı oturum kapandı → backoff reset
            except asyncio.CancelledError:
                log.info("run() iptal edildi — kapanış")
                break
            except Exception:
                self._consecutive_fails += 1
                wait = getattr(self, "_reconnect_backoff", 1)
                # Circuit breaker: 5 ardışık fail = uzun mola (API down / kota / ağ)
                if self._consecutive_fails >= 5:
                    wait = settings.reconnect_backoff_max
                    log.error("Circuit breaker: %d ardışık başarısızlık, %d sn bekleniyor",
                              self._consecutive_fails, wait)
                    self.ui.set_state("THINKING")
                else:
                    log.exception("Bağlantı koptu, %d saniye sonra yeniden denenecek", wait)
                await asyncio.sleep(wait)
                self._reconnect_backoff = min(wait * 2, settings.reconnect_backoff_max)

    async def _context_prefetch_loop(self):
        """Her 30 sn'de bir bağlamı arka planda yeniden inşa et + reaktör telemetrisi."""
        tick = 0
        while True:
            try:
                await asyncio.sleep(5)
                tick += 5
                # Reaktör için CPU sıcaklığı (gerçek donanım) — her 5 sn
                try:
                    import psutil
                    temps = getattr(psutil, "sensors_temperatures", lambda: {})() or {}
                    val = None
                    for arr in temps.values():
                        for s in arr:
                            if s.current:
                                val = s.current
                                break
                        if val:
                            break
                    if val is None:
                        # Donanım sensörü yoksa CPU yüküne göre simüle et (36-44°C)
                        val = 36 + psutil.cpu_percent() * 0.08
                    live_state.set(core_temp=round(float(val), 1))
                except Exception:
                    pass
                if tick >= 30:
                    tick = 0
                    await asyncio.to_thread(self._refresh_context_cache)
            except asyncio.CancelledError:
                return
            except Exception:
                log.exception("context prefetch hatası")

    def _refresh_context_cache(self):
        """Cache'i invalidate edip _gather_context'i tetikler — bir sonraki turda hazır."""
        self._ctx_cache = None
        self._gather_context()

    def shutdown(self):
        """Temiz kapanış: arka plan kaynakları serbest bırak, son flush yap.
        os._exit yerine bu çağrılır — TTS yarıda kalmaz, DB/WAL düzgün kapanır.
        """
        log.info("Graceful shutdown başladı")
        self._shutdown = True
        # Browser (Playwright Chromium)
        try:
            from actions.browser_agent import _close_browser
            _close_browser()
        except Exception:
            pass
        # Arka plan motorları
        for engine_name in ("proactive_monitor", "context_awareness", "initiative_engine"):
            engine = getattr(self, engine_name, None)
            stop = getattr(engine, "stop", None)
            if callable(stop):
                try:
                    stop()
                except Exception:
                    log.exception("%s.stop() başarısız", engine_name)
        # Episodic DB
        try:
            import memory.episodic as ep
            if ep._conn is not None:
                ep._conn.close()
                ep._conn = None
        except Exception:
            pass
        # Vector DB
        try:
            import memory.vector_memory as vm
            if vm._conn is not None:
                vm._conn.close()
                vm._conn = None
        except Exception:
            pass
        # Transcript DB
        try:
            import memory.transcripts as tr
            if tr._conn is not None:
                tr._conn.close()
                tr._conn = None
        except Exception:
            pass
        log.info("Graceful shutdown tamam")

def main():
    """qasync ile Qt + asyncio tek event loop'ta.
    Eski mimaride asyncio ayrı daemon thread'deydi; her tool çağrısı ve UI sinyali
    thread bağlamı değiştiriyordu. qasync ile her şey tek thread — daha az
    context switch, temiz shutdown, sıfır threadsafe köprü ihtiyacı.
    """
    import qasync
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    ui = JarvisUI("face.png")
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    jarvis = JarvisLive(ui)

    def _on_quit():
        try:
            jarvis.shutdown()
        except Exception:
            log.exception("Pencere kapanışında shutdown hatası")
        loop.stop()

    app.aboutToQuit.connect(_on_quit)
    with loop:
        loop.create_task(jarvis.run())
        loop.run_forever()

if __name__ == "__main__":
    main()
