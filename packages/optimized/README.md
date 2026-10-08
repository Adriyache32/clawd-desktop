# @clawd/profile-optimized

Perfil **optimizado** para Clawd Desktop: pensado para PCs con poca RAM o cuando juegas/compilas con la mascota abierta. Consume lo mínimo.

## Qué configura

| Variable | Valor | Efecto |
|---|---|---|
| `MASCOT_OLLAMA_MODEL` | `qwen2.5:0.5b` | el modelo más liviano (~0.4 GB) |
| `MASCOT_RAM_GUARD` | `on` | baja de modelo si la RAM libre es poca |
| `MASCOT_KEEP` | `0s` | descarga el modelo al instante tras responder |
| `MASCOT_CTX` | `512` | contexto mínimo |
| `MASCOT_FPS` | `25` | animación leve (menos CPU) |
| `MASCOT_SYNC` | `30000` | casi no consulta la sesión de OpenCode |
| `MASCOT_TTS` | `off` | sin voz (ahorra CPU) |

## Aplicar

```bash
./apply.sh
```

Escribe `~/.config/clawd/profile.env` y reinicia el servicio de Clawd.

Ideal para equipos de 4–8 GB. Si tienes RAM de sobra y quieres mejor calidad, usa **`@clawd/profile-normal`**.
