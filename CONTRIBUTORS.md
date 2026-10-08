# Contribuidores

Gracias a quienes hacen posible Clawd Desktop.

## Autor / mantenedor
- **Adriyache32** — idea, hardware de pruebas, dirección del proyecto.

## Contribución de IA
- **OpenCode** (agente de terminal, modelo `deepseek-v4.1-flash` del plan OpenCode Go) — escritura del código, diseño de la mascota, instalador, web UI y documentación. Co-autor de los commits vía `Co-authored-by`.
- **Claude (Anthropic)** — origen del personaje **Clawd** y base del proyecto; crédito a Anthropic por el diseño del sprite.

## Proyectos y voces de terceros
- **Anthropic** — personaje Clawd (homenaje no oficial).
- **rhasspy/piper-voices** — voces de Piper (`es_MX-claude-high`).
- **Ollama**, **LobeChat (LobeHub)**, **NVIDIA NIM**, **ElevenLabs** — motores de modelo/chat/voz integrados.

---

### Cómo acreditar a la IA en tus commits

GitHub muestra co-autores si el correo va ligado a una cuenta. Para dejar la atribución en el historial:

```bash
git commit -m "mensaje

Co-authored-by: OpenCode <noreply@opencode.ai>"
```

O con git-trailer:

```bash
git commit --trailer "Co-authored-by: OpenCode <noreply@opencode.ai>" -m "mensaje"
```

> Nota: como OpenCode no tiene cuenta de GitHub, aparece en el mensaje del commit, pero no en la lista de *Contributors* del repo. Para eso haría falta una cuenta real y agregarla en `Settings → Collaborators`.
