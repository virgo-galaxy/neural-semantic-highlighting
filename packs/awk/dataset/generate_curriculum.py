"""Original bounded AWK snippets and mixed tasks, with varied source positions."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

TASKS={
 'phase-fields':'BEGIN {{ FS = ","; OFS = "\\t" }}\nNR > 1 {{ print $1, $3 }}\nEND {{ print NR, "records-{n}" }}\n',
 'sum-records':'{{ total += $2; count++ }}\nEND {{ printf "sum=%g count=%d\\n", total, count }}\n',
 'pattern-actions':'/^[[:alpha:]]/ {{ print NR, $0 }}\n$2 ~ /ready|pending/ {{ accepted++ }}\nEND {{ print accepted + {n} }}\n',
 'array-counts':'{{ counts[$1]++ }}\nEND {{ for (word in counts) print word, counts[word] }}\n',
 'array-delete':'{{ values[$1] = $2 }}\nEND {{ for (key in values) {{ if (values[key] < {n}) delete values[key]; else print key }} }}\n',
 'indexed-loop':'BEGIN {{\n  for (i = 1; i <= {n}; i++) {{ values[i] = i * 2 }}\n  for (i = 1; i <= {n}; i++) print values[i]\n}}\n',
 'while-loop':'BEGIN {{ x = {n}; while (x > 0) {{ print x; x-- }} }}\n',
 'do-loop':'BEGIN {{ x = 0; do {{ x++; printf "%d\\n", x }} while (x < {n}) }}\n',
 'conditional-fields':'{{ if ($2 >= {n}) print $1; else if (NF > 3) print $4; else next }}\n',
 'range-pattern':'/^START/ , /^STOP/ {{ print FNR, $0 }}\nEND {{ print "finished-{n}" }}\n',
 'function-trim':'function {fn}(text) {{ gsub(/^[[:space:]]+|[[:space:]]+$/, "", text); return text }}\nNF {{ print {fn}($0) }}\n',
 'function-score':'function {fn}(value, limit) {{ if (value > limit) return value * 2; return value }}\n{{ print {fn}($2, {n}) }}\n',
 'function-array':'function {fn}(items,    key, total) {{\n  total = 0\n  for (key in items) total += items[key]\n  return total\n}}\n{{ scores[$1] += $2 }}\nEND {{ print {fn}(scores) }}\n',
 'function-slug':'function {fn}(text) {{ gsub(/[[:space:]]+/, "-", text); return tolower(text) }}\n$1 !~ /^#/ {{ print {fn}($1), {n} }}\n',
 'function-clamp':'function {fn}(value, low, high) {{ return value < low ? low : value > high ? high : value }}\n{{ print {fn}($3, 0, {n}) }}\n',
 'function-predicate':'function {fn}(text) {{ return text ~ /^[a-z][a-z0-9_]*$/ }}\n{{ if ({fn}($1)) print $0; else invalid++ }}\nEND {{ print invalid }}\n',
 'split-fields':'{{ n = split($0, parts, /[:,]/); for (i = 1; i <= n; i++) print parts[i] }}\n',
 'match-groups':'{{ if (match($0, /[0-9]+/)) print substr($0, RSTART, RLENGTH), {n} }}\n',
 'substitution':'{{ text = $0; sub(/^prefix:/, "", text); gsub(/ +/, "_", text); print text }}\n',
 'numeric-format':'BEGIN {{ value = sqrt({n}); printf "%0.3f %d\\n", value, int(value) }}\n',
 'field-computation':'{{ column = {n}; print $column, $(column + 1), $NF }}\n',
 'getline-input':'BEGIN {{ while ((getline line < "input-{n}.txt") > 0) {{ if (line !~ /^#/) print line }}; close("input-{n}.txt") }}\n',
 'printf-output':'BEGIN {{ OFS = "," }}\n{{ printf "%s,%0.2f\\n", $1, $2 / {n} }}\n',
 'regex-division':'$0 ~ /https?:\\/\\// {{ ratio = $3 / {n}; print $1, ratio }}\n',
 'unicode-text':'BEGIN {{ label = "星空 🌌 {n}"; print label }}\n{{ print $0, "你好 🚀" }}\n',
 'gnu-file-phases':'BEGINFILE {{ count = 0 }}\nNF > 1 {{ count++; if ($2 ~ /^[0-9]+$/) sum += $2 }}\nENDFILE {{ print FILENAME, count, sum + {n} }}\n',
 'gnu-array-sort':'{{ values[$1] = $2 }}\nEND {{ n = asorti(values, keys); for (i = 1; i <= n; i++) print keys[i], values[keys[i]] }}\n',
 'gnu-switch':'{{ switch ($1) {{ case "ready": print $2; break; case /warn/: print NR; break; default: print "other-{n}" }} }}\n',
 'gnu-namespace':'@namespace "preview"\nfunction {fn}(text) {{ return awk::toupper(text) }}\n{{ print preview::{fn}($1), {n} }}\n',
 'gnu-typed-regex':'BEGIN {{ rule = @/^[A-Z][a-z]+$/ }}\n{{ if ($1 ~ rule) print $0; else rejected += {n} }}\n',
}

def main():
    root=PackSpec.open('awk').dataset_root/'sources/curriculum-v1';files={}
    for family,template in TASKS.items():
        for index in range(20):
            source=template.format(n=index+3,fn=['normalize','convert','render','clamp','select'][index%5])
            position=(index//5)%4
            if position==1:source='# Original AWK task\n'+source
            elif position==2:source='\n'+source
            elif position==3:source='BEGIN { OFS = "|" }\n'+source
            if index%3==1:source=source.replace('\n','\r\n')
            files[f'{family}/{index:02}.awk']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting AWK curriculum. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing AWK source revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-awk-original-curriculum-v1','generatorHash':file_hash(Path(__file__)),'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Original AWK lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'original AWK programs')

if __name__=='__main__':main()
