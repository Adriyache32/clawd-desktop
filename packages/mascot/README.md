# @clawd/mascot

La mascota de escritorio: un solo archivo Python que dibuja a Clawd (pixel-art original de Claude Code) sobre GTK3 + cairo, sin fondo, con animaciones, voz y un cerebro local o en la nube.

## Qué es

- **`claude-mascot.py`** — la app completa (~20 KB).
- Ventana transparente always-on-top, arrastrable, con burbuja de cómic.
- Poses: `idle`, `code` (sentado tecleando), `sleep`, `music`, `happy`.
- Reacciona al cursor (acariciar/mover/soltar).
- Habla con **Ollama** (local), **NVIDIA** o **Ollama Cloud**.
- **Regulador de RAM**: adapta modelo, contexto y `keep_alive` a la memoria libre.
- Voz opcional: **Piper** (natural, por defecto si está), espeak-ng (robótica) o Pocket-TTS.

## Requisitos

- Python 3.11+ con `python-gobject` y `python-cairo`, GTK3 y un compositor X11.
- Opcional: `xprintidle`, `playerctl`, `imagemagick`, `xdotool`, Ollama.

## Uso directo

```bash
python3 claude-mascot.py
```

Variables: `MASCOT_OLLAMA_MODEL`, `MASCOT_API=ollama|nvidia|auto`, `MASCOT_OLLAMA`,
`MASCOT_NVIDIA_KEY` (o `~/.config/clawd/nvidia.key`), `MASCOT_TTS`, `MASCOT_VOICE`.

La instalación y el servicio systemd los maneja el paquete **`suite`**.
