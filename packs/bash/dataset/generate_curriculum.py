"""Original grouped Shell grammar examples, independent of Golden/Playground."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec, file_hash

SH={
 'assignments':'name="entry-{n}"\npath=${{ROOT:-/tmp}}\nexport LABEL=ready\nprintf "%s\\n" "$name"\n',
 'commands':'mkdir -p "build-{n}"\ncp -- source.txt "build-{n}/input.txt"\nprintf done\n',
 'conditionals':'if [ -f "$path" ]; then\n    printf "%s\\n" ready\nelse\n    echo missing\nfi\n',
 'loops':'for entry in alpha beta gamma; do\n    printf "%s\\n" "$entry"\ndone\n',
 'branches':'case "$mode" in\n    ready|active) echo yes ;;\n    *) echo unknown ;;\nesac\n',
 'callables':'task_{n}() {{\n    local item="note-{n}"\n    printf "%s\\n" "$item"\n}}\ntask_{n}\n',
 'quoting':"literal='price $5'\nmessage=\"Hello $USER\"\nprintf '%s\\n' \"$literal\" \"$message\"\n",
 'substitution':'result=$(printf "%s" "entry-{n}")\nname=`basename "$path"`\necho "$result" "$name"\n',
 'arithmetic':'count={n}\nnext=$((count + 2))\necho "$next"\n',
 'pipelines':'printf "%s\\n" alpha beta | sort | uniq\ncat<input.txt>output.txt\n',
 'parameters':'target=${{1:-default}}\nlabel=${{target%.*}}\nprintf "%s" "$label"\n',
 'environment':'TOKEN="$token" command-tool --count {n}\nexport MODE=release\necho "$MODE"\n',
 'comments':'# 原始注释 🌌\nmessage="你好 🚀"\nprintf "%s\\n" "$message" # visible comment\n',
 'multiline':'cat <<DOCUMENT\nAn original entry {n}.\nThis is literal document content.\nDOCUMENT\necho ready\n',
 'groups':'( printf "%s" child; echo ready )\n{{ echo outer; }}\n',
 'while':'index=0\nwhile [ "$index" -lt {n} ]; do\n    index=$((index + 1))\ndone\n',
}
CSH={
 'assignments':'set name = "entry-{n}"\nset path = /tmp\nsetenv LABEL ready\necho "$name"\n',
 'commands':'mkdir -p "build-{n}"\ncp source.txt "build-{n}/input.txt"\necho done\n',
 'conditionals':'if ( -f "$path" ) then\n    echo ready\nelse\n    echo missing\nendif\n',
 'loops':'foreach entry ( alpha beta gamma )\n    echo "$entry"\nend\n',
 'branches':'switch ( "$mode" )\ncase ready:\n    echo yes\n    breaksw\ndefault:\n    echo unknown\n    breaksw\nendsw\n',
 'callables':"alias task_{n} 'echo ready'\ntask_{n}\n",
 'quoting':"set literal = 'price $5'\nset message = \"Hello $USER\"\necho \"$literal\" \"$message\"\n",
 'substitution':'set result = `printf "%s" "entry-{n}"`\nset name = `basename "$path"`\necho "$result" "$name"\n',
 'arithmetic':'@ count = {n}\n@ next = ( $count + 2 )\necho "$next"\n',
 'pipelines':'printf "%s\\n" alpha beta | sort | uniq\ncat<input.txt>output.txt\n',
 'parameters':'set target = $argv[1]\necho "$target" "$status"\n',
 'environment':'setenv MODE release\ncommand-tool --count {n}\necho "$MODE"\n',
 'comments':'# 原始注释 🌌\nset message = "你好 🚀"\necho "$message" # visible comment\n',
 'multiline':"set text = 'An original entry {n}.'\necho \"$text\"\necho 'Second independent line.'\n",
 'groups':'( printf "%s" child; echo ready )\necho outer\n',
 'while':'@ index = 0\nwhile ( $index < {n} )\n    @ index += 1\nend\n',
}

def main():
    root=PackSpec.open('bash').dataset_root/'sources/curriculum-v1';files={}
    for profile in ['posix','bash','zsh','csh']:
        for family,template in (CSH if profile=='csh' else SH).items():
            # POSIX functions omit the optional local builtin.
            if profile=='posix':template=template.replace('local item=','item=')
            for index in range(12):
                body=template.format(n=index+3)
                header=f'# Original {profile} example, {family}, variant {index}\n'
                if index%3==1:body='\n'+body
                if index%3==2:body='# Independent source layout\n\n'+body
                source=header+body
                if index%5==1:source=source.replace('\n','\r\n')
                files[f'{profile}/{family}/{index:02}.sh']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting curriculum. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous curriculum; use a new revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-shell-original-curriculum-v1','generatorHash':file_hash(Path(__file__)),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing curriculum lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'source files')

if __name__=='__main__':main()
