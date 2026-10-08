#!/usr/bin/env python3
"""Clawd · instalador con interfaz web local (solo 127.0.0.1)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOME = Path.home()
SRC = Path(__file__).resolve().parent
MASCOT_SRC = SRC.parent / "mascot" / "claude-mascot.py"
ROOT = SRC.parent.parent
APP = HOME / ".local" / "bin" / "claude-mascot.py"
UNIT = HOME / ".config" / "systemd" / "user" / "claude-mascot.service"
AUTOSTART = HOME / ".config" / "autostart" / "claude-mascot.desktop"
PORT = int(os.environ.get("CLAWD_WEBUI_PORT", "8765"))

MODELS = [
    ("qwen2.5:0.5b", "~0.4 GB", "mínimo"),
    ("qwen2.5:1.5b", "~1.0 GB", "equilibrado"),
    ("qwen2.5:3b", "~2.0 GB", "buena calidad"),
    ("gemma3:4b", "~3.3 GB", "más listo"),
    ("qwen2.5:7b", "~4.7 GB", "el más capaz"),
]


def run(cmd, timeout=600):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except Exception as exc:  # noqa: BLE001
        return 1, f"{type(exc).__name__}: {exc}"


def has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def ram_gb() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemTotal"):
            return round(int(line.split()[1]) / 1048576, 1)
    return 0.0


def recommend() -> str:
    r = ram_gb()
    if r < 6:
        return "qwen2.5:0.5b"
    if r < 12:
        return "qwen2.5:1.5b"
    if r < 20:
        return "qwen2.5:3b"
    return "qwen2.5:7b"


def detect_pm() -> str:
    for pm in ("pacman", "apt", "dnf", "zypper"):
        if has(pm):
            return pm
    return ""


def pkgs() -> list[str]:
    return {
        "pacman": ["python-gobject", "python-cairo", "gtk3", "xorg-xprintidle", "playerctl", "imagemagick", "xdotool"],
        "apt": ["python3-gi", "python3-cairo", "gir1.2-gtk-3.0", "xprintidle", "playerctl", "imagemagick", "xdotool"],
        "dnf": ["python3-gobject", "python3-cairo", "gtk3", "xprintidle", "playerctl", "ImageMagick", "xdotool"],
    }.get(detect_pm(), [])


def status() -> dict:
    deps = subprocess.run(["python3", "-c", "import gi,cairo"], capture_output=True).returncode == 0
    svc = run(["systemctl", "--user", "is-active", "claude-mascot.service"])[1].strip()
    models = []
    if has("ollama"):
        rc, out = run(["ollama", "list"])
        for line in out.splitlines()[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
    return {
        "deps_ok": deps, "deps_missing": (not deps),
        "ollama": has("ollama"), "ram": ram_gb(), "recommend": recommend(),
        "service": svc or "apagada", "installed": APP.exists(),
        "models": models, "pm": detect_pm(), "port": PORT,
    }


def install_deps() -> str:
    pm = detect_pm()
    if not pm:
        return "No reconozco tu gestor de paquetes."
    cmd = {"pacman": ["pkexec", "pacman", "-S", "--needed", "--noconfirm", *pkgs()],
           "apt": ["pkexec", "sh", "-c", "apt-get update && apt-get install -y " + " ".join(pkgs())],
           "dnf": ["pkexec", "dnf", "install", "-y", *pkgs()]}[pm]
    rc, out = run(cmd)
    return "Dependencias instaladas." if rc == 0 else f"Falló: {out.strip()[:300]}"


def install_ollama() -> str:
    rc, out = run(["pkexec", "sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"])
    if rc == 0:
        run(["systemctl", "--user", "enable", "--now", "ollama"])
        return "Ollama instalado."
    return f"Falló: {out.strip()[:300]}"


def pull(model: str) -> str:
    if not has("ollama"):
        return "Ollama no está instalado."
    rc, out = run(["ollama", "pull", model], timeout=3600)
    return f"Modelo {model} listo." if rc == 0 else f"Falló: {out.strip()[:300]}"


def install_files(model: str, api: str = "ollama") -> str:
    APP.parent.mkdir(parents=True, exist_ok=True)
    UNIT.parent.mkdir(parents=True, exist_ok=True)
    AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MASCOT_SRC, APP)
    APP.chmod(0o755)
    UNIT.write_text(f"""[Unit]
Description=Clawd - mascota de escritorio de Claude Code
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {APP}
Environment=MASCOT_OLLAMA_MODEL={model}
Environment=MASCOT_API={api}
PassEnvironment=DISPLAY XAUTHORITY
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
""")
    AUTOSTART.write_text(f"""[Desktop Entry]
Type=Application
Name=Clawd
Comment=Mascota de escritorio de Claude Code
Exec=/usr/bin/python3 {APP}
Terminal=false
Categories=Utility;
""")
    run(["systemctl", "--user", "daemon-reload"])
    run(["systemctl", "--user", "enable", "claude-mascot.service"])
    return "Instalado."


def start_app() -> str:
    run(["systemctl", "--user", "import-environment", "DISPLAY", "XAUTHORITY"])
    rc, out = run(["systemctl", "--user", "restart", "claude-mascot.service"])
    return "Clawd está corriendo." if rc == 0 else f"No arrancó: {out.strip()[:200]}"


def stop_app() -> str:
    run(["systemctl", "--user", "stop", "claude-mascot.service"])
    return "Clawd detenida."


def uninstall() -> str:
    run(["systemctl", "--user", "disable", "--now", "claude-mascot.service"])
    for f in (UNIT, AUTOSTART, APP):
        f.unlink(missing_ok=True)
    run(["systemctl", "--user", "daemon-reload"])
    return "Desinstalado."


def act(action: str, body: dict) -> str:
    if action == "deps":
        return install_deps()
    if action == "ollama":
        return install_ollama()
    if action == "pull":
        return pull(body.get("model", recommend()))
    if action == "install":
        return install_files(body.get("model", recommend()), body.get("api", "ollama"))
    if action == "start":
        return start_app()
    if action == "stop":
        return stop_app()
    if action == "uninstall":
        return uninstall()
    return "acción desconocida"


PAGE = Path(__file__).with_name("webui.html")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_a) -> None:  # silencio
        pass

    def do_GET(self) -> None:
        if self.path.startswith("/api/status"):
            self._send(200, json.dumps(status()).encode(), "application/json")
        elif self.path.startswith("/clawd.png"):
            img = (ROOT / "clawd-official.png").read_bytes()
            self._send(200, img, "image/png")
        else:
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        action = self.path.rsplit("/", 1)[-1]
        result = act(action, body)
        self._send(200, json.dumps({"ok": True, "message": result,
                                    "status": status()}).encode(), "application/json")


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Clawd installer web en {url}")
    if os.environ.get("CLAWD_NO_BROWSER") != "1":
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
