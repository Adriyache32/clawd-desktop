# Clawd Desktop

Mascota de escritorio de Claude Code + suite de instalación con modelos locales (offline) y en la nube.

## Paquetes

| Paquete | Qué es | Cómo se usa |
|---|---|---|
| [`packages/mascot`](packages/mascot) | La mascota (Python, GTK3) | `python3 packages/mascot/claude-mascot.py` |
| [`packages/suite`](packages/suite) | Instalador de terminal + LobeChat + web UI opcional | `cd packages/suite && ./install.sh` |
| [`packages/normal`](packages/normal) | Perfil **equilibrado** (modelo decente, voz, sin recortes) | `cd packages/normal && ./apply.sh` |
| [`packages/optimized`](packages/optimized) | Perfil **optimizado** (poca RAM, sin voz, se libera al instante) | `cd packages/optimized && ./apply.sh` |


Clawd es el bicho naranja pixelado de Claude Code, pero vivo en tu escritorio: flota **sin fondo**, se sienta a teclear en una laptop cuando trabajas, duerme si no usas la PC, se pone audífonos si hay música, y te habla con un modelo **local** (Ollama). Además actúa de ayudante: abre apps, busca en el navegador y puede pasar órdenes a un agente.

![Clawd](clawd-official.png)

## Requisitos reales (medidos, no estimados)

| Recurso | Consumo | Cuándo |
|---|---|---|
| Código | **20 KB** | un solo archivo Python |
| RAM de la mascota | **~8 MB** reposo · **~47 MB** pico | siempre que está abierta |
| RAM del modelo | **0.4–4.7 GB** según modelo | **solo mientras chateas**; se descarga a los 30 s |
| Disco — app | 20 KB | fijo |
| Disco — dependencias | ~60–80 MB | suelen venir preinstaladas |
| Disco — Ollama | 38 MB (binario) | opcional |
| Disco — modelo | 0.4 GB (`0.5b`) a 4.7 GB (`7b`) | opcional, elegible |

**Medición:** `ps -o rss` sobre el proceso en reposo y el pico que reporta systemd (`Memory peak`) tras varias horas.

### Recomendación de modelo según tu RAM

El instalador la calcula sola:

| RAM total | Modelo sugerido | RAM en uso |
|---|---|---|
| Modelo | RAM en uso | Inteligencia |
|---|---|---|
| `qwen2.5:0.5b` | ~0.4 GB | ★☆☆☆☆ muy básico |
| `qwen2.5:1.5b` | ~1.0 GB | ★★☆☆☆ básico |
| `qwen3:1.7b` | ~1.4 GB | ★★☆☆☆ básico |
| `qwen2.5:3b` | ~2.0 GB | ★★★☆☆ aceptable |
| `qwen3:4b` | ~2.7 GB | ★★★☆☆ aceptable |
| `gemma3:4b` | ~3.3 GB | ★★★☆☆ multimodal |
| `llama3.1:8b` | ~4.7 GB | ★★★★☆ bueno |
| `deepseek-r1:8b` | ~5.0 GB | ★★★★☆ razona paso a paso |
| `qwen3:8b` | ~5.2 GB | ★★★★☆ de los mejores |
| `gemma3:12b` | ~8.1 GB | ★★★★★ muy capaz |
| `phi4:14b` | ~9.1 GB | ★★★★★ denso y listo |
| `qwen3:14b` | ~9.3 GB | ★★★★★ el más completo |
| `kimi-k3:cloud` | nube | ★★★★★ Kimi K3 (remoto, requiere `ollama signin`) |
| `nvidia/nemotron-3-ultra-550b-a55b` | nube | ★★★★★ Nemotron 3 Ultra (NVIDIA API) |
| `nvidia/nemotron-3-super-120b-a12b` | nube | ★★★★★ Nemotron 3 Super (NVIDIA API) |

### Backend NVIDIA (nube)

Para los Nemotron, guarda tu clave en `~/.config/clawd/nvidia.key` (permisos 600) o define `MASCOT_NVIDIA_KEY`. La mascota la lee sola y llama a `integrate.api.nvidia.com`. No consume tu RAM.

Cualquier otro modelo de Ollama también sirve: elige "Otro" y escribe su nombre.

> El modelo **no se queda en RAM**: Ollama lo descarga 30 s después de la última respuesta.

### 🛡️ Regulador de RAM (automático)

Aunque elijas un modelo grande, **Clawd cuida tu RAM** mirando la memoria libre antes de cada respuesta:

