# Frontend examples

A code fence can reuse an already registered language model.

```tsx title=Preview.tsx
export function Preview() {
  return <button type="button">Open docs</button>;
}
```

```json
{"theme": "default", "enabled": true, "languages": ["xml", "markdown"]}
```

```css
.preview {
  display: grid;
  gap: 16px;
  color: var(--foreground);
}
```

HTML in Markdown remains escaped source: <span class="note">a note</span>.
