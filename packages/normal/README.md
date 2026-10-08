# @clawd/profile-normal

Perfil **equilibrado** para Clawd Desktop. Es el comportamiento por defecto: usa un modelo decente y deja la voz activada, sin recortes automáticos.

## Qué configura

| Variable | Valor | Efecto |
|---|---|---|
| `MASCOT_OLLAMA_MODEL` | `qwen2.5:1.5b` | modelo local equilibrado |
| `MASCOT_RAM_GUARD` | `off` | no baja de modelo automáticamente |
| `MASCOT_KEEP` | `30s` | libera el modelo a los 30 s |
| `MASCOT_CTX` | `2048` | contexto amplio |
| `MASCOT_FPS` | `55` | animación fluida |
| `MASCOT_TTS` | `espeak` | habla con voz |

## Aplicar

```bash
./apply.sh
```

Escribe `~/.config/clawd/profile.env` y reinicia el servicio de Clawd.

Para PCs con RAM de sobra. Si vas justo de memoria, usa **`@clawd/profile-optimized`**.
