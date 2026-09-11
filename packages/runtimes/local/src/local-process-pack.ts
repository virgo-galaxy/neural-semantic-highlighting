import { type ChildProcessWithoutNullStreams, spawn } from "node:child_process";
import { createInterface, type Interface as ReadLineInterface } from "node:readline";

import type { HighlightRequest, HighlightResult, PackManifest, SemanticPack } from "@nsh/core";

import { asProtocolError, parseProviderResponse } from "./protocol.js";

export interface LocalProcessPackOptions {
  manifest: PackManifest;
  command: string;
  args?: readonly string[];
  cwd?: string;
  env?: NodeJS.ProcessEnv;
}

interface PendingRequest {
  resolve(result: HighlightResult): void;
  reject(error: Error): void;
}

export class LocalProcessPack implements SemanticPack {
  readonly manifest: PackManifest;

  readonly #options: LocalProcessPackOptions;
  readonly #pending = new Map<number, PendingRequest>();
  #process: ChildProcessWithoutNullStreams | undefined;
  #reader: ReadLineInterface | undefined;
  #nextRequestId = 1;
  #closed = false;
  #stderr = "";

  constructor(options: LocalProcessPackOptions) {
    if (!options.command) {
      throw new Error("Local process command must not be empty.");
    }

    this.manifest = options.manifest;
    this.#options = options;
  }

  async highlight(request: HighlightRequest): Promise<HighlightResult> {
    if (this.#closed) {
      throw new Error("Local process pack is closed.");
    }

    const child = this.#ensureProcess();
    const id = this.#nextRequestId++;

    return new Promise<HighlightResult>((resolve, reject) => {
      this.#pending.set(id, { resolve, reject });

      child.stdin.write(
        `${JSON.stringify({ id, source: request.source, documentKind: request.documentKind })}\n`,
        (error) => {
          if (!error) {
            return;
          }

          const pending = this.#pending.get(id);

          if (pending) {
            this.#pending.delete(id);
            pending.reject(
              new Error(`Unable to write to local semantic provider: ${error.message}`),
            );
          }
        },
      );
    });
  }

  async close(): Promise<void> {
    if (this.#closed) {
      return;
    }

    this.#closed = true;
    this.#rejectPending(new Error("Local process pack was closed."));

    const child = this.#process;
    this.#clearProcess(child);

    if (!child || child.exitCode !== null || child.signalCode !== null) {
      return;
    }

    await new Promise<void>((resolve) => {
      let settled = false;
      const forceKillTimer = setTimeout(() => child.kill(), 250);
      const finish = () => {
        if (settled) {
          return;
        }

        settled = true;
        clearTimeout(forceKillTimer);
        resolve();
      };

      child.once("exit", finish);
      child.stdin.end();

      if (child.exitCode !== null || child.signalCode !== null) {
        finish();
      }
    });
  }

  #ensureProcess(): ChildProcessWithoutNullStreams {
    if (this.#process) {
      return this.#process;
    }

    this.#stderr = "";
    const child = spawn(this.#options.command, [...(this.#options.args ?? [])], {
      cwd: this.#options.cwd,
      env: this.#options.env ? { ...process.env, ...this.#options.env } : process.env,
      stdio: "pipe",
    });
    const reader = createInterface({ input: child.stdout });

    this.#process = child;
    this.#reader = reader;

    reader.on("line", (line) => {
      try {
        this.#handleLine(line);
      } catch (error) {
        this.#rejectPending(asProtocolError(error));
        child.kill();
      }
    });

    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk: string) => {
      this.#stderr = `${this.#stderr}${chunk}`.slice(-8192);
    });

    child.on("error", (error) => {
      this.#clearProcess(child);
      this.#rejectPending(new Error(`Unable to start local semantic provider: ${error.message}`));
    });

    child.on("exit", (code, signal) => {
      this.#clearProcess(child);

      if (this.#closed || this.#pending.size === 0) {
        return;
      }

      const reason = signal ? `signal ${signal}` : `code ${code ?? "unknown"}`;
      const stderr = this.#stderr.trim();

      this.#rejectPending(
        new Error(`Local semantic provider exited with ${reason}.${stderr ? `\n${stderr}` : ""}`),
      );
    });

    return child;
  }

  #handleLine(line: string): void {
    const response = parseProviderResponse(line);
    const pending = this.#pending.get(response.id);

    if (!pending) {
      throw new Error(`Local semantic provider returned unknown request id ${response.id}.`);
    }

    this.#pending.delete(response.id);

    if (response.error) {
      pending.reject(new Error(response.error.message));
      return;
    }

    if (!response.result) {
      pending.reject(new Error("Local semantic provider returned no result."));
      return;
    }

    pending.resolve(response.result);
  }

  #clearProcess(child: ChildProcessWithoutNullStreams | undefined): void {
    if (!child || this.#process !== child) {
      return;
    }

    this.#process = undefined;
    this.#reader?.close();
    this.#reader = undefined;
  }

  #rejectPending(error: Error): void {
    for (const pending of this.#pending.values()) {
      pending.reject(error);
    }

    this.#pending.clear();
  }
}

export function createLocalProcessPack(options: LocalProcessPackOptions): LocalProcessPack {
  return new LocalProcessPack(options);
}
