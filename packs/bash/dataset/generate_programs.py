"""Mixed-feature programs: hold out whole tasks without holding out a syntax."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec,file_hash

SH={
 'copy-assets':'''destination="build-{n}"
mkdir -p "$destination"
for source in draft release archive; do
    if [ -f "$source" ]; then
        cp "$source" "$destination/"
    else
        printf '%s\\n' "$source missing"
    fi
done
''',
 'count-records':'''total=0
for value in 2 5 {n}; do
    total=$((total + value))
    if [ "$value" -gt 3 ]; then
        printf '%s\\n' "$value"
    fi
done
printf 'Total: %s\\n' "$total"
''',
 'run-targets':'''{fn}() {{
    printf 'Preparing %s\\n' "$1"
}}
for target in client server worker; do
    if {fn} "$target"; then
        printf '%s\\n' "built-{n}: $target"
    fi
done
''',
 'retry-worker':'''attempt=0
while [ "$attempt" -lt {n} ]; do
    if run_job "$attempt"; then
        echo finished
        break
    fi
    attempt=$((attempt + 1))
done
''',
 'select-profile':'''profile=${{1:-release}}
for service in api web queue; do
    case "$profile" in
        release) if [ -n "$service" ]; then publish "$service" --tag {n}; fi ;;
        *) printf '%s\\n' "preview: $service" ;;
    esac
done
''',
 'read-arguments':'''output="args-{n}.txt"
for argument in "$@"; do
    if [ "$argument" = --help ]; then
        printf '%s\\n' usage
    else
        printf '%s\\n' "$argument" >> "$output"
    fi
done
''',
 'format-labels':'''{fn}() {{ printf '%s\\n' "$1" | tr a-z A-Z; }}
for label in alpha beta omega; do
    result=$({fn} "$label")
    if [ -n "$result" ]; then
        printf '%s: %s\\n' {n} "$result"
    fi
done
''',
 'check-sources':'''root=${{1:-source-{n}}}
for path in "$root"/*; do
    if [ -f "$path" ]; then
        head -n 1 "$path" | grep -- ready
    else
        echo "skip: $path"
    fi
done
''',
}
CSH={
 'copy-assets':'''set destination = "build-{n}"
mkdir -p "$destination"
foreach source ( draft release archive )
    if ( -f "$source" ) then
        cp "$source" "$destination/"
    else
        echo "$source missing"
    endif
end
''',
 'count-records':'''@ total = 0
foreach value ( 2 5 {n} )
    @ total += $value
    if ( $value > 3 ) then
        echo "$value"
    endif
end
echo "Total: $total"
''',
 'run-targets':'''alias {fn} 'echo Preparing'
foreach target ( client server worker )
    {fn} "$target"
    if ( $status == 0 ) then
        echo "built-{n}: $target"
    endif
end
''',
 'retry-worker':'''@ attempt = 0
while ( $attempt < {n} )
    run_job "$attempt"
    if ( $status == 0 ) then
        echo finished
        break
    endif
    @ attempt += 1
end
''',
 'select-profile':'''set profile = release
foreach service ( api web queue )
    switch ( "$profile" )
    case release:
        if ( "$service" != "" ) then
            publish "$service" --tag {n}
        endif
        breaksw
    default:
        echo "preview: $service"
        breaksw
    endsw
end
''',
 'read-arguments':'''set output = "args-{n}.txt"
foreach argument ( $argv )
    if ( "$argument" == --help ) then
        echo usage
    else
        echo "$argument" >> "$output"
    endif
end
''',
 'format-labels':'''alias {fn} 'printf "%s\\n"'
foreach label ( alpha beta omega )
    set result = `{fn} "$label" | tr a-z A-Z`
    if ( "$result" != "" ) then
        echo "{n}: $result"
    endif
end
''',
 'check-sources':'''set root = "source-{n}"
foreach path ( "$root"/* )
    if ( -f "$path" ) then
        head -n 1 "$path" | grep -- ready
    else
        echo "skip: $path"
    endif
end
''',
}

def main():
    root=PackSpec.open('bash').dataset_root/'sources/programs-v1';files={}
    for number,profile in enumerate(['posix','bash','zsh','csh']):
        for family,template in (CSH if profile=='csh' else SH).items():
            for index in range(18):
                source=template.format(n=4+index+number*30,fn=['emit','prepare','show','describe','report','process'][index%6])
                if profile in {'bash','zsh'} and index%2:
                    source=source.replace('if [ ','if [[ ').replace(' ]; then',' ]]; then')
                if index%3==1:source='\n'+source
                elif index%3==2:source=f'# Original {profile} program\n'+source
                if index%5==1:source=source.replace('\n','\r\n')
                files[f'{profile}/{family}/{index:02}.sh']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting mixed-feature programs. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing program revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-shell-original-programs-v1','generatorHash':file_hash(Path(__file__)),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing program lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'source programs')

if __name__=='__main__':main()
