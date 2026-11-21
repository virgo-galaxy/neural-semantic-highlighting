import type { HighlightResult } from "@nsh/core";
import { renderToHtml } from "@nsh/html";
import { useEffect, useRef, useState } from "react";

import { defaultModelSource, PlaygroundRuntimeManager } from "@/runtime";
import defaultPreview from "@/views/highlighter/default-preview.json";
import { examplesForContentType, type HighlighterExample } from "@/views/highlighter/examples";

type Preview =
  | { status: "ready" }
  | { status: "loading" }
  | { status: "highlighted"; html: string; elapsedMs?: number }
  | { status: "error"; message: string };

function firstExample(contentTypeId: string): HighlighterExample | undefined {
  const examples = examplesForContentType(contentTypeId);
  return examples.find(({ filename }) => filename.startsWith("hello.")) ?? examples[0];
}

const initialExample = firstExample("typescript")!;

function initialPreview(): Preview {
  if (
    defaultPreview.filename !== initialExample.id ||
    defaultPreview.documentKind !== initialExample.documentKind ||
    defaultPreview.source !== initialExample.source
  )
    return { status: "ready" };
  return {
    status: "highlighted",
    html: renderToHtml({
      source: defaultPreview.source,
      documentKind: defaultPreview.documentKind,
      result: defaultPreview.result as HighlightResult,
    }),
  };
}

export function useHighlighter() {
  const [example, setExample] = useState(initialExample);
  const [source, setSource] = useState(initialExample.source);
  const [preview, setPreview] = useState<Preview>(initialPreview);
  const runtime = useRef<PlaygroundRuntimeManager | null>(null);
  const revision = useRef(0);

  useEffect(
    () => () => {
      revision.current++;
      runtime.current?.close();
      runtime.current = null;
    },
    [],
  );

  async function highlight(text = source, documentKind = example.documentKind): Promise<void> {
    const request = ++revision.current;
    if (!text) {
      setPreview({ status: "ready" });
      return;
    }

    setPreview({ status: "loading" });
    const started = performance.now();
    try {
      runtime.current ??= new PlaygroundRuntimeManager();
      const highlighter = await runtime.current.get(defaultModelSource);
      const result = await highlighter.highlight({ source: text, documentKind });
      if (revision.current !== request) return;
      setPreview({
        status: "highlighted",
        html: renderToHtml({ source: text, documentKind, result }),
        elapsedMs: Math.max(1, Math.round(performance.now() - started)),
      });
    } catch (error) {
      if (revision.current !== request) return;
      setPreview({
        status: "error",
        message: error instanceof Error ? error.message : "Unable to highlight source.",
      });
    }
  }

  function selectExample(next: HighlighterExample) {
    setExample(next);
    setSource(next.source);
    void highlight(next.source, next.documentKind);
  }

  function selectLanguage(id: string) {
    if (id === example.contentTypeId) return;
    const next = firstExample(id);
    if (!next) return;
    if (source === example.source) {
      selectExample(next);
    } else {
      setExample(next);
      void highlight(source, next.documentKind);
    }
  }

  function editSource(text: string) {
    revision.current++;
    setSource(text);
    setPreview({ status: "ready" });
  }

  return { example, source, preview, highlight, editSource, selectLanguage, selectExample };
}
