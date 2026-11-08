import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, expect, it } from "vitest";

import { collect, label, validate } from "../packs/html/dataset/pipeline.js";

const temporary: string[] = [];
afterEach(async () => {
  await Promise.all(temporary.splice(0).map((path) => rm(path, { recursive: true, force: true })));
});

async function setup() {
  const base = await mkdtemp(join(tmpdir(), "nsh-html-data-"));
  temporary.push(base);
  const source = join(base, "source"),
    root = join(base, "html"),
    config = join(base, "sources.json");
  await mkdir(join(source, "fixtures"), { recursive: true });
  await writeFile(
    join(source, "index.html"),
    '<dialog open><p class="md:gap-4">Ready</p></dialog>',
  );
  await writeFile(
    join(source, "embedded.htm"),
    '<script type="module">const x=1;</script><style>.x { color:red; }</style>',
  );
  await writeFile(join(source, "legacy.html"), "<font>old</font>");
  await writeFile(join(source, "broken.html"), '<p title="unfinished>');
  await writeFile(join(source, "fixtures/heldout.html"), "<h1>heldout</h1>");
  await writeFile(
    config,
    JSON.stringify({
      format: "nsh-html-sources-v1",
      sources: [{ id: "example", base: "absolute", path: source }],
    }),
  );
  return { source, root, config };
}

it("freezes source, excludes fixtures, quarantines obsolete/broken HTML and preserves typed regions", async () => {
  const { source, root, config } = await setup();
  const captured = await collect(root, config);
  expect(captured.files).toBe(4);
  expect((await collect(root, config)).snapshot).toBe(captured.snapshot);
  await writeFile(join(source, "index.html"), "<p>changed checkout</p>");
  const gold = await label(root);
  expect(gold.files).toBe(2);
  expect(gold.quarantine).toBe(2);
  expect(gold.documentKinds).toEqual({ html: 2 });
  expect(gold.features).toEqual({ "embedded-css": 1, "embedded-javascript": 1, "markup-only": 1 });
  expect((await validate(root)).snapshot).toBe(gold.snapshot);
  expect((await collect(root, config)).snapshot).not.toBe(captured.snapshot);
});

it("rejects changed Gold rather than silently accepting new regions or roles", async () => {
  const { root, config } = await setup();
  await collect(root, config);
  await label(root);
  const pointer = JSON.parse(await readFile(join(root, "current-gold.json"), "utf8")) as {
    directory: string;
  };
  const path = join(root, pointer.directory, "labeled-sample.jsonl");
  await writeFile(path, (await readFile(path, "utf8")) + "\n");
  await expect(validate(root)).rejects.toThrow("checksum");
});
