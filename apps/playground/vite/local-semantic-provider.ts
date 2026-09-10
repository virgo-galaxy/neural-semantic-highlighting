import { readFileSync } from "node:fs";
import type { IncomingMessage, ServerResponse } from "node:http";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import type { HighlightRequest, PackManifest } from "@nsh/core";
import { createLocalProcessPack, type LocalProcessPack } from "@nsh/local";
import type { Plugin } from "vite";

const LOCAL_PREFIX = "/__nsh/local";
const REPOSITORY_ROOT = fileURLToPath(new URL("../../..", import.meta.url));
const MANIFEST_PATH = join(REPOSITORY_ROOT, "packs/typescript/manifest.json");
const PYTHON_PATH = join(REPOSITORY_ROOT, ".venv/bin/python");

const manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf8")) as PackManifest;

/**
 * Development-only bridge between the browser Playground and @nsh/local.
 *
 * The TypeScript model still runs as a local, long-lived Python process over
 * stdin/stdout. HTTP here is only the browser-to-Vite transport used by this
 * web Playground; it is not part of the SemanticPack contract.
 */
export function localSemanticProviderPlugin(): Plugin {
  let pack: LocalProcessPack | undefined;

  const getPack = () => {
    pack ??= createLocalProcessPack({
      manifest,
      command: PYTHON_PATH,
      args: ["-m", "packs.typescript.runtime.local", "--stdio"],
      cwd: REPOSITORY_ROOT,
    });

    return pack;
  };

  return {
    name: "nsh-playground-local-provider",

    configureServer(server) {
      server.middlewares.use(async (request, response, next) => {
        const pathname = new URL(request.url ?? "/", "http://localhost").pathname;

        if (pathname === `${LOCAL_PREFIX}/manifest`) {
          if (request.method !== "GET") {
            sendMethodNotAllowed(response, "GET");
            return;
          }

          sendJson(response, 200, manifest);
          return;
        }

        if (pathname !== `${LOCAL_PREFIX}/highlight`) {
          next();
          return;
        }

        if (request.method !== "POST") {
          sendMethodNotAllowed(response, "POST");
          return;
        }

        try {
          const payload = await readJsonBody(request);
          const highlightRequest = parseHighlightRequest(payload);
          const result = await getPack().highlight(highlightRequest);

          sendJson(response, 200, { result });
        } catch (error) {
          sendJson(response, 500, {
            error: {
              message: error instanceof Error ? error.message : "Local highlighting failed.",
            },
          });
        }
      });

      server.httpServer?.once("close", () => {
        const activePack = pack;
        pack = undefined;

        if (activePack) {
          void activePack.close();
        }
      });
    },
  };
}

function parseHighlightRequest(value: unknown): HighlightRequest {
  if (
    !isRecord(value) ||
    typeof value.source !== "string" ||
    typeof value.documentKind !== "string"
  ) {
    throw new Error("Highlight request must contain source and documentKind strings.");
  }

  return {
    source: value.source,
    documentKind: value.documentKind,
  };
}

async function readJsonBody(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];

  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }

  const body = Buffer.concat(chunks).toString("utf8");

  if (!body) {
    throw new Error("Request body must not be empty.");
  }

  return JSON.parse(body) as unknown;
}

function sendJson(response: ServerResponse, statusCode: number, value: unknown): void {
  response.statusCode = statusCode;
  response.setHeader("Content-Type", "application/json; charset=utf-8");
  response.end(JSON.stringify(value));
}

function sendMethodNotAllowed(response: ServerResponse, method: string): void {
  response.setHeader("Allow", method);
  sendJson(response, 405, {
    error: {
      message: `Method not allowed. Use ${method}.`,
    },
  });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
