"""Freeze a bounded host Perl core source/license capture; never execute modules."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec,file_hash

FILES='base.pm UNIVERSAL.pm NEXT.pm if.pm FindBin.pm XSLoader.pm less.pm blib.pm overload.pm feature.pm strict.pm warnings.pm constant.pm integer.pm locale.pm re.pm sort.pm sigtrap.pm subs.pm vars.pm utf8.pm vmsish.pm parent.pm English.pm Exporter.pm File/Basename.pm File/Compare.pm File/Copy.pm File/Find.pm File/Path.pm File/Spec.pm File/stat.pm Getopt/Std.pm Getopt/Long.pm IPC/Open2.pm IPC/Open3.pm Thread/Queue.pm Thread/Semaphore.pm Time/Local.pm Text/ParseWords.pm Text/Tabs.pm Text/Wrap.pm Tie/Array.pm Tie/Hash.pm Tie/Scalar.pm'.split()

def main():
    source=Path('/System/Library/Perl/5.34');root=PackSpec.open('perl').dataset_root/'sources/perl-5.34-core';files={}
    for name in FILES:
        path=source/name
        if path.is_file() and path.stat().st_size<=50000:
            raw=path.read_bytes();raw.decode('utf-8');files[name]=raw
    if len(files)<24:raise ValueError('Need the expected bounded host core source')
    for name in ['perlartistic.pod','perlgpl.pod']:files['licenses/'+name]=(source/'pods'/name).read_bytes()
    files['LICENSE']=(b'This capture retains Perl core source under the terms of Perl itself.\nSee the complete original Artistic/GPL texts in licenses/.\n\n'+files['licenses/perlartistic.pod']+b'\n'+files['licenses/perlgpl.pod'])
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing captured core revision')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-perl-host-core-source-v1','origin':str(source),'collectorHash':file_hash(Path(__file__)),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Host source lock changed; create another revision')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-3,'core modules')

if __name__=='__main__':main()
