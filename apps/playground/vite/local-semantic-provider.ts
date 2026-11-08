import { existsSync, readFileSync } from "node:fs";
import type { IncomingMessage, ServerResponse } from "node:http";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type { HighlightRequest, PackManifest, SemanticPack } from "@nsh/core";
import { createLocalProcessPack, type LocalProcessPack } from "@nsh/local";
import type { Plugin } from "vite";

import { createCompositeHtmlPack } from "../../../packs/html/runtime/composite";
import { createCompositeVuePack } from "../../../packs/vue/runtime/composite";

const LOCAL_PREFIX = "/__nsh/local";
const REPOSITORY_ROOT = fileURLToPath(new URL("../../..", import.meta.url));
const PYTHON_PATH = join(REPOSITORY_ROOT, ".venv/bin/python");
const TYPESCRIPT_MANIFEST_PATH = join(REPOSITORY_ROOT, "packs/typescript/manifest.json");
const GO_MANIFEST_PATH = join(REPOSITORY_ROOT, "packs/go/manifest.json");
const CSS_MANIFEST_PATH = join(REPOSITORY_ROOT, "packs/css/manifest.json");
const HTML_MANIFEST_PATH = join(REPOSITORY_ROOT, "packs/html/manifest.json");
const VUE_MANIFEST_PATH = join(REPOSITORY_ROOT, "packs/vue/manifest.json");

const typescriptManifest = readManifest(TYPESCRIPT_MANIFEST_PATH);
const goManifest = readManifest(GO_MANIFEST_PATH);
const cssManifest = readManifest(CSS_MANIFEST_PATH);
const htmlManifest = readManifest(HTML_MANIFEST_PATH);
const vueManifest = readManifest(VUE_MANIFEST_PATH);
const standaloneManifests = ["python", "bash", "perl", "awk", "sql", "powershell", "bat"].map(
  (id) => readManifest(join(REPOSITORY_ROOT, "packs", id, "manifest.json")),
);
const manifest: PackManifest = {
  id: "playground-local",
  documentKinds: [
    ...typescriptManifest.documentKinds,
    ...goManifest.documentKinds,
    ...cssManifest.documentKinds,
    ...htmlManifest.documentKinds,
    ...vueManifest.documentKinds,
    ...standaloneManifests.flatMap((pack) => pack.documentKinds),
  ],
};
const goDocumentKinds = new Set(goManifest.documentKinds.map((item) => item.id));
const typescriptDocumentKinds = new Set(typescriptManifest.documentKinds.map((item) => item.id));
const cssDocumentKinds = new Set(cssManifest.documentKinds.map((item) => item.id));

/**
 * Development-only bridge between the browser Playground and @nsh/local.
 *
 * Language models run as long-lived local Python processes. Go and CSS-family
 * paths consume neural weights directly without invoking language tooling.
 * HTML composes those same processes inside neurally predicted body regions.
 */
export function localSemanticProviderPlugin(): Plugin {
  let typescriptPack: LocalProcessPack | undefined;
  let goPack: LocalProcessPack | undefined;
  let cssPack: LocalProcessPack | undefined;
  let htmlBasePack: LocalProcessPack | undefined;
  let htmlPack: SemanticPack | undefined;
  let vueBasePack: LocalProcessPack | undefined;
  let vuePack: SemanticPack | undefined;
  const standalonePacks = new Map<string, LocalProcessPack>();

  const getPack = (documentKind: string): SemanticPack => {
    const standalone = standaloneManifests.find((pack) =>
      pack.documentKinds.some((kind) => kind.id === documentKind),
    );
    if (standalone) {
      let pack = standalonePacks.get(standalone.id);
      if (!pack) {
        pack = createStandalonePack(standalone);
        standalonePacks.set(standalone.id, pack);
      }
      return pack;
    }
    if (documentKind === "vue") {
      vueBasePack ??= createVuePack();
      vuePack ??= createCompositeVuePack({
        base: vueBasePack,
        highlightEmbedded: (request) => getPack(request.documentKind).highlight(request),
      });
      return vuePack;
    }
    if (documentKind === "html") {
      htmlBasePack ??= createHtmlPack();
      htmlPack ??= createCompositeHtmlPack({
        base: htmlBasePack,
        highlightEmbedded: (request) => getPack(request.documentKind).highlight(request),
      });
      return htmlPack;
    }
    if (cssDocumentKinds.has(documentKind)) {
      cssPack ??= createCssPack();
      return cssPack;
    }
    if (goDocumentKinds.has(documentKind)) {
      goPack ??= createGoPack();
      return goPack;
    }

    if (typescriptDocumentKinds.has(documentKind)) {
      typescriptPack ??= createTypeScriptPack();
      return typescriptPack;
    }

    throw new Error(`Unsupported document kind "${documentKind}".`);
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
          const result = await getPack(highlightRequest.documentKind).highlight(highlightRequest);

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
        const activePacks = [
          typescriptPack,
          goPack,
          cssPack,
          htmlBasePack,
          vueBasePack,
          ...standalonePacks.values(),
        ].filter((pack): pack is LocalProcessPack => pack !== undefined);
        typescriptPack = undefined;
        goPack = undefined;
        cssPack = undefined;
        htmlBasePack = undefined;
        htmlPack = undefined;
        vueBasePack = undefined;
        vuePack = undefined;
        standalonePacks.clear();

        for (const pack of activePacks) {
          void pack.close();
        }
      });
    },
  };
}

