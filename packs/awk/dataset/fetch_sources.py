"""Select original GNU AWK example/library source and licenses, without install."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
from training.shared.spec import PackSpec,REPOSITORY,file_hash

VERSION='5.4.1'
URL='https://ftp.gnu.org/gnu/gawk/gawk-5.4.1.tar.xz'
SHA256='07f6f7342b7febe4313fc2c2542ad93d64fe20ad8717200109f105a826f5fd37'

def main():
    archive=REPOSITORY/'artifacts/tools'/f'gawk-{VERSION}.tar.xz';archive.parent.mkdir(parents=True,exist_ok=True)
    if not archive.exists():
        raw=subprocess.check_output(['curl','--fail','--silent','--show-error','--location',URL])
        if hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError('GNU AWK archive hash differs')
        archive.write_bytes(raw)
    if file_hash(archive)!=SHA256:raise ValueError('Cached GNU AWK archive changed')
    root=PackSpec.open('awk').dataset_root/'sources'/f'gawk-{VERSION}';files={}
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            if not member.isfile():continue
            name=member.name.removeprefix(f'gawk-{VERSION}/')
            if not (name=='COPYING' or name.startswith('awklib/eg/') and name.endswith('.awk') and member.size<=30000):continue
            raw=bundle.extractfile(member).read();raw.decode('utf-8');files[name]=raw
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe source path')
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous GNU AWK capture')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-awk-gnu-source-v1','version':VERSION,'url':URL,'archiveSha256':SHA256,'collectorHash':file_hash(Path(__file__)),'files':{n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Source lock changed')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'AWK programs/libraries')

if __name__=='__main__':main()
