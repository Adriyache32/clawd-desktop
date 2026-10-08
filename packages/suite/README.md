# @clawd/suite

El instalador de **terminal** (funciona sin navegador y sin internet permanente) que monta todo: dependencias, Ollama, la mascota y **LobeChat** como interfaz de chat local.

## Qué incluye

- **`install.sh`** — menú de terminal (`gum` o `whiptail`) con:
  - Instalar todo (Clawd + Ollama + LobeChat)
  - Instalar Clawd (consola)
  - Instalar LobeChat
  - Elegir modelo (local o nube, con estrellas de "inteligencia")
  - Ver estado · Desinstalar
  - Instalador web *(opcional, requiere navegador)*
- **`webui.py` + `webui.html`** — instalador web opcional en `127.0.0.1:8765`.

## Uso

```bash
cd packages/suite
./install.sh
```

El instalador copia la mascota desde `../mascot/claude-mascot.py`, crea el servicio de usuario y el autostart, y arranca.

## LobeChat (interfaz offline)

```bash
podman run -d --name lobe-chat --network host \
  -e OLLAMA_PROXY_URL=http://127.0.0.1:11434 \
  docker.io/lobehub/lobe-chat:latest
```

Queda en `http://localhost:3210`, hablando con tus modelos locales de Ollama. Solo la primera descarga necesita conexión.
