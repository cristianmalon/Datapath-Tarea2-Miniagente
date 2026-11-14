# Mini-agente de texto (Sesión 9)

Agente "Edy" de texto con *tool use*, basado en el de la Sesión 8, pero autónomo:
funciona solo (catálogo de muestra) o conectado a Eduplatform con `PLATFORM_URL`.

## Cómo correrlo
```bash
cp .env.example .env        # y pega tu ANTHROPIC_API_KEY
.venv/Scripts/python agent.py                       # chat con memoria
.venv/Scripts/python agent.py "tira un dado de 20 caras"
```

## El ciclo (agent.py → `run_agent`)
1. Se describen las herramientas a la API de Claude (`tools.py → TOOLS`).
2. Si el modelo responde con `stop_reason == "tool_use"`, **pide** usar una herramienta.
3. **Nuestro código** la ejecuta (`run_tool`) y devuelve un `tool_result` con el mismo `tool_use_id`.
4. Claude lee el resultado y redacta la respuesta final. `MAX_STEPS` evita bucles.

El modelo nunca ejecuta nada: solo pide. Por eso con MCP tú controlas los permisos.

## Pruebas para mostrar
| Mensaje | Esperado |
|---|---|
| `tira un dado de 20 caras` | usa `roll_die` y muestra el número |
| `cuéntame un chiste` | responde sin herramientas (o dice que solo ayuda con cursos) |
| `¿tienes algo para vender por redes sociales?` | usa `search_courses` y recomienda cursos con enlace |
| `¿cuánto cuesta el curso de IA?` | no inventa precios |
