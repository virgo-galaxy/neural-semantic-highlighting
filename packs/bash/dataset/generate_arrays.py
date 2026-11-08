"""Original array tasks with portable positional-parameter counterparts."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

SH={
 'job-queue':'''jobs=(compile bundle upload)
for job in "${{jobs[@]}}"; do
    if [ "$job" != skip ]; then
        run_job "$job" --limit {n}
    fi
done
''',
 'append-files':'''files=(entry.log activity.log)
files+=(cache-{n}.log)
first="${{files[{idx}]}}"
for file in "${{files[@]}}"; do
    if [ "$file" = "$first" ]; then echo primary; else echo "$file"; fi
done
''',
 'visit-paths':'''paths=(src lib test)
{fn}() {{ printf 'Visit: %s\\n' "$1"; }}
for path in "${{paths[@]}}"; do
    if [ -d "$path" ]; then {fn} "$path"; fi
done
{fn} "done-{n}" --verbose
''',
 'sum-values':'''values=(2 {n} 9)
total=0
for value in "${{values[@]}}"; do
    if [ "$value" -gt 0 ]; then total=$((total + value)); fi
done
printf '%s\\n' "$total"
''',
 'choose-mode':'''modes=(draft preview release)
for mode in "${{modes[@]}}"; do
    case "$mode" in
        release) if [ -n "$mode" ]; then publish --version {n}; fi ;;
        *) printf '%s\\n' "$mode" ;;
    esac
done
''',
 'filter-files':'''inputs=(alpha.txt beta.txt gamma-{n}.txt)
for file in "${{inputs[@]}}"; do
    if [ -f "$file" ]; then
        head -n 1 "$file" | sort
    else
        printf 'Missing %s\\n' "$file"
    fi
done
''',
}
CSH={
 'job-queue':'''set jobs = ( compile bundle upload )
foreach job ( $jobs )
    if ( "$job" != skip ) then
        run_job "$job" --limit {n}
    endif
end
''',
 'append-files':'''set files = ( entry.log activity.log )
set files = ( $files cache-{n}.log )
set first = "$files[1]"
foreach file ( $files )
    if ( "$file" == "$first" ) then
        echo primary
    else
        echo "$file"
    endif
end
''',
 'visit-paths':'''set paths = ( src lib test )
alias {fn} 'echo Visit'
foreach path ( $paths )
    if ( -d "$path" ) then
        {fn} "$path"
    endif
end
{fn} "done-{n}" --verbose
''',
 'sum-values':'''set values = ( 2 {n} 9 )
@ total = 0
foreach value ( $values )
    if ( $value > 0 ) then
        @ total += $value
    endif
end
echo "$total"
''',
 'choose-mode':'''set modes = ( draft preview release )
foreach mode ( $modes )
    switch ( "$mode" )
    case release:
        if ( "$mode" != "" ) then
            publish --version {n}
        endif
        breaksw
    default:
        echo "$mode"
        breaksw
    endsw
end
''',
 'filter-files':'''set inputs = ( alpha.txt beta.txt gamma-{n}.txt )
foreach file ( $inputs )
    if ( -f "$file" ) then
        head -n 1 "$file" | sort
    else
        echo "Missing $file"
    endif
end
''',
}

def main():
    root=PackSpec.open('bash').dataset_root/'sources/array-programs-v1';files={}
    for number,profile in enumerate(['posix','bash','zsh','csh']):
        for family,template in (CSH if profile=='csh' else SH).items():
            for index in range(16):
                source=template.format(n=8+index+number*30,idx=0 if profile=='bash' else 1,fn=['emit','show','report','visit'][index%4])
                if profile=='posix':
                    import re
                    source=re.sub(r'^(?:jobs|files|paths|values|modes|inputs)=\(([^\n]*)\)',r'set -- \1',source,flags=re.M)
                    source=source.replace('files+=(cache-', 'set -- "$@" cache-')
                    source=re.sub(r'^(set -- .*cache-[^\n]*)\)$',r'\1',source,flags=re.M)
                    source=re.sub(r'\$\{(?:jobs|files|paths|values|modes|inputs)\[@\]\}',r'$@',source)
                    source=source.replace('${files[1]}','$1')
                elif profile in {'bash','zsh'} and index%2:
                    source=source.replace('if [ ','if [[ ').replace(' ]; then',' ]]; then')
                if index%3==1:source='\n'+source
                elif index%3==2:source=f'# Original {profile} collection task\n'+source
                if index%5==1:source=source.replace('\n','\r\n')
                files[f'{profile}/{family}/{index:02}.sh']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting collection programs. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve prior array task revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-shell-original-array-programs-v1','generatorHash':file_hash(Path(__file__)),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing array task lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'source programs')

if __name__=='__main__':main()
