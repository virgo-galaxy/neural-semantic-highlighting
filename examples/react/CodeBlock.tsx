import { createHighlighter } from "@nsh/highlighter";
import { useEffect, useState } from "react";
import "@nsh/highlighter/theme.css";

// Reuse one worker and its loaded models across code blocks.
const highlighter = createHighlighter();

export function CodeBlock({ code, language }: { code: string; language: string }) {
  const [result, setResult] = useState<{ code: string; language: string; value: string }>();
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    setError("");
    highlighter.highlight(code, { language }).then(
      ({ value }) => {
        if (active) setResult({ code, language, value });
      },
      (reason: unknown) => {
        if (active) setError(String(reason));
      },
    );
    return () => {
      active = false;
    };
  }, [code, language]);
  const value = result?.code === code && result.language === language ? result.value : undefined;
  return (
    <>
      <pre className="nsh" data-language={language}>
        {value === undefined ? (
          <code>{code}</code>
        ) : (
          <code dangerouslySetInnerHTML={{ __html: value }} />
        )}
      </pre>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
