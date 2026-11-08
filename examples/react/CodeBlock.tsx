import { useEffect, useState } from "react";

import { highlighter } from "../highlighter";

type Highlighted = { code: string; language: string; value?: string; error?: string };

export function CodeBlock({ code, language }: { code: string; language: string }) {
  const [result, setResult] = useState<Highlighted>();
  useEffect(() => {
    let active = true;
    highlighter.highlight(code, { language }).then(
      ({ value }) => {
        if (active) setResult({ code, language, value });
      },
      (reason: unknown) => {
        if (active) setResult({ code, language, error: String(reason) });
      },
    );
    return () => {
      active = false;
    };
  }, [code, language]);
  const current = result?.code === code && result.language === language ? result : undefined;
  return (
    <>
      <pre className="nsh" data-language={language} aria-busy={current === undefined}>
        {current?.value === undefined ? (
          <code>{code}</code>
        ) : (
          <code dangerouslySetInnerHTML={{ __html: current.value }} />
        )}
      </pre>
      {current?.error ? <p role="alert">{current.error}</p> : null}
    </>
  );
}
