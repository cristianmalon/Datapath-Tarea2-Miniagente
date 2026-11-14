"""Herramientas del mini-agente.

Dos herramientas:
  - search_courses: busca cursos. Usa Eduplatform (PLATFORM_URL) si esta disponible
    y, si no, un catalogo de MUESTRA local para que el agente funcione solo.
  - roll_die: tira un dado de N caras (la herramienta de la tarea del Lab 9).

IMPORTANTE: el modelo nunca ejecuta nada; solo PIDE usar una herramienta.
Aqui esta el codigo que de verdad se ejecuta, y tu decides que se permite.
"""
import json
import os
import random
import unicodedata

import httpx

PLATFORM_URL = os.environ.get("PLATFORM_URL", "").rstrip("/")

# Catalogo de MUESTRA (datos de demostracion, no son los cursos reales de Eduplatform).
SAMPLE_CATALOG = [
    {"id": "demo-1", "title": "Marketing Digital desde Cero",
     "description": "Fundamentos de marketing digital: embudo, canales y metricas basicas.",
     "url": "/cursos/demo-1"},
    {"id": "demo-2", "title": "Vender por Redes Sociales",
     "description": "Estrategia de contenido, Instagram y TikTok para vender productos.",
     "url": "/cursos/demo-2"},
    {"id": "demo-3", "title": "Publicidad en Meta y Google Ads",
     "description": "Crea y optimiza campanas pagadas con presupuesto pequeno.",
     "url": "/cursos/demo-3"},
    {"id": "demo-4", "title": "IA Generativa para Principiantes",
     "description": "Que es la IA generativa y como usar ChatGPT y Claude en el trabajo diario.",
     "url": "/cursos/demo-4"},
    {"id": "demo-5", "title": "Agentes de IA con Claude Code",
     "description": "Construye agentes que usan herramientas, specs y skills.",
     "url": "/cursos/demo-5"},
    {"id": "demo-6", "title": "Programacion para Principiantes",
     "description": "Aprende a programar paso a paso con Python y proyectos pequenos.",
     "url": "/cursos/demo-6"},
]


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _search_local(query: str) -> dict:
    q = _norm(query).replace("inteligencia artificial", "ia").replace("artificial intelligence", "ia")
    stop = {"de", "la", "el", "en", "un", "una", "por", "para", "con", "los", "las", "que", "del",
            "al", "y", "o", "a", "cursos", "curso", "quiero", "algo", "tienes", "hay"}
    words = [w for w in q.replace(",", " ").replace("?", " ").split() if len(w) >= 2 and w not in stop]
    scored = []
    for course in SAMPLE_CATALOG:
        haystack = _norm(course["title"] + " " + course["description"])
        tokens = set(haystack.replace(".", " ").replace(",", " ").split())
        # palabras cortas (ia, ads) deben coincidir completas para no dar falsos positivos
        score = sum(1 for w in words if (w in tokens if len(w) <= 3 else w in haystack))
        if score:
            scored.append((score, course))
    scored.sort(key=lambda x: -x[0])
    return {"source": "catalogo_de_muestra", "courses": [c for _, c in scored[:5]]}


def search_courses(query: str) -> dict:
    if PLATFORM_URL:
        try:
            r = httpx.get(f"{PLATFORM_URL}/api/courses/search", params={"q": query}, timeout=10)
            r.raise_for_status()
            data = r.json()
            return {"source": "eduplatform", "courses": data.get("results") or data.get("courses") or []}
        except (httpx.HTTPError, ValueError):
            pass  # si la plataforma no responde, usamos el catalogo de muestra
    return _search_local(query)


def roll_die(sides: int) -> dict:
    sides = int(sides)
    if sides < 2 or sides > 1000:
        return {"error": "El dado debe tener entre 2 y 1000 caras."}
    return {"sides": sides, "result": random.randint(1, sides)}


# Descripcion de las herramientas para la API de Claude: es lo que el modelo "lee"
# para decidir cuando usarlas.
TOOLS = [
    {
        "name": "search_courses",
        "description": (
            "Busca en el catalogo los cursos mas relevantes para lo que la persona quiere aprender. "
            "Devuelve id, title, description y url de cada curso."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string",
                          "description": "Lo que la persona quiere aprender, en lenguaje natural."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "roll_die",
        "description": "Tira un dado de N caras y devuelve el resultado. Usalo solo si la persona pide tirar un dado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sides": {"type": "integer", "minimum": 2, "description": "Numero de caras del dado."}
            },
            "required": ["sides"],
        },
    },
]

IMPLEMENTATIONS = {"search_courses": search_courses, "roll_die": roll_die}


def run_tool(name: str, args: dict) -> str:
    """Ejecuta la herramienta pedida por el modelo (con control de errores)."""
    impl = IMPLEMENTATIONS.get(name)
    if impl is None:
        return json.dumps({"error": f"Herramienta desconocida: {name}"}, ensure_ascii=False)
    try:
        return json.dumps(impl(**args), ensure_ascii=False)
    except Exception as exc:  # noqa: BLE001 - devolvemos el error al modelo en vez de romper
        return json.dumps({"error": str(exc)}, ensure_ascii=False)
