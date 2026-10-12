#!/usr/bin/env node
// Runs the web app (Vite) and the analysis API (uvicorn) together with prefixed logs.
// Ctrl+C stops both; if either exits, the other is stopped too.
// Pass names to run a subset: `node scripts/dev.mjs api`.
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

// Secrets such as ANTHROPIC_API_KEY live in .env (git-ignored); both children inherit them.
if (existsSync(".env")) process.loadEnvFile(".env");

const venvPython =
  process.platform === "win32"
    ? path.join(".venv", "Scripts", "python.exe")
    : path.join(".venv", "bin", "python");
const python = existsSync(venvPython) ? venvPython : "python3";

const allProcesses = [
  { name: "web", color: 36, command: "npx", args: ["vite"] },
  {
    name: "api",
    color: 35,
    command: python,
    args: ["-m", "uvicorn", "api.main:app", "--reload", "--port", "8000"],
  },
];

const selected = process.argv.slice(2);
const processes = allProcesses.filter(({ name }) => !selected.length || selected.includes(name));

const children = processes.map(({ name, color, command, args }) => {
  const child = spawn(command, args, { shell: process.platform === "win32" });
  const prefix = `\x1b[${color}m[${name}]\x1b[0m `;
  const forward = (stream, target) =>
    stream.on("data", (chunk) => {
      for (const line of chunk.toString().split("\n")) if (line) target.write(prefix + line + "\n");
    });
  forward(child.stdout, process.stdout);
  forward(child.stderr, process.stderr);
  child.on("exit", (code) => {
    process.stdout.write(`${prefix}exited with code ${code ?? 0}\n`);
    shutdown(code ?? 0);
  });
  return child;
});

let stopping = false;
function shutdown(code) {
  if (stopping) return;
  stopping = true;
  for (const child of children) if (child.exitCode === null) child.kill("SIGTERM");
  process.exitCode = code;
}

process.on("SIGINT", () => shutdown(0));
process.on("SIGTERM", () => shutdown(0));
