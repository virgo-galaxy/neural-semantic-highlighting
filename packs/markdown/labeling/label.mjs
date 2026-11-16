/** Offline parse-only AST ranges. No formatting, Markdown rendering or code execution. */
import * as prettier from "prettier";
import { decodeHTMLStrict } from "entities";
import { createInterface } from "node:readline";

export async function label(source) {
  if (typeof source !== "string" || source.includes("\0")) throw Error("Invalid Markdown source");
  const map = [source.startsWith("\ufeff") ? 1 : 0];
  let normalized = "";
  for (let i = map[0]; i < source.length; i++) {
    if (source[i] === "\r") {
      if (source[i + 1] === "\n") i++;
      normalized += "\n";
    } else normalized += source[i];
    map.push(i + 1);
  }
  const parsed = await prettier.__debug.parse(source, { parser: "markdown" });
  if (parsed.text !== normalized)
    throw Error("Unexpected parser preprocessing; original offsets cannot be mapped");
  const roles = Array(normalized.length).fill("text");
  const flags = Array(normalized.length).fill(0);
  const breaks = new Set([0, normalized.length]);
  const features = new Set();
  const paint = (a, b, role, mask = 0) => {
    if (!Number.isInteger(a) || !Number.isInteger(b) || a < 0 || b > normalized.length || b < a)
      throw Error("Invalid parser source range");
    roles.fill(role, a, b);
    flags.fill(mask, a, b);
    breaks.add(a);
    breaks.add(b);
  };
  const bounds = (n) => {
    const a = n.position?.start.offset,
      b = n.position?.end.offset;
    if (!Number.isInteger(a) || !Number.isInteger(b) || a < 0 || b < a || b > normalized.length)
      throw Error("Missing original AST positions: " + n.type);
    return [a, b];
  };
  function destination(at, end) {
    while (at < end && /\s/u.test(normalized[at])) at++;
    const begin = at;
    if (normalized[at] === "<") {
      at++;
      while (at < end) {
        if (normalized[at] === "\\") at += 2;
        else if (normalized[at++] === ">") break;
      }
    } else {
      let depth = 0;
      while (at < end) {
        const c = normalized[at];
        if (c === "\\") {
          at += 2;
          continue;
        }
        if (/\s/u.test(c) || (c === ")" && !depth)) break;
        if (c === "(") depth++;
        else if (c === ")") depth--;
        at++;
      }
    }
    paint(begin, Math.min(at, end), "link-destination");
    while (at < end && /\s/u.test(normalized[at])) at++;
    if (at < end && ['"', "'", "("].includes(normalized[at])) {
      const start = at,
        close = normalized[at] === "(" ? ")" : normalized[at];
      at++;
      while (at < end) {
        if (normalized[at] === "\\") at += 2;
        else if (normalized[at++] === close) break;
      }
      paint(start, Math.min(at, end), "string");
    }
  }
  function linkSuffix(n, a, b, contentEnd) {
    let at = contentEnd;
    while (at < b && normalized[at] !== "]") at++;
    at++;
    if (normalized[at] === "(") destination(at + 1, b - 1);
    else if (normalized[at] === "[") paint(at + 1, b - 1, "link-destination");
  }
  function walk(n, role = "text", mask = 0, containers = []) {
    const [a, b] = bounds(n);
    breaks.add(a);
    breaks.add(b);
    const children = n.children ?? [];
    const recurse = (r = role, m = mask, c = containers) =>
      children.forEach((x) => walk(x, r, m, c));
    switch (n.type) {
      case "root":
        recurse();
        break;
      case "paragraph":
        paint(a, b, role, mask);
        recurse();
        break;
      case "text": {
        paint(a, b, role, mask);
        const raw = normalized.slice(a, b);
        for (const m of raw.matchAll(
          /\\[!-/:-@\[-`{-~]|&(?:#[0-9]+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);/gu,
        )) {
          if (m[0][0] === "&" && decodeHTMLStrict(m[0]) === m[0]) continue;
          paint(a + m.index, a + m.index + m[0].length, "entity", mask);
          features.add("entities");
        }
        break;
      }
      case "heading":
        paint(a, b, "punctuation");
        features.add("headings");
        recurse("heading");
        break;
      case "strong":
      case "emphasis":
      case "delete": {
        const bit = { strong: 1, emphasis: 2, delete: 4 }[n.type];
        features.add(n.type === "delete" ? "strikethrough" : "emphasis");
        paint(a, b, "punctuation");
        recurse(role, mask | bit);
        break;
      }
      case "inlineCode":
        paint(a, b, "code", mask);
        features.add("inline-code");
        break;
      case "code": {
        const raw = normalized.slice(a, b),
          lineEnd = raw.indexOf("\n");
        const opening = /^( {0,3})(`{3,}|~{3,})([^\n]*)/u.exec(raw);
        if (!opening || containers.length) {
          const indent = !opening ? (/^[ \t]+/u.exec(raw)?.[0].length ?? 0) : 0;
          paint(a + indent, b, "code");
          features.add(containers.length ? "container-code" : "indented-code");
          break;
        }
        features.add("fenced-code");
        const delimiter = opening[2];
        paint(a + opening[1].length, a + opening[1].length + delimiter.length, "code-fence");
        const tail = opening[3],
          info = /^\s*(\S+)/u.exec(tail);
        if (info) {
          const start =
            a + opening[1].length + delimiter.length + info.index + info[0].length - info[1].length;
          paint(start, start + info[1].length, "code-language");
          let rest = start + info[1].length;
          while (rest < a + lineEnd && /\s/u.test(normalized[rest])) rest++;
          if (lineEnd >= 0 && normalized.slice(rest, a + lineEnd).trim())
            paint(rest, a + lineEnd, "string");
        }
        if (lineEnd < 0) break;
        const bodyStart = a + lineEnd + 1;
        const lastLine = normalized.lastIndexOf("\n", b - 1) + 1;
        const closing =
          lastLine >= bodyStart
            ? new RegExp(
                "^ {0,3}" + delimiter[0] + "{" + delimiter.length + ",}[ \\t]*$",
                "u",
              ).exec(normalized.slice(lastLine, b))
            : null;
        const bodyEnd = closing ? lastLine : b;
        if (bodyEnd > bodyStart) paint(bodyStart, bodyEnd, "embedded-code");
        if (closing) {
          const m = /[^ \t]+/u.exec(closing[0]);
          paint(lastLine + m.index, lastLine + m.index + m[0].length, "code-fence");
        }
        break;
      }
      case "list":
        features.add("lists");
        recurse(role, mask, [...containers, "list"]);
        break;
      case "listItem": {
        const first = children.length ? bounds(children[0])[0] : b;
        paint(a, first, "punctuation");
        const raw = normalized.slice(a, first),
          task = /\[[ xX]\]/u.exec(raw);
        if (typeof n.checked === "boolean") {
          if (!task) throw Error("Task position missing");
          paint(a + task.index, a + task.index + 3, "keyword");
          features.add("tasks");
        }
        recurse();
        break;
      }
      case "blockquote": {
        features.add("quotes");
        recurse(role, mask, [...containers, "quote"]);
        for (const m of normalized.slice(a, b).matchAll(/(^|\n) {0,3}>/gu)) {
          const start = a + m.index + m[0].length - 1;
          paint(start, start + 1, "punctuation");
        }
        break;
      }
      case "thematicBreak":
        paint(a, b, "punctuation");
        features.add("rules");
        break;
      case "link":
      case "linkReference": {
        paint(a, b, "punctuation");
        features.add("links");
        recurse("link");
        if (children.length) linkSuffix(n, a, b, bounds(children.at(-1))[1]);
        else if (normalized.slice(a, b).startsWith("[](")) destination(a + 3, b - 1);
        break;
      }
      case "image":
      case "imageReference": {
        paint(a, b, "punctuation");
        features.add("images");
        features.add("links");
        let at = a + 2,
          depth = 0;
        while (at < b) {
          const c = normalized[at];
          if (c === "\\") {
            at += 2;
            continue;
          }
          if (c === "[") depth++;
          else if (c === "]") {
            if (!depth) break;
            depth--;
          }
          at++;
        }
        paint(a + 2, at, "link");
        linkSuffix(n, a, b, at);
        break;
      }
      case "definition": {
        features.add("references");
        features.add("links");
        paint(a, b, "punctuation");
        const close = normalized.indexOf("]:", a);
        if (close < 0 || close >= b) throw Error("Reference definition range missing");
        paint(a + 1, close, "link");
        destination(close + 2, b);
        break;
      }
      case "table": {
        features.add("tables");
        paint(a, b, "punctuation");
        children.forEach((row, i) =>
          row.children.forEach((cell) => walk(cell, i ? "text" : "heading", mask, containers)),
        );
        break;
      }
      case "tableCell":
        recurse();
        break;
      case "break":
        paint(a, b, "punctuation");
        features.add("hard-breaks");
        break;
      case "html":
        paint(a, b, normalized.slice(a, b).trimStart().startsWith("<!--") ? "comment" : "string");
        features.add("html");
        break;
      case "frontMatter":
        paint(a, b, "code");
        features.add("front-matter");
        break;
      case "footnoteDefinition": {
        features.add("footnotes");
        paint(a, b, "punctuation");
        recurse();
        break;
      }
      case "footnoteReference":
        paint(a, b, "link");
        features.add("footnotes");
        break;
      default:
        throw Error("Unsupported Markdown AST node: " + n.type);
    }
  }
  walk(parsed.ast);
  const spans = [];
  if (source.startsWith("\ufeff")) spans.push({ start: 0, end: 1, tokenType: "punctuation" });
  const names = ["strong", "emphasis", "strikethrough"];
  const emit = (a, b) => {
    const role = roles[a];
    if (
      !["code", "embedded-code", "comment", "string", "link-destination"].includes(role) &&
      !normalized.slice(a, b).trim()
    )
      return;
    if (["punctuation", "code-language", "code-fence", "keyword"].includes(role)) {
      while (a < b && /\s/u.test(normalized[a])) a++;
      while (b > a && /\s/u.test(normalized[b - 1])) b--;
    }
    if (a === b) return;
    const span = { start: map[a], end: map[b], tokenType: role };
    const modifiers = names.filter((_, i) => flags[a] & (1 << i));
    if (modifiers.length) span.modifiers = modifiers;
    spans.push(span);
  };
  let start = 0;
  for (let i = 1; i <= normalized.length; i++)
    if (
      i === normalized.length ||
      roles[i] !== roles[start] ||
      flags[i] !== flags[start] ||
      breaks.has(i)
    ) {
      emit(start, i);
      start = i;
    }
  let end = 0;
  const boundaries = new Set([0]);
  let unit = 0;
  for (const c of source) {
    unit += c.length;
    boundaries.add(unit);
  }
  for (const s of spans) {
    if (
      s.start < end ||
      s.end <= s.start ||
      !boundaries.has(s.start) ||
      !boundaries.has(s.end) ||
      source.slice(end, s.start).trim()
    )
      throw Error("Incomplete/overlapping original Markdown coverage");
    end = s.end;
  }
  if (source.slice(end).trim()) throw Error("Uncovered Markdown suffix");
  if (source.includes("\r\n")) features.add("crlf");
  if (/[^\x00-\x7f]/u.test(source)) features.add("unicode");
  return { offsetEncoding: "utf-16", spans, features: [...features].sort() };
}
const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of input) {
  try {
    const request = JSON.parse(line);
    console.log(JSON.stringify({ result: await label(request.source) }));
  } catch (error) {
    console.log(JSON.stringify({ error: String(error.message) }));
  }
}
