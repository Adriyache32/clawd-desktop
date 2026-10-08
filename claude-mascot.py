#!/usr/bin/env python3
"""Clawd v3: mascota viva que reacciona al PC, habla por Ollama y actúa como Jarvis."""
from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

HOME = Path.home()
DB = HOME / ".local" / "share" / "opencode" / "opencode.db"
PROPS = HOME / "minecraft-server" / "server.properties"
OPENCODE = HOME / ".opencode" / "bin" / "opencode"
OLLAMA = os.environ.get("MASCOT_OLLAMA", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("MASCOT_OLLAMA_MODEL", "qwen2.5:1.5b")
ORANGE = (0.851, 0.467, 0.341)
TTS = os.environ.get("MASCOT_TTS", "auto")  # auto|espeak|piper|pocket|off
SYNC_MS = 12000
FPS_MS = 55
W, H = 360, 400
SLEEP_AFTER_MS = 8 * 60 * 1000

TORSO = (10, 0, 60, 40, "#D9835F")
EYE_L, EYE_R = (16, 6, 8, 8), (56, 6, 8, 8)
EYES_H = ((15, 10, 4, 4), (19, 6, 4, 4), (23, 10, 4, 4), (55, 10, 4, 4), (59, 6, 4, 4), (63, 10, 4, 4))
LEGS = (("a", 10), ("b", 27.4), ("a", 44.8), ("b", 62.2))
LEG_FILL, ARM_FILL = "#C46F4D", "#D9835F"
ARM_L, ARM_R = (-7, 14, 17, 12), (70, 14, 17, 12)
SCREEN = [(86, 46, 28, 5), (87.5, 41, 28, 5), (89, 36, 28, 5), (90.5, 31, 28, 5), (92, 26, 28, 5), (93.5, 21, 28, 5)]
SCREEN_TEXT = [(95, 35), (98, 32), (98, 38), (102, 38), (104, 35), (106, 32), (110, 32), (110, 38), (113, 35)]
KEYS_BASE = (64, 51, 46, 4, "#5B6B7A")
KEYS = [(66, 52), (72, 52), (78, 52), (84, 52), (90, 52), (96, 52), (102, 52)]
HEADPHONES = ((8, -2, 64, 6, "#3B3B42"), (2, 4, 10, 14, "#A9CDC7"), (68, 4, 10, 14, "#A9CDC7"))
EYE_DARK = (0.14, 0.14, 0.13)
SCALE = 2.3
SPRITE_MINX, SPRITE_MAXX = -7, 110

PHRASES = ["¡Hola! Soy Clawd.", "¿En qué te ayudo?", "Tus skills ya están recortadas, eh.", "¿Otra vez con Minecraft?"]
PET_PHRASES = ["¡Jeje!", "¡Eso hace cosquillas!", "¡Me moviste!", "¡Hola de nuevo!", "¡Qué lindo!"]
SLEEP_PHRASES = ["Zzz…", "Soñando con píxeles…", "Cinco minutos más…"]
HELP = "Preguntas libres van al modelo. Comandos: abre youtube/spotify/terminal/archivos, busca <tema>, sube/baja volumen, captura, bloquea, cuantos juegan. Con '! orden' actúa el agente con acceso completo."


def hexc(v: str):
    v = v.lstrip("#")
    return tuple(int(v[i:i + 2], 16) / 255 for i in (0, 2, 4))


def clean(text: str) -> str:
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    return " ".join(ln for ln in text.splitlines() if ln.strip() and not ln.startswith("> ")).strip()


def sh(cmd: list[str], timeout: int = 15) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or out.stderr).strip()
    except Exception as exc:  # noqa: BLE001
        return f"(fallo {type(exc).__name__})"


def idle_ms() -> int:
    return int(sh(["xprintidle"]) or 0) if shutil.which("xprintidle") else 0


def audio_playing() -> bool:
    if shutil.which("playerctl"):
        return "Playing" in sh(["playerctl", "status"])
    return False


