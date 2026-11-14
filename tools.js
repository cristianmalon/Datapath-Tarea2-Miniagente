// Herramientas del mini-agente: search_courses y roll_die.
// El modelo nunca ejecuta nada; solo PIDE usar una herramienta. Aqui esta el codigo que se ejecuta.

const PLATFORM_URL = (process.env.PLATFORM_URL ?? "").replace(/\/+$/, "");

// Catalogo de MUESTRA (datos de demostracion, no son los cursos reales de Eduplatform).
const SAMPLE_CATALOG = [
  { id: "demo-1", title: "Marketing Digital desde Cero",
    description: "Fundamentos de marketing digital: embudo, canales y metricas basicas.", url: "/cursos/demo-1" },
  { id: "demo-2", title: "Vender por Redes Sociales",
    description: "Estrategia de contenido, Instagram y TikTok para vender productos.", url: "/cursos/demo-2" },
  { id: "demo-3", title: "Publicidad en Meta y Google Ads",
    description: "Crea y optimiza campanas pagadas con presupuesto pequeno.", url: "/cursos/demo-3" },
  { id: "demo-4", title: "IA Generativa para Principiantes",
    description: "Que es la IA generativa y como usar ChatGPT y Claude en el trabajo diario.", url: "/cursos/demo-4" },
  { id: "demo-5", title: "Agentes de IA con Claude Code",
    description: "Construye agentes que usan herramientas, specs y skills.", url: "/cursos/demo-5" },
  { id: "demo-6", title: "Programacion para Principiantes",
    description: "Aprende a programar paso a paso con Python y proyectos pequenos.", url: "/cursos/demo-6" },
];

const STOP = new Set(["de", "la", "el", "en", "un", "una", "por", "para", "con", "los", "las", "que", "del",
  "al", "y", "o", "a", "cursos", "curso", "quiero", "algo", "tienes", "hay"]);

const norm = (t) => t.toLowerCase().normalize("NFD").replace(/\p{Mn}/gu, "");

function searchLocal(query) {
  const q = norm(query).replace("inteligencia artificial", "ia").replace("artificial intelligence", "ia");
  const words = q.replace(/[,?]/g, " ").split(/\s+/).filter((w) => w.length >= 2 && !STOP.has(w));
  const scored = [];
  for (const course of SAMPLE_CATALOG) {
    const haystack = norm(`${course.title} ${course.description}`);
    const tokens = new Set(haystack.replace(/[.,]/g, " ").split(/\s+/));
    // palabras cortas (ia, ads) deben coincidir completas para no dar falsos positivos
    const score = words.filter((w) => (w.length <= 3 ? tokens.has(w) : haystack.includes(w))).length;
    if (score) scored.push([score, course]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  return { source: "catalogo_de_muestra", courses: scored.slice(0, 5).map(([, c]) => c) };
}

async function searchCourses({ query }) {
  if (PLATFORM_URL) {
    try {
      const r = await fetch(`${PLATFORM_URL}/api/courses/search?q=${encodeURIComponent(query)}`,
        { signal: AbortSignal.timeout(10_000) });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      return { source: "eduplatform", courses: data.results || data.courses || [] };
    } catch {
      // si la plataforma no responde, usamos el catalogo de muestra
    }
  }
  return searchLocal(query);
}

function rollDie({ sides }) {
  sides = Math.trunc(Number(sides));
  if (!(sides >= 2 && sides <= 1000)) return { error: "El dado debe tener entre 2 y 1000 caras." };
  return { sides, result: 1 + Math.floor(Math.random() * sides) };
}

// Descripcion para la API de Claude: es lo que el modelo "lee" para decidir cuando usarlas.
export const TOOLS = [
  {
    name: "search_courses",
    description: "Busca en el catalogo los cursos mas relevantes para lo que la persona quiere aprender. " +
      "Devuelve id, title, description y url de cada curso.",
    input_schema: {
      type: "object",
      properties: { query: { type: "string", description: "Lo que la persona quiere aprender, en lenguaje natural." } },
      required: ["query"],
    },
  },
  {
    name: "roll_die",
    description: "Tira un dado de N caras y devuelve el resultado. Usalo solo si la persona pide tirar un dado.",
    input_schema: {
      type: "object",
      properties: { sides: { type: "integer", minimum: 2, description: "Numero de caras del dado." } },
      required: ["sides"],
    },
  },
];

const IMPLEMENTATIONS = { search_courses: searchCourses, roll_die: rollDie };

/** Ejecuta la herramienta pedida por el modelo (con control de errores). */
export async function runTool(name, args) {
  const impl = IMPLEMENTATIONS[name];
  if (!impl) return JSON.stringify({ error: `Herramienta desconocida: ${name}` });
  try {
    return JSON.stringify(await impl(args));
  } catch (exc) {
    return JSON.stringify({ error: String(exc.message ?? exc) });
  }
}
