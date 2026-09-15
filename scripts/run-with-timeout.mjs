#!/usr/bin/env node

import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function parseDuration(value) {
  const match = /^(\d+)(ms|s|m)$/.exec(value ?? "");
  if (!match) throw new Error(`Invalid duration ${JSON.stringify(value)}; use ms, s or m`);
  const multipliers = { ms: 1, s: 1_000, m: 60_000 };
  return Number(match[1]) * multipliers[match[2]];
}

export function commandArguments(argv) {
  const separator = argv.indexOf("--");
  const timeoutIndex = argv.indexOf("--timeout");
  const killAfterIndex = argv.indexOf("--kill-after");
  if (separator < 0 || !argv[separator + 1] || timeoutIndex < 0 || killAfterIndex < 0) {
    throw new Error("Usage: run-with-timeout.mjs --timeout <duration> --kill-after <duration> -- <command> [args]");
  }
  return {
    timeoutMs: parseDuration(argv[timeoutIndex + 1]),
    killAfterMs: parseDuration(argv[killAfterIndex + 1]),
    command: argv[separator + 1],
    args: argv.slice(separator + 2),
  };
}

function signalProcess(child, signal) {
  if (child.exitCode !== null || child.signalCode !== null) return;
  try {
    if (process.platform === "win32") child.kill(signal);
    else process.kill(-child.pid, signal);
  } catch (error) {
    if (error?.code !== "ESRCH") throw error;
  }
}

async function main() {
  const options = commandArguments(process.argv.slice(2));
  const child = spawn(options.command, options.args, {
    stdio: "inherit",
    detached: process.platform !== "win32",
  });
  let timedOut = false;
  let killTimer;
  const timeoutTimer = setTimeout(() => {
    timedOut = true;
    console.error(`Command exceeded ${options.timeoutMs}ms; sending SIGTERM.`);
    signalProcess(child, "SIGTERM");
    killTimer = setTimeout(() => signalProcess(child, "SIGKILL"), options.killAfterMs);
  }, options.timeoutMs);
  const outcome = await new Promise((resolveOutcome, reject) => {
    child.once("error", reject);
    child.once("exit", (code, signal) => resolveOutcome({ code, signal }));
  });
  clearTimeout(timeoutTimer);
  if (killTimer) clearTimeout(killTimer);
  if (timedOut) process.exitCode = 124;
  else if (outcome.signal) process.exitCode = 1;
  else process.exitCode = outcome.code ?? 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(error instanceof Error ? error.message : String(error));
    process.exitCode = 1;
  });
}
