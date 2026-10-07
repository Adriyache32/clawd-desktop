# Clawd — mascota de escritorio de Claude Code

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
| menos de 6 GB | `qwen2.5:0.5b` | ~0.4 GB |
| 6–12 GB | `qwen2.5:1.5b` | ~1.0 GB |
| 12–20 GB | `qwen2.5:3b` | ~2.0 GB |
| más de 20 GB | `gemma3:4b` | ~3.3 GB |
| equipo potente | `qwen2.5:7b` | ~4.7 GB |

> El modelo **no se queda en RAM**: Ollama lo descarga 30 s después de la última respuesta, así que puedes jugar o trabajar sin que ocupe memoria.

## Dependencias

- **Python 3.11+** con `python-gobject` (PyGObject) y `python-cairo`
- **GTK3** (para la ventana y la transparencia)
- **X11 con compositor** (en XFCE: `xfwm4` con *use_compositing = true*)
- Opcionales: `xprintidle` (para dormir), `playerctl` (audífonos), ImageMagick/`import` (capturas), `xdotool` (control)
- Opcional: **Ollama** para las respuestas (el instalador lo instala si falta)

## Instalación

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

Interacción: **pasar el cursor** (la acaricias), **clic y arrastrar** para moverla, **clic derecho** para cerrarla.

## Cómo está hecho

- Sprite pixel-art **original** de Claude Code (mismo que la terminal), reconstruido en cairo.
- Estados: `idle`, `code` (sentado teclenado), `work`, `think`, `sleep`, `music`, `happy`.
- Sensores: `xprintidle` (sueño), `playerctl` (audio), tiempo de inactividad de OpenCode (trabajo), RCON de Minecraft (jugadores).

## Licencia

MIT. Clawd es un personaje de Anthropic; este proyecto es un homenaje no oficial.