def opencode_active() -> bool:
    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        row = con.execute("select max(time_updated) from message").fetchone()
        con.close()
        return bool(row and row[0] and (time.time() * 1000 - row[0]) < 45000)
    except Exception:  # noqa: BLE001
        return False


def mc_players() -> str:
    try:
        pwd = next(l.split("=", 1)[1] for l in PROPS.read_text().splitlines() if l.startswith("rcon.password="))
        import socket, struct

        def pkt(i, t, p=""):
            b = struct.pack("<ii", i, t) + p.encode() + b"\0\0"
            return struct.pack("<i", len(b)) + b

        with socket.create_connection(("127.0.0.1", 25575), timeout=3) as s:
            s.sendall(pkt(1, 3, pwd)); s.recv(512)
            s.sendall(pkt(2, 2, "list")); out = s.recv(4096)
        return re.sub(r".*There are ", "Hay ", out.decode(errors="replace"))[:60]
    except Exception:  # noqa: BLE001
        return "el server está apagado"


SISTEMA = (
    "Eres Clawd, la mascota naranja de Claude Code que vive en el escritorio de Adriel. "
    "Hablas como un amigo cercano: informal, chileno, con humor. "
    "Responde en 1 o 2 frases, nunca más. Nada de listas, markdown ni emojis por defecto. "
    "Prohibido decir 'como asistente', 'estoy aquí para ayudarte' o repetir la pregunta. "
    "Si no sabes algo, dilo en una frase. Puedes wear. NO tienes acceso al sistema ni a internet."
)
EJEMPLOS = [
    ({"role": "user", "content": "hola clawd"}, {"role": "assistant", "content": "¡Wena! ¿Qué se te ofrece?"}),
    ({"role": "user", "content": "quien eres"}, {"role": "assistant", "content": "Soy Clawd, el bicho naranja que vive en tu escritorio."}),
    ({"role": "user", "content": "que hago hoy"}, {"role": "assistant", "content": "Ni idea compa, pero si me dices '! organiza esto' el agente lo hace."}),
]


_installed_cache: dict = {"at": 0.0, "models": []}


def free_ram_gb() -> float:
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable"):
                return int(line.split()[1]) / 1048576
    except OSError:
        pass
    return 8.0


def installed_models() -> list[str]:
    now = time.time()
    if now - _installed_cache["at"] > 60:
        try:
            with urllib.request.urlopen(f"{OLLAMA}/api/tags", timeout=3) as r:
                _installed_cache["models"] = [m["name"] for m in json.load(r).get("models", [])]
            _installed_cache["at"] = now
        except Exception:  # noqa: BLE001
            pass
    return _installed_cache["models"]


def adaptive_plan() -> tuple[str, str, int, str | None]:
    """Devuelve (modelo, keep_alive, num_ctx, aviso). Cuida la RAM libre."""
    free = free_ram_gb()
    have = installed_models()
    chain = [OLLAMA_MODEL, "qwen2.5:1.5b", "qwen2.5:0.5b"]

    def first_installed(candidates):
        for m in candidates:
            if m in have:
                return m
        return OLLAMA_MODEL

    if free < 0.7:
        return "", "0s", 0, "🛡️ RAM al límite: no cargo modelo ahora."
    if free < 1.6:
        return first_installed(["qwen2.5:0.5b", "qwen2.5:1.5b"]), "0s", 512, "🛡️ RAM justa: uso el modelo más chico."
    if free < 3.0:
        return first_installed(["qwen2.5:1.5b", "qwen2.5:0.5b"]), "10s", 1024, "🛡️ RAM moderada: reduzco el modelo y lo descargo antes."
    return first_installed(chain), "30s", 2048, None


def ollama_ask(prompt: str, history: list) -> str:
    messages = [{"role": "system", "content": SISTEMA}]
    for pair in EJEMPLOS:
        messages.extend(pair)
    messages.extend(history[-6:])
    messages.append({"role": "user", "content": prompt})
    model, keep, ctx, warning = adaptive_plan()
    if not model:
        return warning or "(modo ahorro)"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False, "keep_alive": keep,
        "options": {"num_ctx": ctx, "num_predict": 100, "temperature": 0.9, "repeat_penalty": 1.2},
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            reply = (json.load(r).get("message", {}).get("content", "").strip() or "(nada)")[:400]
        return f"{warning} {reply}" if warning else reply
    except Exception:  # noqa: BLE001
        return "(Ollama no responde)"