| RAM libre | Qué hace |
|---|---|
| más de 3 GB | usa tu modelo elegido, contexto 2048, lo libera a los 30 s |
| 1.6–3 GB | baja a un modelo más chico, contexto 1024, libera a los 10 s |
| 0.7–1.6 GB | usa el más pequeño (0.5b), contexto 512, libera al instante |
| menos de 0.7 GB | no carga ningún modelo (modo ahorro) |

Te avisa en la burbuja cuando entra en modo ahorro, así nunca te sorprende.

## Dependencias

- **Python 3.11+** con `python-gobject` (PyGObject) y `python-cairo`
- **GTK3** (para la ventana y la transparencia)
- **X11 con compositor** (en XFCE: `xfwm4` con *use_compositing = true*)
- Opcionales: `xprintidle` (para dormir), `playerctl` (audífonos), ImageMagick/`import` (capturas), `xdotool` (control)
- Opcional: **Ollama** para las respuestas (el instalador lo instala si falta)

## Instalación (todo, paso a paso)

```bash
git clone https://github.com/Adriyache32/clawd-desktop
cd clawd-desktop/packages/suite
./install.sh
```

El instalador es un **menú de terminal** (funciona sin navegador). La opción **“Instalar todo”** hace:

1. **Dependencias** del sistema (GTK, python-gobject, etc.).
2. **Ollama** (si falta) — cerebro local para uso **sin internet**.
3. **Clawd** — la mascota, con servicio y autostart.
4. **LobeChat** — interfaz de chat en `http://localhost:3210`, conectada a tus modelos locales.

Solo la primera descarga (modelos, imagen de LobeChat) necesita conexión; después funciona offline.

## LobeChat (interfaz de chat)

Si prefieres una interfaz tipo ChatGPT pero 100% local, el instalador levanta LobeChat con Docker/Podman:

```bash
podman run -d --name lobe-chat --network host \
  -e OLLAMA_PROXY_URL=http://127.0.0.1:11434 docker.io/lobehub/lobe-chat:latest
```

Queda en `http://localhost:3210` y usa tus modelos de Ollama sin internet.

## Instalación (detalle)

```bash
git clone <tu-repo>/clawd-desktop
cd clawd-desktop
./install.sh
```

El instalador abre un **menú** que:

1. **Comprueba dependencias** e intenta instalarlas con tu gestor (`pacman`/`apt`/`dnf`).
2. **Detecta Ollama**; si no está, ofrece instalarlo.
3. **Recomienda un modelo** según tu RAM y permite elegir otro.
4. Copia la app, crea el servicio de usuario y el autostart, y la arranca.

Opciones del menú: instalar, elegir modelo, comprobar dependencias, ver estado, desinstalar.

## Uso

Escribe en la barra de abajo:

- Preguntas libres → responde el modelo (local).
- `abre youtube` / `spotify` / `terminal` / `archivos` / `navegador` / `calculadora`
- `busca <tema>` o `investiga <tema>` → abre el navegador
- `sube/baja volumen`, `captura`, `bloquea`, `cuantos juegan`, `ayuda`
- `! <orden>` → se la pasa al **agente**, que sí puede tocar tu PC
- Palabras como `audita`, `pentest` o `seguridad` van solas al agente con las **skills Hermes/Strix**

Interacción: **pasar el cursor** (la acaricias), **clic y arrastrar** para moverla, **clic derecho** para cerrarla.

## Voz (TTS opcional)

Clawd puede **hablar** lo que responde. Backends, en orden de calidad/peso:

| Backend | Peso | Calidad | Notas |
|---|---|---|---|
| **espeak-ng** | 0 (ya instalado) | robótica | funciona al instante; `MASCOT_TTS=espeak` |
| **Piper** | ~150 MB | buena, natural | `pip install piper-tts` + voz en español |
| **Pocket-TTS** | ~2 GB (arrastra PyTorch) | muy buena + clona voz | `pip install "pocket-tts[audio]"` |

Se autodetecta: si `pocket_tts` o `piper` están instalados los usa; si no, cae a `espeak-ng`. Controla con `MASCOT_TTS=auto|espeak|piper|pocket|off`. Comandos en la mascota: `calla` y `habla`.

## Cómo está hecho

- Sprite pixel-art **original** de Claude Code (mismo que la terminal), reconstruido en cairo.
- Estados: `idle`, `code` (sentado teclenado), `work`, `think`, `sleep`, `music`, `happy`.
- Sensores: `xprintidle` (sueño), `playerctl` (audio), tiempo de inactividad de OpenCode (trabajo), RCON de Minecraft (jugadores).

## Licencia

MIT. Clawd es un personaje de Anthropic; este proyecto es un homenaje no oficial.
