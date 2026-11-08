import { renderCodeToHtml, renderToHtml } from "@nsh/html";
import { describe, expect, it } from "vitest";

describe("renderToHtml", () => {
  it("renders semantic spans and preserves unhighlighted source", () => {
    const html = renderToHtml({
      source: "const value = 1;",
      documentKind: "typescript",
      result: {
        offsetEncoding: "utf-16",
        spans: [
          {
            start: 0,
            end: 5,
            tokenType: "keyword",
          },
          {
            start: 6,
            end: 11,
            tokenType: "variable",
          },
        ],
      },
    });

    expect(html).toBe(
      '<pre class="nsh" data-language="typescript"><code>' +
        '<span class="nsh-token" data-token-type="keyword">const</span> ' +
        '<span class="nsh-token" data-token-type="variable">value</span>' +
        " = 1;</code></pre>",
    );
  });

  it("renders semantic modifiers", () => {
    const html = renderToHtml({
      source: "value",
      documentKind: "typescript",
      result: {
        offsetEncoding: "utf-16",
        spans: [
          {
            start: 0,
            end: 5,
            tokenType: "variable",
            modifiers: ["declaration", "readonly"],
          },
        ],
      },
    });

    expect(html).toContain('data-modifiers="declaration readonly"');
  });

  it("escapes source text", () => {
    const html = renderToHtml({
      source: "<T & U>",
      documentKind: "typescript",
      result: {
        offsetEncoding: "utf-16",
        spans: [],
      },
    });

    expect(html).toContain("&lt;T &amp; U&gt;");
  });

  it("supports UTF-8 span offsets", () => {
    const html = renderToHtml({
      source: "a😀b",
      documentKind: "text",
      result: {
        offsetEncoding: "utf-8",
        spans: [
          {
            start: 1,
            end: 5,
            tokenType: "symbol",
          },
        ],
      },
    });

    expect(html).toContain('<span class="nsh-token" data-token-type="symbol">😀</span>');
  });

  it("supports UTF-32 span offsets", () => {
    const html = renderToHtml({
      source: "a😀b",
      documentKind: "text",
      result: {
        offsetEncoding: "utf-32",
        spans: [
          {
            start: 1,
            end: 2,
            tokenType: "symbol",
          },
        ],
      },
    });

    expect(html).toContain('<span class="nsh-token" data-token-type="symbol">😀</span>');
  });

  it("rejects overlapping semantic spans", () => {
    expect(() =>
      renderToHtml({
        source: "abcdef",
        documentKind: "text",
        result: {
          offsetEncoding: "utf-16",
          spans: [
            {
              start: 0,
              end: 4,
              tokenType: "first",
            },
            {
              start: 3,
              end: 6,
              tokenType: "second",
            },
          ],
        },
      }),
    ).toThrow("Semantic spans must not overlap.");
  });
});

describe("renderCodeToHtml", () => {
  it("returns an escaped fragment without adding a wrapper", () => {
    expect(
      renderCodeToHtml({
        source: "<>&",
        documentKind: "html",
        result: {
          offsetEncoding: "utf-16",
          spans: [{ start: 0, end: 1, tokenType: 'tag"onclick="x' }],
        },
      }),
    ).toBe(
      '<span class="nsh-token" data-token-type="tag&quot;onclick=&quot;x">&lt;</span>&gt;&amp;',
    );
  });
});
