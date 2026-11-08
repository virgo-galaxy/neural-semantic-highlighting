"""Small original mixed Here Document tasks; preserve all earlier revisions."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec, file_hash

BODIES = {
    'emit-config': 'service: virgo-{n}\nroot: $workspace\n# {end} inside a comment is not the terminator\n',
    'render-page': '<section class="preview">\n  <h1>Hello $name</h1>\n  <p>build {n}: $(date)</p>\n</section>\n',
    'write-note': 'Hello $USER,\nThe {end} marker belongs on its own line.\nRelease {n} is ready; quotes " and apostrophes \' stay here.\n',
    'query-input': 'SELECT name, score FROM records\nWHERE score > {n} AND owner = \'$user\';\n-- $(echo example) stays inside this input\n',
    'help-body': 'Usage: tool --mode MODE\n  --limit {n}    maximum entries\nExamples: tool | sort; echo "$value"\n',
    'check-lines': 'alpha-{n}\nbeta $value\nnot-{end}-yet\n$(printf ignored)\n',
    'show-template': 'function fake() {{ echo literal; }}\n${{missing:-fallback}}\nvalue={n}; # this is body text\n',
    'save-manifest': '{{\n  "name": "virgo-{n}",\n  "command": "$(not_a_command)",\n  "message": "星空 🌌 $name"\n}}\n',
}

# Different surrounding programs keep whole-string bodies from becoming the
# same identifier-normalized template across independent task families.
CONTEXTS = {
    'emit-config': ('workspace=${WORKSPACE:-/tmp/preview}\nexport workspace\n', 'test -f preview.txt && echo saved\n'),
    'render-page': ('for page in home about; do\nprintf \'Page %s\\n\' "$page"\n', 'done\n'),
    'write-note': ('recipient=$1\nif [ -z "$recipient" ]; then exit 1; fi\n', 'printf \'Sent to %s\\n\' "$recipient"\n'),
    'query-input': ('set -f\n', 'status=$?\nif [ "$status" -ne 0 ]; then echo failed; fi\n'),
    'help-body': ('case "$1" in\n--help)\n', ';;\n*) echo unknown ;;\nesac\n'),
    'check-lines': ('count=0\nwhile [ "$count" -lt 2 ]; do\n', 'count=$((count + 1))\ndone\n'),
    'show-template': ('(\ncd /tmp || exit 1\n', ')\necho finished\n'),
    'save-manifest': ('mkdir -p output\nif [ -d output ]; then\n', 'else\necho unavailable\nfi\n'),
}


def main():
    root = PackSpec.open('bash').dataset_root / 'sources/heredoc-programs-v2'
    files = {}
    for profile in ['posix', 'bash', 'zsh']:
        for family, body in BODIES.items():
            for index in range(24):
                end = ['EOF', 'CONFIG', 'MESSAGE', 'END_INPUT', 'DATA', 'PAGE'][index % 6]
                form = index % 4
                word = end if form == 0 else "'" + end + "'" if form == 1 else '"' + end + '"' if form == 2 else end
                intro = '<<-' if form == 3 else '<<'
                content = body.format(n=17 + index, end=end)
                if form == 3: content = ''.join('\t' + line for line in content.splitlines(keepends=True))
                terminator = ('\t' if form == 3 else '') + end
                command = ['cat', 'cat > preview.txt', 'tee output.txt', 'sed -n \'1,3p\''][index % 4]
                source = f'{command} {intro}{word}\n{content}{terminator}\n'
                before, after = CONTEXTS[family]
                source = before + source + after
                # Both function-keyword forms, portable definitions and direct
                # snippets occur in every task family, never a held-out concept.
                if index % 3 == 1:
                    function = ['emit_preview', 'show_input', 'write_output'][index % 3]
                    declaration = function + '()' if profile == 'posix' else 'function ' + function + ('()' if index % 2 else '')
                    source = declaration + ' {\n' + source + '}\n' + function + '\n'
                elif index % 3 == 2:
                    source = 'if [ -n "$workspace" ]; then\n' + source + 'fi\n'
                source += ['echo complete\n', 'printf \'%s\\n\' "ready"\n', 'pwd\n'][index % 3]
                if index % 6 == 2: source = '# Original heredoc task\n' + source
                if index % 7 == 4: source = source.replace('\n', '\r\n')
                files[f'{profile}/{family}/{index:02}.sh'] = source.encode()
    files['LICENSE'] = b'Original private neural-semantic-highlighting Here Document programs. No additional license grant.\n'
    root.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        path = root / name
        if path.exists() and path.read_bytes() != raw: raise ValueError('Preserve existing heredoc revision')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    lock = {'format': 'nsh-shell-original-heredocs-v2', 'generatorHash': file_hash(Path(__file__)),
            'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}}
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != lock: raise ValueError('Existing heredoc lock differs')
    path.write_text(json.dumps(lock, indent=2) + '\n')
    print(root, len(files) - 1, 'source programs')


if __name__ == '__main__': main()
