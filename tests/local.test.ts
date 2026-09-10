import { createLocalProcessPack } from "@nsh/local";
import { afterEach, describe, expect, it } from "vitest";

const manifest = {
  id: "test-local",
  documentKinds: [
    {
      id: "test",
      extensions: [".test"],
    },
  ],
} as const;

const providerScript = String.raw`
let buffer = "";
let count = 0;
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buffer += chunk;
  for (;;) {
    const newline = buffer.indexOf("\n");
    if (newline < 0) break;
    const line = buffer.slice(0, newline);
    buffer = buffer.slice(newline + 1);
    if (!line) continue;
    const request = JSON.parse(line);
    if (request.source === "fail") {
      process.stdout.write(JSON.stringify({
        id: request.id,
        error: { message: "provider failure" },
      }) + "\n");
      continue;
    }
    count += 1;
    process.stdout.write(JSON.stringify({
      id: request.id,
      result: {
        offsetEncoding: "utf-16",
        spans: [{
          start: 0,
          end: Math.min(1, request.source.length),
          tokenType: "request-" + count,
        }],
      },
    }) + "\n");
  }
});
`;

const openPacks: ReturnType<typeof createLocalProcessPack>[] = [];

afterEach(async () => {
  await Promise.all(openPacks.splice(0).map((pack) => pack.close()));
});

describe("createLocalProcessPack", () => {
  it("reuses one long-lived provider process across highlight calls", async () => {
    const pack = createLocalProcessPack({
      manifest,
      command: process.execPath,
      args: ["-e", providerScript],
    });
    openPacks.push(pack);

    const first = await pack.highlight({
      source: "a",
      documentKind: "test",
    });
    const second = await pack.highlight({
      source: "b",
      documentKind: "test",
    });

    expect(first.spans[0]?.tokenType).toBe("request-1");
    expect(second.spans[0]?.tokenType).toBe("request-2");
  });

  it("propagates provider errors", async () => {
    const pack = createLocalProcessPack({
      manifest,
      command: process.execPath,
      args: ["-e", providerScript],
    });
    openPacks.push(pack);

    await expect(
      pack.highlight({
        source: "fail",
        documentKind: "test",
      }),
    ).rejects.toThrow("provider failure");
  });

  it("rejects highlight calls after close", async () => {
    const pack = createLocalProcessPack({
      manifest,
      command: process.execPath,
      args: ["-e", providerScript],
    });

    await pack.close();

    await expect(
      pack.highlight({
        source: "a",
        documentKind: "test",
      }),
    ).rejects.toThrow("Local process pack is closed.");
  });
});
