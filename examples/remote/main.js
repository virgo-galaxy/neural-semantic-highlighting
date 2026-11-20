import "@nsh/highlighter/theme.css";

import { clearModelCache, createHighlighter } from "@nsh/highlighter";

// For example: ?models=https://storage.example.com/highlighting/
// The resource root contains the v1/ directory from @nsh/models/dist/assets/.
const query = new URLSearchParams(location.search);
const modelBaseUrl = query.get("models") ?? "/models/";
const reference = query.get("reference");
if (query.has("clearCache")) await clearModelCache();
const highlighter = createHighlighter({
  modelBaseUrl,
  cache: { persistent: query.get("cache") !== "off" },
  ...(reference ? {} : { languages: ["tsx", "scss", "html", "vue"] }),
});
const report = { passed: false, checks: [], parity: { total: 0, passed: 0, failures: [] } };
try {
  for (const [language, source] of [
    ["tsx", 'export const App = () => <button className="action">Hello</button>;'],
    ["scss", ".root { display: grid; .action { color: #09f; &:hover { opacity: .8; } } }"],
    [
      "html",
      "<style>.action { color: red; }</style><button>Hello</button><script>const value = 1;</script>",
    ],
    [
      "vue",
      '<script setup lang="ts">const value = 1;</script><template><button>{{ value }}</button></template><style scoped>.action { color: red; }</style>',
    ],
  ]) {
    const output = await highlighter.highlight(source, { language });
    const block = document.createElement("div");
    block.innerHTML = output.html;
    document.querySelector("#preview").append(block);
    report.checks.push({
      language,
      sourcePreserved: block.textContent === source,
      spans: output.result.spans.length,
    });
  }
  if (reference) {
    const { cases } = await (await fetch(reference)).json();
    report.parity.total = cases.length;
    for (const test of cases) {
      document.querySelector("#status").textContent = `Running ${test.filename}`;
      const actual = await highlighter.highlightTokens({
        source: test.source,
        documentKind: test.documentKind,
      });
      if (JSON.stringify(actual) === JSON.stringify(test.result)) report.parity.passed++;
      else report.parity.failures.push(test.filename);
    }
  }
  report.passed =
    report.checks.every((check) => check.sourcePreserved && check.spans > 0) &&
    report.parity.passed === report.parity.total;
  document.querySelector("#status").textContent = report.passed ? "Completed" : "Failed";
} catch (error) {
  report.error = String(error);
  document.querySelector("#status").textContent = "Failed";
} finally {
  highlighter.close();
  try {
    const cache = await caches.open("nsh-model-assets-v1");
    const keys = await cache.keys();
    report.cache = {
      entries: keys.length,
      bytes: (
        await Promise.all(
          keys.map(async (key) =>
            Number((await cache.match(key))?.headers.get("X-NSH-Bytes") ?? 0),
          ),
        )
      ).reduce((a, b) => a + b, 0),
    };
  } catch {
    report.cache = { available: false };
  }
  document.querySelector("#report").textContent = JSON.stringify(report, null, 2);
}
