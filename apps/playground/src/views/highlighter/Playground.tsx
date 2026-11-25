import { contentCategories } from "@nsh/highlighter/catalog";
import { themes } from "@nsh/highlighter/themes";
import {
  CopyIcon,
  GithubIcon,
  MoonFilledIcon,
  ResetIcon,
  SunFilledIcon,
} from "@virgo-design/icons";
import {
  Button,
  LocaleProvider,
  SegmentedControl,
  Select,
  Surface,
  Textarea,
  Tooltip,
} from "@virgo-design/ui";
import { enUS } from "@virgo-design/ui/locale";
import { type KeyboardEvent, useEffect, useRef, useState } from "react";

import { useHighlighter } from "@/views/highlighter/composables/useHighlighter";
import { examplesForContentType, highlighterContentTypes } from "@/views/highlighter/examples";

type Appearance = "light" | "dark";
type Pane = "source" | "preview";

const languageGroups = contentCategories.map((category) => ({
  ...category,
  entries: highlighterContentTypes
    .filter((entry) => entry.category === category.id)
    .sort(
      (left, right) =>
        left.label.localeCompare(right.label, "en", { ignorePunctuation: true }) ||
        left.label.localeCompare(right.label, "en"),
    ),
}));

const highlightStatusLabels = {
  ready: "Editing",
  loading: "Highlighting",
  highlighted: "Highlighted",
  error: "Error",
};

function performanceLevel(elapsedMs: number | undefined) {
  if (elapsedMs === undefined) return undefined;
  if (elapsedMs <= 100) return "fast";
  if (elapsedMs <= 250) return "warning";
  return "critical";
}

