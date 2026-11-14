"""Mini-agente de texto con tool use (Sesion 9).

Uso:
    python agent.py                      # chat interactivo con memoria
    python agent.py "tira un dado de 20 caras"   # una sola pregunta
"""
import os
import sys

import anthropic
from dotenv import load_dotenv

from tools import TOOLS, run_tool

load_dotenv()

# La consola de Windows usa cp1252 y falla con emojis/acentos: forzamos UTF-8.
for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

MODEL = os.environ.get("AGENT_MODEL", "claude-haiku-5-5")
MAX_STEPS = 5  # tope de vueltas del ciclo, para que nunca quede en bucle

SYSTEM_PROMPT = """\
Eres Edy, el asistente de una plataforma de cursos de marketing digital e IA.
Tu tarea es ayudar a encontrar cursos del catalogo.

- Responde sobre cursos SOLO con datos devueltos por la herramienta search_courses.
  Nunca inventes cursos, lecciones, precios ni resenas.
- Maximo 3 cursos por respuesta, cada uno con titulo, una frase y su enlace.
- Escribe el enlace EXACTAMENTE como lo devuelve la herramienta (por ejemplo /cursos/demo-4),
  sin agregar dominios ni "https://".
- Si no hay resultados, dilo con honestidad y sugiere reformular la busqueda.
- No procesas pagos ni inscribes a nadie. Para inscribirse: "entra al curso desde /cursos
  y usa el boton de inscripcion; si no tienes cuenta, crea una en /registro".
- Si la persona pide tirar un dado, usa roll_die.
- Si la pregunta no tiene que ver con cursos, responde con calidez que solo puedes ayudar con eso.
Tono: cercano, claro y entusiasta; sin ventas agresivas.
"""

client = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno


def run_agent(messages: list) -> str:
    """Ciclo del agente. `messages` se modifica para conservar la memoria de la charla."""
    for _ in range(MAX_STEPS):
        # 1) Le describimos las herramientas a Claude y le pasamos la conversacion.
        response = client.messages.create(
            model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT, tools=TOOLS, messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})

        # 2) Si no pidio ninguna herramienta, esta es la respuesta final.
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        # 3) Pidio herramientas: las ejecutamos NOSOTROS y devolvemos el resultado.
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [herramienta] {block.name}({block.input})")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,  # debe coincidir con el id de la peticion
                    "content": run_tool(block.name, block.input),
                })
        messages.append({"role": "user", "content": results})
        # 4) Volvemos al paso 1: Claude lee el resultado y redacta su respuesta.

    return "No pude completar la respuesta, intenta reformular tu pregunta."


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Falta ANTHROPIC_API_KEY. Copia .env.example a .env y completalo.")

    if len(sys.argv) > 1:
        print(run_agent([{"role": "user", "content": " ".join(sys.argv[1:])}]))
        return

    print("Edy (escribe 'salir' para terminar)")
    history: list = []
    while True:
        try:
            text = input("\nTu: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in {"salir", "exit", "quit"}:
            break
        if text:
            history.append({"role": "user", "content": text})
            print("\nEdy:", run_agent(history))


if __name__ == "__main__":
    main()
