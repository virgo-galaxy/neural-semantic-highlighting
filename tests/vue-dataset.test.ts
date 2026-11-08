import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, expect, it } from "vitest";

import { collect, label, validate } from "../packs/vue/dataset/pipeline.js";

const temporary: string[] = [];
afterEach(async () => {
  await Promise.all(temporary.splice(0).map((path) => rm(path, { recursive: true, force: true })));
});
async function setup() {
  const base = await mkdtemp(join(tmpdir(), "nsh-vue-data-"));
  temporary.push(base);
  const source = join(base, "source"),
    root = join(base, "vue"),
    config = join(base, "sources.json");
  await mkdir(join(source, "fixtures"), { recursive: true });
  await writeFile(
    join(source, "Counter.vue"),
    '<template><button @click="count++">{{ count }}</button></template><script>export default { data() { return {count:0}; } };</script>',
  );
  await writeFile(join(source, "broken.vue"), "<script>const x = ;</script>");
  await writeFile(join(source, "fixtures/heldout.vue"), "<template><p>heldout</p></template>");
  await writeFile(
    config,
    JSON.stringify({
      format: "nsh-vue-sources-v1",
      sources: [
        {
          id: "example",
          base: "absolute",
          path: source,
          profile: "vue2",
          groupFamily: "counter-family",
        },
      ],
    }),
  );
  return { source, root, config };
}
it("freezes original Vue source, version provenance and grouped-family identity", async () => {
  const { source, root, config } = await setup();
  const corpus = await collect(root, config);
  expect(corpus.files).toBe(2);
  await writeFile(join(source, "Counter.vue"), "<template>changed checkout</template>");
  const gold = await label(root);
  expect(gold.files).toBe(1);
  expect(gold.quarantine).toBe(1);
  expect((await validate(root)).snapshot).toBe(gold.snapshot);
  const pointer = JSON.parse(await readFile(join(root, "current-gold.json"), "utf8"));
  const record = JSON.parse(
    (await readFile(join(root, pointer.directory, "labeled-sample.jsonl"), "utf8")).trim(),
  );
  expect(record.profile).toBe("vue2");
  expect(record.sourceGroup).toBe("counter-family:.");
  expect(record.source).toContain("count++");
});
it("refuses modified frozen Gold", async () => {
  const { root, config } = await setup();
  await collect(root, config);
  await label(root);
  const p = JSON.parse(await readFile(join(root, "current-gold.json"), "utf8"));
  const path = join(root, p.directory, "labeled-sample.jsonl");
  await writeFile(path, (await readFile(path, "utf8")) + "\n");
  await expect(validate(root)).rejects.toThrow("checksum");
});