export function Playground() {
  const [appearance, setAppearance] = useState<Appearance>("light");
  const [preset, setPreset] = useState("default");
  const [pane, setPane] = useState<Pane>("source");
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">("idle");
  const isComposing = useRef(false);
  const { example, source, preview, highlight, editSource, selectLanguage, selectExample } =
    useHighlighter();
  const examples = examplesForContentType(example.contentTypeId);
  const busy = preview.status === "loading";
  const elapsedMs = preview.status === "highlighted" ? preview.elapsedMs : undefined;
  const statusLabel =
    preview.status === "highlighted" && elapsedMs === undefined
      ? "Example preview"
      : highlightStatusLabels[preview.status];

  useEffect(() => {
    document.documentElement.dataset.theme = appearance;
  }, [appearance]);

  function runHighlight() {
    if (!source.trim()) return;
    setPane("preview");
    if (!busy) void highlight();
  }

  function handleEditorKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (isComposing.current || event.nativeEvent.isComposing) return;
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      runHighlight();
    }
  }

  async function copySource() {
    try {
      await navigator.clipboard.writeText(source);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }

  return (
    <LocaleProvider locale={enUS}>
      <header className="site-header">
        <div className="site-header__inner">
          <div className="site-brand">
            <img src="/favicon.svg" width="30" height="30" alt="" />
            <span>Neural Semantic Highlighting</span>
          </div>
          <div className="site-actions">
            <Button
              className="site-action"
              variant="text"
              size="small"
              iconOnly
              aria-label={appearance === "light" ? "Use dark appearance" : "Use light appearance"}
              onClick={() => setAppearance(appearance === "light" ? "dark" : "light")}
            >
              {appearance === "light" ? <MoonFilledIcon /> : <SunFilledIcon />}
            </Button>
            <a
              className="site-action repo-link"
              href="https://github.com/virgo-galaxy/virgo-nsh"
              aria-label="GitHub repository"
            >
              <GithubIcon size={20} />
            </a>
          </div>
        </div>
      </header>

      <main className="playground" data-nsh-theme={appearance} data-nsh-preset={preset}>
        <div className="playground__intro">
          <h1>Playground</h1>
          <p>Try semantic highlighting on your own code, right in the browser.</p>
        </div>

        <Surface className="workspace" radius={12} border="default">
          <div className="workspace__toolbar">
            <div className="workspace__controls">
              <div className="control">
                <label htmlFor="language">Language</label>
                <Select
                  id="language"
                  size="small"
                  value={example.contentTypeId}
                  onValueChange={(id) => {
                    setCopyState("idle");
                    selectLanguage(id);
                  }}
                >
                  <Select.Trigger />
                  <Select.Content className="language-menu">
                    {languageGroups.map(({ id, label, entries }) => (
                      <div className="language-group" key={id} role="group" aria-label={label}>
                        <div className="language-group__label" aria-hidden="true">
                          {label}
                        </div>
                        <div className="language-group__options">
                          {entries.map(({ id: value, label: name, icon }) => (
                            <Select.Option key={value} value={value}>
                              {icon && <img className="language-icon" alt="" src={icon} />}
                              {name}
                            </Select.Option>
                          ))}
                        </div>
                      </div>
                    ))}
                  </Select.Content>
                </Select>
              </div>
              <div className="control">
                <label htmlFor="example">Example</label>
                <Select
                  id="example"
                  size="small"
                  value={example.id}
                  onValueChange={(id) => {
                    const next = examples.find((item) => item.id === id);
                    if (next) {
                      setCopyState("idle");
                      selectExample(next);
                    }
                  }}
                >
                  <Select.Trigger />
                  <Select.Content>
                    {examples.map(({ id, filename }) => (
                      <Select.Option key={id} value={id}>
                        {filename}
                      </Select.Option>
                    ))}
                  </Select.Content>
                </Select>
              </div>
            </div>
            <div className="pane-switcher">
              <SegmentedControl
                aria-label="Workspace view"
                size="small"
                value={pane}
                onValueChange={(value) => {
                  if (value === "source" || value === "preview") setPane(value);
                }}
              >
                <SegmentedControl.Item value="source">Source</SegmentedControl.Item>
                <SegmentedControl.Item value="preview">Preview</SegmentedControl.Item>
              </SegmentedControl>
            </div>
            <div className="control control--theme">
              <label htmlFor="code-theme">Code theme</label>
              <Select id="code-theme" size="small" value={preset} onValueChange={setPreset}>
                <Select.Trigger />
                <Select.Content>
                  {themes.map(({ id, name }) => (
                    <Select.Option key={id} value={id}>
                      {name}
                    </Select.Option>
                  ))}
                </Select.Content>
              </Select>
            </div>
          </div>

          <div className="workpanes" data-pane={pane}>
            <section className="pane pane--source" aria-labelledby="source-title">
              <div className="pane__heading">
                <h2 id="source-title">Source</h2>
                <div className="pane__actions">
                  <Tooltip>
                    <Tooltip.Trigger
                      disabled={source === example.source}
                      onClick={() => {
                        setCopyState("idle");
                        selectExample(example);
                      }}
                      render={(triggerProps) => (
                        <Button
                          {...triggerProps}
                          size="small"
                          variant="text"
                          iconOnly
                          aria-label="Reset to example"
                        >
                          <ResetIcon />
                        </Button>
                      )}
                    />
                    <Tooltip.Content size="small" placement="top">
                      Reset to example
                    </Tooltip.Content>
                  </Tooltip>
                  <Tooltip
                    closeOnClick={false}
                    onOpenChange={(open) => {
                      if (!open) setCopyState((state) => (state === "copied" ? "idle" : state));
                    }}
                  >
                    <Tooltip.Trigger
                      disabled={!source}
                      onClick={() => void copySource()}
                      render={(triggerProps) => (
                        <Button
                          {...triggerProps}
                          size="small"
                          variant="text"
                          iconOnly
                          aria-label="Copy source"
                        >
                          <CopyIcon />
                        </Button>
                      )}
                    />
                    <Tooltip.Content size="small" placement="top">
                      {copyState === "copied" ? "Copied!" : "Copy source"}
                    </Tooltip.Content>
                  </Tooltip>
                </div>
              </div>
              <Textarea
                className="source-editor"
                aria-label="Source code"
                aria-keyshortcuts="Control+Enter Meta+Enter"
                value={source}
                spellCheck={false}
                placeholder="Paste or type code"
                wrap="off"
                onChange={(event) => {
                  setCopyState("idle");
                  editSource(event.currentTarget.value, isComposing.current);
                }}
                onCompositionStart={(event) => {
                  isComposing.current = true;
                  editSource(event.currentTarget.value, true);
                }}
                onCompositionEnd={(event) => {
                  isComposing.current = false;
                  editSource(event.currentTarget.value);
                }}
                onKeyDown={handleEditorKeyDown}
              />
            </section>

            <section className="pane pane--preview" aria-labelledby="preview-title">
              <div className="pane__heading">
                <h2 id="preview-title">Preview</h2>
                <span
                  className="highlight-status"
                  data-state={preview.status}
                  data-performance={performanceLevel(elapsedMs)}
                  role="status"
                >
                  <span className="highlight-status__dot" aria-hidden="true" />
                  <span className="highlight-status__label">{statusLabel}</span>
                  <span className="highlight-status__divider" aria-hidden="true" />
                  <span className="highlight-status__latency">
                    {elapsedMs === undefined ? (
                      <span aria-hidden="true">—</span>
                    ) : (
                      <>
                        <strong>{elapsedMs}</strong> <span>ms</span>
                      </>
                    )}
                  </span>
                </span>
              </div>
              <div className="preview-code" aria-busy={busy}>
                {preview.status === "highlighted" ? (
                  <div dangerouslySetInnerHTML={{ __html: preview.html }} />
                ) : (
                  <pre className="nsh">
                    <code>{source}</code>
                  </pre>
                )}
              </div>
            </section>
          </div>

          {(preview.status === "error" || copyState === "error") && (
            <div className="workspace__footer">
              {preview.status === "error" && (
                <>
                  <span className="workspace__error" role="alert">
                    {preview.message}
                  </span>
                  <Button size="small" variant="text" onClick={runHighlight}>
                    Retry
                  </Button>
                </>
              )}
              {copyState === "error" && (
                <span role="alert">Select and copy the source manually.</span>
              )}
            </div>
          )}
        </Surface>
      </main>
    </LocaleProvider>
  );
}
