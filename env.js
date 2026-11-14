// Carga el .env (Node >= 20.12). Se importa primero para que las demas variables ya existan.
try {
  process.loadEnvFile(new URL("./.env", import.meta.url));
} catch {
  // sin .env: se usan las variables del entorno
}
