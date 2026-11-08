"""Small original modern-HTML grammar curriculum, separate from real-source evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def digest(raw): return hashlib.sha256(raw).hexdigest()


def examples(index: int) -> dict[str, str]:
    n = index + 10
    title = f"Example {n} — 星 🌌"
    doctype = "<!doctype html>\n"
    js = f'''const label{n} = '<strong data-note="ready">{title}</strong>';
const items{n} = [1, 2, 3];
document.querySelector("main").innerHTML = label{n};
'''
    css = f'''.panel-{n} {{ padding: {n}px; color: #3157ab; }}
.panel-{n}::before {{ content: "<span>ready</span>"; }}
'''
    long_js = "\n".join(f'const value{n}_{i} = {{ name: "item-{i}", enabled: true }};' for i in range(10 + index % 9))
    long_css = "\n".join(f'.row-{i} {{ margin: {i}px; color: rgb({i}, 40, 80); }}' for i in range(12 + index % 9))
    data = json.dumps({"name": title, "description": "<p>plain data</p>", "items": list(range(8 + index % 7))}, ensure_ascii=False)
    variants = {
        "attribute-forms": doctype + f'<section><input type=email required value="user{n}&amp;team"><button disabled data-count={n} aria-label=\'Open panel\'>Continue {n}</button></section>',
        "strings-and-entities": doctype + f'<article class="grid sm:grid-cols-2 hover:bg-sky-600" title="A &quot;quoted&quot; value {n}"><p>{title} &amp; notes &lt; limit &#x1f680;</p></article>',
        "comments-and-text": doctype + f'<!-- Header {title} -->\n<main><p>Read <b>part {n}</b> and <i>notes</i>.</p><!-- end {n} --><small>Updated today</small></main>',
        "rcdata": doctype + f'<title>View {n} &amp; notes</title><textarea name=message>\n<strong>literal {n}</strong> &copy; {title}</textarea>',
        "foreign-content": doctype + f'<svg role=img viewBox="0 0 24 24"><title>Icon {n}</title><path d="M0 0L{n} 20"/><text><![CDATA[x &amp; y < {n}]]></text></svg><math><mrow><mi>x</mi><mo>+</mo><mn>{n}</mn></mrow></math>',
        "custom-shadow": doctype + f'<app-panel><template shadowrootmode=open><style>{css}</style><slot name=heading>Default {n}</slot><span part=status>Ready</span></template><h2 slot=heading>{title}</h2></app-panel>',
        "javascript-strings": doctype + f'<main id=content>{title}</main><script type="module">\n{js}</script>',
        "css-strings": doctype + f'<style>\n{css}</style><article class="panel-{n}" data-size={n}>Card {n}</article>',
        "typed-data": doctype + f'<script type="application/ld+json">{data}</script><aside><p>{title}</p></aside><script>const result{n} = {n};</script>',
        "import-map": doctype + f'<script type="importmap">{{"imports":{{"demo-{n}":"./demo-{n}.js"}}}}</script><script type="application/ld+json">{data}</script><script type=module>import "demo-{n}";</script><p>{title}</p>',
        "long-bodies": doctype + f'<style>\n{long_css}\n</style><main><h1>{title}</h1><p>Content remains markup.</p></main><script>\n{long_js}\n</script>',
        "forms-and-dialog": doctype + f'<dialog id="panel-{n}" open><form method=dialog><label>Count <input type=number min=0 max={n} value={index}></label><textarea name=notes><em>literal {n}</em> &gt; notes</textarea><button autofocus>Accept</button></form></dialog><details name=help><summary>Details {n}</summary><p>{title}</p></details>',
        "inline-code": doctype + f'<button class="md:hover:opacity-75" style="color: rgb(40, 50, {n})" onclick="console.log(&quot;item-{n}&quot;)">{title}</button><output for=result>Result {n}</output>',
        "long-attributes": doctype + '<section><div class="' + " ".join(["px-4 py-2 rounded-lg hover:bg-blue-500 md:grid-cols-2"] * (8 + index % 9)) + f'" data-key="{n}">{title}</div><p>After the quoted value</p></section>',
    }
    return {family: text.replace("\n", "\r\n") if index % 3 == 0 else text for family, text in variants.items()}


def generate(target: Path, variants: int = 24):
    if not 4 <= variants <= 128: raise ValueError("Use a bounded curriculum with 4..128 variants per family")
    identity = {"kind": "original-modern-html-curriculum", "generatorHash": digest(Path(__file__).read_bytes()),
                "variantsPerFamily": variants, "version": 2}
    if target.exists():
        saved = json.loads((target / "source.lock.json").read_text())
        if saved["identity"] != identity: raise ValueError("Preserve the existing curriculum; choose a new output directory")
        for name, expected in saved["files"].items():
            path = target / name
            if not path.resolve().is_relative_to(target.resolve()) or digest(path.read_bytes()) != expected:
                raise ValueError("Immutable curriculum was modified")
        print("Reused curriculum:", target)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".curriculum-", dir=target.parent))
    try:
        files = {}
        for index in range(variants):
            for family, source in examples(index).items():
                relative = f"{family}/example-{index:03d}.html"
                path = staging / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                raw = source.encode()
                path.write_bytes(raw)
                files[relative] = digest(raw)
        lock = {**identity, "identity": identity, "spec": {"name": "nsh-html-curriculum", "version": "2"},
                "integrity": "sha256:" + digest(json.dumps(identity, sort_keys=True).encode()), "files": dict(sorted(files.items()))}
        (staging / "source.lock.json").write_text(json.dumps(lock, indent=2) + "\n")
        staging.rename(target)
        print(f"Generated {len(files)} curriculum HTML documents: {target}")
    finally:
        if staging.exists(): shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(os.environ.get("NSH_DATASET_ROOT", "~/Datasets/neural-semantic-highlighting")).expanduser() / "html/sources/curriculum-v2")
    parser.add_argument("--variants", type=int, default=24)
    args = parser.parse_args()
    generate(args.output.expanduser().resolve(), args.variants)


if __name__ == "__main__": main()
