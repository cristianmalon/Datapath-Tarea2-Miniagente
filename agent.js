// Mini-agente de texto con tool use (Sesion 9).
// Uso:
//   node agent.js                              # chat interactivo con memoria
//   node agent.js "tira un dado de 20 caras"   # una sola pregunta
import "./env.js";
import Anthropic from "@anthropic-ai/sdk";
import readline from "node:readline/promises";
import { TOOLS, runTool } from "./tools.js";

const MODEL = process.env.AGENT_MODEL ?? "claude-haiku-5-5";
const MAX_STEPS = 5; // tope de vueltas del ciclo, para que nunca quede en bucle

const SYSTEM_PROMPT = `\
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
`;

const client = new Anthropic(); // lee ANTHROPIC_API_KEY del entorno

/** Ciclo del agente. `messages` se modifica para conservar la memoria de la charla. */
async function runAgent(messages) {
  for (let step = 0; step < MAX_STEPS; step++) {
    // 1) Le describimos las herramientas a Claude y le pasamos la conversacion.
    const response = await client.messages.create({
      model: MODEL, max_tokens: 1024, system: SYSTEM_PROMPT, tools: TOOLS, messages,
    });
    messages.push({ role: "assistant", content: response.content });

    // 2) Si no pidio ninguna herramienta, esta es la respuesta final.
    if (response.stop_reason !== "tool_use") {
      return response.content.filter((b) => b.type === "text").map((b) => b.text).join("");
    }

    // 3) Pidio herramientas: las ejecutamos NOSOTROS y devolvemos el resultado.
    const results = [];
    for (const block of response.content) {
      if (block.type === "tool_use") {
        console.log(`  [herramienta] ${block.name}(${JSON.stringify(block.input)})`);
        results.push({
          type: "tool_result",
          tool_use_id: block.id, // debe coincidir con el id de la peticion
          content: await runTool(block.name, block.input),
        });
      }
    }
    messages.push({ role: "user", content: results });
    // 4) Volvemos al paso 1: Claude lee el resultado y redacta su respuesta.
  }
  return "No pude completar la respuesta, intenta reformular tu pregunta.";
}

async function main() {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Falta ANTHROPIC_API_KEY. Copia .env.example a .env y completalo.");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  if (args.length) {
    console.log(await runAgent([{ role: "user", content: args.join(" ") }]));
    return;
  }

  console.log("Edy (escribe 'salir' para terminar)");
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const history = [];
  try {
    while (true) {
      const text = (await rl.question("\nTu: ")).trim();
      if (["salir", "exit", "quit"].includes(text.toLowerCase())) break;
      if (text) {
        history.push({ role: "user", content: text });
        console.log("\nEdy:", await runAgent(history));
      }
    }
  } catch {
    // Ctrl+C / EOF
  } finally {
    rl.close();
  }
}

main();
