"""Small original positional/opaque-body revision in existing frozen families."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash
from .generate_curriculum import TASKS

FAMILIES=['heredoc-single','heredoc-double','heredoc-indent','heredoc-queue','heredoc-function','heredoc-lines','function-arguments','quote-forms','pod-function','data-section']

def main():
    root=PackSpec.open('perl').dataset_root/'sources/fragments-v2';files={}
    for family in FAMILIES:
        for index in range(64):
            source=TASKS[family].format(n=31+index,fn=['emit','report','display','summarize','transform'][index%5],pkg='App::Item')
            if family=='heredoc-indent':
                indent=['  ','    ','\t','        '][index%4]
                content=['$path ${name} and $(sample) are literal', '"double" and \'single\' quotes remain text', 'my $fake = 1; # body code', '星空 🌌 $value'][(index//4)%4]
                source=f"my $note = <<~'NOTE';\n{indent}{content}\n{indent}revision {31+index}\n{indent}NOTE\nprintf '%s', $note;\n"
            elif family in {'heredoc-single','heredoc-double'}:
                source=source.replace('$name and $(literal) build', '${path} $user $(example) build').replace('Hello $name, version','${name} starts the line, version')
            if (index//16)%4==1:source='# Original short Perl task\n'+source
            elif (index//16)%4==2:source='\n'+source
            elif (index//16)%4==3:source='=pod\n\nShort original source notes.\n\n=cut\n\n'+source
            if index%5==2:source=source.replace('\n','\r\n')
            files[f'{family}/{index:02}.pl']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting Perl fragments. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous Perl fragment revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-perl-original-fragments-v2','generatorHash':file_hash(Path(__file__)),'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing fragment lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'original fragments')

if __name__=='__main__':main()
