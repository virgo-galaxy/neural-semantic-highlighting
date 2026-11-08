"""Short original Here Documents with code-like body openings and real suffixes."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec, file_hash

TEMPLATES = {
    'print-status': 'cat {doc}\necho complete\nexit 0\n',
    'show-directory': 'cat {doc}\npwd\n',
    'print-summary': 'title=preview\ncat {doc}\nprintf \'%s\\n\' "$title"\n',
    'count-input': 'cat {doc}\nwc -l input.txt\n',
    'filter-input': 'sed -n \'1,2p\' {doc}\necho filtered\n',
    'save-output': 'cat {intro} > output.txt\n{body}{end}\nprintf \'%s\\n\' saved\n',
    'read-values': 'read -r first {doc}\necho "$first"\n',
    'function-input': '{definition} {{\ncat {doc}\n}}\n{fn} --brief\n',
    'conditional-input': 'if [ -n "$1" ]; then\ncat {doc}\nfi\necho checked\n',
    'repeat-input': 'for file in alpha beta; do\ncat {doc}\ndone\n',
    'number-lines': 'cat -n {doc}\ntrue\n',
    'append-output': 'cat {intro} >> report.txt\n{body}{end}\n: recorded\n',
}


def main():
    root = PackSpec.open('bash').dataset_root / 'sources/heredoc-fragments-v2'
    files = {}
    for profile in ['posix', 'bash', 'zsh']:
        for family, template in TEMPLATES.items():
            for index in range(24):
                marker = ['END', 'BLOCK', 'CONTENT', 'PAYLOAD', 'STOP', 'FINISH'][index % 6]
                form = index % 4
                word = marker if form == 0 else "'" + marker + "'" if form == 1 else '"' + marker + '"' if form == 2 else marker
                intro = ('<<-' if form == 3 else '<<') + word
                body = [
                    f'$user ${{path:-/tmp/{index}}} $(printf sample)\nRelease {index} is ready.\n',
                    f'"double" and \'single\' `backticks`\nif [ -n "$item" ]; then echo {index}; fi\n',
                    f'${{setting:-default}}\nconst value = "{index}"; // body text\n',
                    f'$(date) is literal here when quoted\n<article>星空 🌌 {index}</article>\n',
                    f'# {marker} is only part of this line\nHello $USER, build {index}\n',
                    f'function example() {{ return {index}; }}\nname: $name\n',
                ][(index // 4) % 6]
                end = marker
                if form == 3:
                    body = ''.join('\t' + line for line in body.splitlines(keepends=True)); end = '\t' + marker
                fn = ['emit_text', 'show_block', 'write_message'][index % 3]
                definition = fn + '()' if profile == 'posix' else 'function ' + fn + ('()' if index % 2 else '')
                source = template.format(doc=intro+'\n'+body+end, intro=intro, body=body, end=end, fn=fn, definition=definition)
                if index % 5 == 3: source = source.replace('\n', '\r\n')
                files[f'{profile}/{family}/{index:02}.sh'] = source.encode()
    files['LICENSE'] = b'Original private neural-semantic-highlighting Here Document fragments. No additional license grant.\n'
    root.mkdir(parents=True, exist_ok=True)
    for name, raw in files.items():
        path = root / name
        if path.exists() and path.read_bytes() != raw: raise ValueError('Preserve prior heredoc fragments')
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    lock = {'format': 'nsh-shell-original-heredoc-fragments-v2', 'generatorHash': file_hash(Path(__file__)),
            'files': {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}}
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != lock: raise ValueError('Existing fragment lock differs')
    path.write_text(json.dumps(lock, indent=2)+'\n'); print(root, len(files)-1, 'source fragments')


if __name__ == '__main__': main()
