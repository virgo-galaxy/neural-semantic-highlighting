import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import { collect, label, validate } from "../packs/css/dataset/pipeline.js";

const temporary: string[] = [];
afterEach(async () => {
  await Promise.all(
    temporary.splice(0).map((folder) => rm(folder, { recursive: true, force: true })),
  );
});

async function setup() {
  const base = await mkdtemp(join(tmpdir(), "nsh-css-data-"));
  temporary.push(base);
  const source = join(base, "source");
  const root = join(base, "css");
  await mkdir(join(source, "fixtures"), { recursive: true });
  await writeFile(join(source, "site.css"), ".card { display: grid; }");
  await writeFile(join(source, "site.scss"), "$gap: 8px; .card { gap: $gap; }");
  await writeFile(join(source, "site.less"), "@gap: 8px; .card { gap: @gap; }");
  await writeFile(join(source, "invalid.scss"), ".broken {");
  await writeFile(join(source, "fixtures", "heldout.css"), ".heldout { color: red; }");
  const config = join(base, "sources.json");
  await writeFile(
    config,
    JSON.stringify({
      format: "nsh-css-sources-v1",
      sources: [{ id: "example", base: "absolute", path: source }],
    }),
  );
  return { base, source, root, config };
}

describe("CSS external corpus safety", () => {
  it("freezes source bytes, excludes fixtures and quarantines unsupported syntax", async () => {
    const { source, root, config } = await setup();
    const first = await collect(root, config);
    expect(first.files).toBe(4);
    expect((await collect(root, config)).snapshot).toBe(first.snapshot);
    // Label the collected bytes, not whatever the original checkout now contains.
    await writeFile(join(source, "site.css"), ".changed { color: blue; }");
    const gold = await label(root);
    expect(gold.files).toBe(3);
    expect(gold.quarantine).toBe(1);
    expect(gold.documentKinds).toEqual({ css: 1, scss: 1, less: 1 });
    expect((await validate(root)).snapshot).toBe(gold.snapshot);
    const second = await collect(root, config);
    expect(second.snapshot).not.toBe(first.snapshot);
    expect(
      JSON.parse(await readFile(join(root, "corpora", first.snapshot, "sample.json"), "utf8"))
        .snapshot,
    ).toBe(first.snapshot);
  });

  it("detects changed Gold and preserves the previously published pointer on failure", async () => {
    const { root, config, source } = await setup();
    await collect(root, config);
    await label(root);
    const pointerPath = join(root, "current-corpus.json");
    const before = await readFile(pointerPath, "utf8");
    await rm(source, { recursive: true });
    await expect(collect(root, config)).rejects.toThrow();
    expect(await readFile(pointerPath, "utf8")).toBe(before);
    const pointer = JSON.parse(await readFile(join(root, "current-gold.json"), "utf8")) as {
      directory: string;
    };
    await writeFile(join(root, pointer.directory, "labeled-sample.jsonl"), "{}\n");
    await expect(validate(root)).rejects.toThrow("checksum");
  });

  it("does not delete another collector's lock", async () => {
    const { root, config } = await setup();
    await mkdir(root);
    await writeFile(join(root, ".dataset.lock"), "other process");
    await expect(collect(root, config)).rejects.toThrow();
    expect(await readFile(join(root, ".dataset.lock"), "utf8")).toBe("other process");
  });
});