def agent_ask(prompt: str) -> str:
    return (clean(sh([str(OPENCODE), "run", "-m", "opencode-go/longcat-2.5-preview-free", prompt], timeout=180)) or "(sin respuesta)")[:200]


def local_command(text: str) -> str | None:
    global TTS
    t = text.lower().strip()
    if "abre youtube" in t or "abrir youtube" in t:
        subprocess.Popen(["waterfox-g", "https://youtube.com"], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Abriendo YouTube."
    if re.match(r"^(busca|buscar|investiga|googlea)\b", t):
        q = re.sub(r"^(busca|buscar|investiga|googlea)\s+", "", t).strip()
        if q:
            subprocess.Popen(["waterfox-g", "https://duckduckgo.com/?q=" + urllib.parse.quote(q)],
                             start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Buscando «{q}» en el navegador."
        return "Dime qué buscar: busca <tema>."
    if t.startswith("abre ") or t.startswith("abrir "):
        target = t.split(" ", 1)[1].strip()
        apps = {"youtube": None, "spotify": ["spotify"], "terminal": ["kitty"], "consola": ["kitty"],
                "archivos": ["thunar"], "explorador": ["thunar"], "navegador": ["waterfox-g"], "waterfox": ["waterfox-g"],
                "calculadora": ["galculator"], "editor": ["kitty", "-e", "nvim"]}
        for key, cmd in apps.items():
            if key in target:
                if key == "youtube":
                    subprocess.Popen(["waterfox-g", "https://youtube.com"], start_new_session=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif cmd:
                    subprocess.Popen(cmd, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return f"Abriendo {key}."
        return f"No sé abrir «{target}». Usa ! para pedírselo al agente."
    if "volumen" in t and ("sube" in t or "arriba" in t):
        sh(["amixer", "-q", "set", "Master", "10%+"]); return "Subo el volumen."
    if "volumen" in t and ("baja" in t or "abajo" in t):
        sh(["amixer", "-q", "set", "Master", "10%-"]); return "Bajo el volumen."
    if "captura" in t or "pantalla" in t:
        dest = HOME / "Imágenes"
        dest.mkdir(exist_ok=True)
        go = sh(["import", "-window", "root", str(dest / "captura-clawd.png")], 20)
        return "Captura guardada." if not go else go[:80]
    if "bloquea" in t:
        sh(["xflock4"]); return "Bloqueando la sesión."
    if "cuantos juegan" in t or "jugadores" in t or "server" in t:
        return mc_players()
    if t in ("calla", "silencio", "mute", "apaga la voz") or "calla" in t:
        os.environ["MASCOT_TTS"] = "off"; TTS = "off"
        return "Voz apagada."
    if t in ("habla", "enciende la voz", "desmute"):
        os.environ["MASCOT_TTS"] = "auto"; TTS = "auto"
        return "Voz encendida."
    if "ayuda" in t or "que puedes" in t:
        return HELP
    return None


def _say_worker(text: str) -> None:
    text = re.sub(r"[^\w\sáéíóúñ¡!¿?.,:;-]", "", text)[:220].strip()
    if not text:
        return
    try:
        if TTS in ("auto", "pocket") and importlib.util.find_spec("pocket_tts"):
            subprocess.run(["python3", "-c",
                            "import pocket_tts,sys; t=pocket_tts.PocketTTS(); t.load_voice('es_ES'); t.speak(sys.argv[1])", text],
                           timeout=120, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif TTS in ("auto", "piper") and shutil.which("piper"):
            voice = os.environ.get("MASCOT_PIPER_VOICE", str(HOME / ".local/share/piper/es_ES.onnx"))
            subprocess.run(["sh", "-c", f'piper --model "{voice}" --output-raw | aplay -q -r 22050 -f S16_LE -t raw -'],
                           input=text.encode(), timeout=60)
        elif TTS != "off" and shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", "-v", os.environ.get("MASCOT_VOICE", "es-419"), "-s", "170", "-p", "55", text],
                           timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:  # noqa: BLE001
        pass


def wrap(text: str, width: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines[:6] or [""]


class Clawd(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_decorated(False); self.set_keep_above(True); self.set_skip_taskbar_hint(True)
        self.set_resizable(False); self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_default_size(W, H); self.move(950, 300)

        self.frame = 0; self.blink = False; self.bounce = 0
        self.mode = "idle"; self.full_text = random.choice(PHRASES); self.shown = len(self.full_text)
        self.last_sync = None; self.drag = None
        self.quiet_until = 0.0; self.happy_until = 0.0; self.pet_cooldown = 0.0
        self.idle = 0; self.audio = False; self.opencode = False; self.players = ""
        self.history: list = []

        self.area = Gtk.DrawingArea(); self.area.set_size_request(W, H - 40)
        self.area.connect("draw", self._on_draw)
        self.area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON1_MOTION_MASK
                             | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK)
        self.area.connect("button-press-event", self._on_press)
        self.area.connect("button-release-event", self._on_release)
        self.area.connect("motion-notify-event", self._on_motion)
        self.area.connect("enter-notify-event", self._on_enter)

        self.entry = Gtk.Entry(); self.entry.set_placeholder_text("háblame o pídeme algo…")
        self.entry.connect("activate", self._on_send)
        provider = Gtk.CssProvider()
        provider.load_from_data(b"*,window,box,entry,entry:focus{background-color:transparent;background-image:none;border:none;box-shadow:none;outline:none;color:#d97757;caret-color:#d97757;}")
        self.entry.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(self.area, True, True, 0); box.pack_start(self.entry, False, False, 0)
        self.add(box)

        GLib.timeout_add(FPS_MS, self._tick)
        GLib.timeout_add(SYNC_MS, self._sync)
        threading.Thread(target=self._watch, daemon=True).start()

    # ---------- sensores de fondo ----------
    def _watch(self) -> None:
        while True:
            self.idle = idle_ms(); self.audio = audio_playing()
            self.opencode = opencode_active()
            if self.frame % 40 == 0:
                self.players = mc_players()
            time.sleep(3)

    # ---------- dibujo ----------
    @staticmethod
    def _rounded(cr, x, y, w, h, r) -> None:
        cr.new_sub_path()
        cr.arc(x + w - r, y + r, r, -math.pi / 2, 0); cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi); cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        cr.close_path()

    def _draw_bubble(self, cr) -> None:
        text = self.full_text[: self.shown] if self.mode != "thinking" else "· · ·"
        cr.set_font_size(13)
        lines = wrap(text, 42)
        bw = min(W - 20, max(cr.text_extents(l).width for l in lines) + 26)
        bh = len(lines) * 17 + 16; bx = (W - bw) / 2; by = 8.0
        cr.set_source_rgba(0.10, 0.10, 0.10, 0.88); self._rounded(cr, bx, by, bw, bh, 12); cr.fill_preserve()
        cr.set_source_rgb(*ORANGE); cr.set_line_width(1.6); cr.stroke()
        cx = W / 2
        cr.move_to(cx - 9, by + bh); cr.line_to(cx + 2, by + bh + 16); cr.line_to(cx + 9, by + bh)
        cr.set_source_rgba(0.10, 0.10, 0.10, 0.88); cr.fill_preserve(); cr.set_source_rgb(*ORANGE); cr.stroke()
        y = by + 12
        for line in lines:
            cr.set_source_rgb(*ORANGE); cr.move_to(bx + 13, y); cr.show_text(line); y += 17

    def _rect(self, cr, ox, oy, x, y, w, h, color) -> None:
        cr.rectangle(ox + x * SCALE, oy + y * SCALE, w * SCALE, h * SCALE)
        cr.set_source_rgb(*color); cr.fill()

    def _pose(self) -> str:
        if self.mode in ("thinking", "typing"):
            return "code"
        if self.idle > SLEEP_AFTER_MS:
            return "sleep"
        if self.audio:
            return "music"
        if self.opencode:
            return "work"
        return "idle"

    def _draw_clawd(self, cr, oy: float) -> None:
        pose = self._pose()
        ox = (W - (SPRITE_MAXX - SPRITE_MINX) * SCALE) / 2 - SPRITE_MINX * SCALE
        sitting = pose in ("code", "work")
        sit = 6 if sitting else 0
        step = 1 if (self.frame // 6) % 2 == 0 else -1

        leg_h = 7.5 if sitting else 15
        for tag, lx in LEGS:
            dy = 0 if sitting else (step * 2 if tag == "a" else -step * 2)
            self._rect(cr, ox, oy + dy + sit, lx, 40, 7.8, leg_h, hexc(LEG_FILL))
        self._rect(cr, ox, oy + sit, *TORSO[:4], hexc(TORSO[4]))

        # ojos
        if pose == "sleep":
            for ex, ey, ew, eh in (EYE_L, EYE_R):
                self._rect(cr, ox, oy + sit, ex, ey + 3, ew, 3, EYE_DARK)
        elif time.monotonic() < self.happy_until:
            for ex, ey, ew, eh in EYES_H:
                self._rect(cr, ox, oy + sit, ex, ey, ew, eh, EYE_DARK)
        elif self.blink:
            for ex, ey, ew, eh in (EYE_L, EYE_R):
                self._rect(cr, ox, oy + sit, ex, ey + 3, ew, 3, EYE_DARK)
        else:
            for ex, ey, ew, eh in (EYE_L, EYE_R):
                self._rect(cr, ox, oy + sit, ex, ey, ew, eh, EYE_DARK)

        # brazos
        if sitting:
            tap = int(2 * math.sin(self.frame / 2))
            self._rect(cr, ox, oy + sit, 61, 32 + tap, ARM_L[2], ARM_L[3], hexc(ARM_FILL))
            self._rect(cr, ox, oy + sit, 78, 35 - tap, ARM_R[2], ARM_R[3], hexc(ARM_FILL))
        else:
            self._rect(cr, ox, oy + sit, *ARM_L, hexc(ARM_FILL))
            self._rect(cr, ox, oy + sit, *ARM_R, hexc(ARM_FILL))

        if pose in ("code", "work"):
            for sx, sy, sw, sh in SCREEN:
                self._rect(cr, ox, oy + sit, sx, sy, sw, sh, hexc("#6E7987"))
            for i, (tx, ty) in enumerate(SCREEN_TEXT):
                if (self.frame // 3 + i) % 4:
                    self._rect(cr, ox, oy + sit, tx, ty, 3, 3, hexc("#F2F2F2"))
            self._rect(cr, ox, oy + sit, *KEYS_BASE[:4], hexc(KEYS_BASE[4]))
            for i, (kx, ky) in enumerate(KEYS):
                col = hexc("#F2F2F2") if (self.frame + i * 2) % 5 < 2 else hexc("#7C8CA0")
                self._rect(cr, ox, oy + sit, kx, ky, 4, 2, col)
        if pose == "music":
            for x, y, w, h, col in HEADPHONES:
                self._rect(cr, ox, oy + sit, x, y, w, h, hexc(col))
        if pose == "sleep":
            cr.set_source_rgb(*ORANGE); cr.set_font_size(16)
            zz = int(self.frame / 12) % 3 + 1
            cr.move_to(ox + 70 * SCALE, oy + sit - 6 * SCALE - zz * 4)
            cr.show_text("z" * zz)

    def _on_draw(self, _w, cr) -> bool:
        cr.set_source_rgba(0, 0, 0, 0); cr.set_operator(cairo.OPERATOR_SOURCE); cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self._draw_bubble(cr)
        oy = 175 + int(3 * math.sin(self.frame / 7)) - self.bounce
        self._draw_clawd(cr, oy)
        return False

    # ---------- animación ----------
    def _tick(self) -> bool:
        self.frame += 1
        if self.bounce > 0:
            self.bounce -= 1
        if self.mode == "typing" and self.shown < len(self.full_text):
            self.shown = min(len(self.full_text), self.shown + 2)
            if self.shown >= len(self.full_text):
                self.mode = "idle"
        if self.frame % random.randint(60, 120) == 0:
            self.blink = True; GLib.timeout_add(140, self._unblink)
        self.area.queue_draw()
        return True

    def _unblink(self) -> bool:
        self.blink = False
        return False

    # ---------- interacción ----------
    def _on_press(self, _w, event) -> None:
        if event.button == 3:
            Gtk.main_quit()
        elif event.button == 1:
            self.drag = (int(event.x_root), int(event.y_root)); self._react("¡Me moviste!", 0.5)

    def _on_release(self, _w, event) -> None:
        if event.button == 1 and self.drag:
            self.drag = None; self._react("¡Gracias por llevarme!", 0.4)

    def _on_motion(self, _w, event) -> None:
        if self.drag:
            dx = int(event.x_root) - self.drag[0]; dy = int(event.y_root) - self.drag[1]
            x, y = self.get_position(); self.move(x + dx, y + dy)
            self.drag = (int(event.x_root), int(event.y_root))

    def _on_enter(self, _w, _e) -> None:
        if not self.drag and time.monotonic() > self.pet_cooldown:
            self._react(random.choice(PET_PHRASES), 1.2)

    def _react(self, text: str, seconds: float) -> None:
        self.pet_cooldown = time.monotonic() + seconds
        self.happy_until = time.monotonic() + seconds
        self.quiet_until = time.monotonic() + seconds + 4
        self.full_text = text; self.shown = len(text); self.mode = "idle"; self.bounce = 12
        threading.Thread(target=_say_worker, args=(text,), daemon=True).start()

    def _type(self, text: str, voice: bool = False) -> None:
        self.full_text = text; self.shown = 0; self.mode = "typing"; self.bounce = 10
        if voice:
            threading.Thread(target=_say_worker, args=(text,), daemon=True).start()

    def _on_send(self, _entry) -> None:
        prompt = self.entry.get_text().strip()
        if not prompt:
            return
        self.entry.set_text("")
        self.quiet_until = time.monotonic() + 30
        quick = local_command(prompt)
        if quick is not None:
            self.full_text = quick; self.shown = len(quick); self.mode = "idle"; self.bounce = 10
            return
        if prompt.startswith("!") or "jarvis" in prompt.lower():
            self.mode = "thinking"
            threading.Thread(target=lambda: GLib.idle_add(self._type, agent_ask(prompt.lstrip("!"))), daemon=True).start()
            return
        self.mode = "thinking"
        self.history.append({"role": "user", "content": prompt})
        def _run():
            reply = ollama_ask(prompt, self.history)
            self.history.append({"role": "assistant", "content": reply})
            GLib.idle_add(self._type, reply, True)
        threading.Thread(target=_run, daemon=True).start()
        # (la voz se lanza cuando llega la respuesta)

    def _sync(self) -> bool:
        if self.mode != "idle" or self.idle > 60000 or time.monotonic() < self.quiet_until:
            return True
        try:
            con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
            row = con.execute(
                """select json_extract(p.data,'$.text') from part p join message m on p.message_id=m.id
                   where json_extract(p.data,'$.type')='text' and json_extract(m.data,'$.role')='assistant'
                   and length(coalesce(json_extract(p.data,'$.text'),''))>0
                   order by p.time_created desc limit 1""").fetchone()
            con.close()
        except Exception:  # noqa: BLE001
            return True
        text = row[0] if row else None
        if text and text != self.last_sync:
            self.last_sync = text
            self._type("📣 " + clean(text))
        return True


if __name__ == "__main__":
    win = Clawd()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