function createStandalonePack(pack: PackManifest): LocalProcessPack {
  const args = ["-m", `packs.${pack.id}.runtime.local`, "--stdio", "--device", "auto"];
  const configuredPath =
    process.env[`NSH_${pack.id.toUpperCase().replaceAll("-", "_")}_CHECKPOINT`];
  if (configuredPath) {
    const checkpointPath = resolve(REPOSITORY_ROOT, configuredPath);
    if (!existsSync(checkpointPath)) {
      throw new Error(`${pack.id} checkpoint does not exist: ${checkpointPath}`);
    }
    args.push("--checkpoint", checkpointPath);
  }
  return createLocalProcessPack({
    manifest: pack,
    command: PYTHON_PATH,
    args,
    cwd: REPOSITORY_ROOT,
  });
}

function createTypeScriptPack(): LocalProcessPack {
  return createLocalProcessPack({
    manifest: typescriptManifest,
    command: PYTHON_PATH,
    args: ["-m", "packs.typescript.runtime.local", "--stdio"],
    cwd: REPOSITORY_ROOT,
  });
}

function createGoPack(): LocalProcessPack {
  const args = ["-m", "packs.go.runtime.local", "--stdio", "--device", "auto"];
  const configuredPath = process.env.NSH_GO_CHECKPOINT;

  if (configuredPath) {
    const checkpointPath = resolve(REPOSITORY_ROOT, configuredPath);

    if (!existsSync(checkpointPath)) {
      throw new Error(`Go checkpoint does not exist: ${checkpointPath}`);
    }

    args.push("--checkpoint", checkpointPath);
  }

  return createLocalProcessPack({
    manifest: goManifest,
    command: PYTHON_PATH,
    args,
    cwd: REPOSITORY_ROOT,
  });
}

function readManifest(path: string): PackManifest {
  return JSON.parse(readFileSync(path, "utf8")) as PackManifest;
}

function createCssPack(): LocalProcessPack {
  const args = ["-m", "packs.css.runtime.local", "--stdio", "--device", "auto"];
  const configuredPath = process.env.NSH_CSS_CHECKPOINT;
  if (configuredPath) {
    const checkpointPath = resolve(REPOSITORY_ROOT, configuredPath);
    if (!existsSync(checkpointPath)) {
      throw new Error(`CSS checkpoint does not exist: ${checkpointPath}`);
    }
    args.push("--checkpoint", checkpointPath);
  }
  return createLocalProcessPack({
    manifest: cssManifest,
    command: PYTHON_PATH,
    args,
    cwd: REPOSITORY_ROOT,
  });
}

function createHtmlPack(): LocalProcessPack {
  const args = ["-m", "packs.html.runtime.local", "--stdio", "--device", "auto"];
  const configuredPath = process.env.NSH_HTML_CHECKPOINT;
  if (configuredPath) {
    const checkpointPath = resolve(REPOSITORY_ROOT, configuredPath);
    if (!existsSync(checkpointPath)) {
      throw new Error(`HTML checkpoint does not exist: ${checkpointPath}`);
    }
    args.push("--checkpoint", checkpointPath);
  }
  return createLocalProcessPack({
    manifest: htmlManifest,
    command: PYTHON_PATH,
    args,
    cwd: REPOSITORY_ROOT,
  });
}

function createVuePack(): LocalProcessPack {
  const args = ["-m", "packs.vue.runtime.local", "--stdio", "--device", "auto"];
  const configuredPath = process.env.NSH_VUE_CHECKPOINT;
  if (configuredPath) {
    const checkpointPath = resolve(REPOSITORY_ROOT, configuredPath);
    if (!existsSync(checkpointPath)) {
      throw new Error(`Vue checkpoint does not exist: ${checkpointPath}`);
    }
    args.push("--checkpoint", checkpointPath);
  }
  return createLocalProcessPack({
    manifest: vueManifest,
    command: PYTHON_PATH,
    args,
    cwd: REPOSITORY_ROOT,
  });
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
