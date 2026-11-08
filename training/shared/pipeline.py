"""Freeze a bounded source corpus and compiler Gold outside the repository.

Sources are read, never executed. Golden/Playground roots are explicitly denied.
Every snapshot records source bytes, licenses, compiler and teacher provenance.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import platform
import shutil
import sys
import sysconfig
import tempfile
from training.shared.spec import REPOSITORY, current, file_hash, dumps
from training.shared.io import atomic_json, training_lock
from training.shared.encoding import Schema, encode

DENIED={'fixtures','tests','__pycache__','node_modules','.git','model','runtime','playground','challenges'}

def publish(root, area, identity, write):
    parent=root/area;parent.mkdir(parents=True,exist_ok=True)
    key=hashlib.sha256(dumps(identity).encode()).hexdigest();target=parent/key
    with training_lock(parent):
        if not target.exists():
            staging=Path(tempfile.mkdtemp(prefix='.staging-',dir=parent))
            try:
                manifest=write(staging)
                manifest.update(snapshot=key,identity=identity)
                manifest['checksums']={str(p.relative_to(staging)):file_hash(p) for p in sorted(staging.rglob('*')) if p.is_file()}
                atomic_json(staging/'sample.json',manifest);staging.rename(target)
            finally:
                if staging.exists():shutil.rmtree(staging)
        manifest=json.loads((target/'sample.json').read_text())
        for name,expected in manifest['checksums'].items():
            if file_hash(target/name)!=expected:raise ValueError('Corrupt immutable source/Gold snapshot')
        atomic_json(root/f'current-{"corpus" if area=="corpora" else area}.json',
                    {'directory':f'{area}/{key}','manifestHash':file_hash(target/'sample.json')})
    return target,manifest

def collect():
    spec=current();config_path=spec.directory/'dataset/sources.json'
    config=json.loads(config_path.read_text());records=[];locks=[]
    for entry in config['sources']:
        base={'repository':REPOSITORY,'dataset':spec.dataset_root.parent,'python-stdlib':Path(sysconfig.get_path('stdlib'))}[entry['base']]
        folder=(base/entry.get('path','')).resolve()
        if not folder.is_relative_to(base.resolve()):raise ValueError('Source outside declared root')
        license_path=(base/entry['license']).resolve()
        license_raw=license_path.read_bytes()
        paths=[folder/name for name in entry['files']] if 'files' in entry else sorted(folder.rglob('*'))
        chosen=[]
        for path in paths:
            if not path.is_file() or path.suffix not in entry.get('extensions',['.py']):continue
            relative=path.relative_to(folder)
            if set(relative.parts)&DENIED:continue
            if not path.resolve().is_relative_to(folder):raise ValueError('Source symlink escapes root')
            raw=path.read_bytes()
            if not raw or len(raw)>entry.get('maxBytes',50000):continue
            source=raw.decode('utf-8')
            if source.encode('utf-8')!=raw:raise ValueError('Source byte roundtrip failed')
            group=entry.get('groups',{}).get(relative.as_posix()) or entry.get('groupFamily') or relative.with_suffix('').as_posix()
            if entry.get('groupBy')=='directory':group=relative.parts[0]
            record={'repository':entry['id'],'path':relative.as_posix(),'sourceGroup':entry['id']+':'+group,
                    'documentKind':entry.get('documentKind',spec.document_kinds[0]),'profile':entry.get('profile',spec.profiles[0]),
                    'stream':entry.get('stream','natural'),'source':source,'contentHash':hashlib.sha256(raw).hexdigest()}
            records.append(record);chosen.append({k:record[k] for k in ('path','contentHash','sourceGroup')})
        if not chosen:raise ValueError('No usable source files: '+entry['id'])
        locks.append({'id':entry['id'],'root':str(folder),'files':chosen,'licenseFile':license_path.name,
                      'licenseSha256':hashlib.sha256(license_raw).hexdigest(),'licenseText':license_raw.decode('utf-8')})
    identity={'format':f'nsh-{spec.id}-corpus-v1','sourcesConfig':file_hash(config_path),'locks':locks,
              'collectorHash':file_hash(Path(__file__))}
    def write(directory):
        (directory/'sample.jsonl').write_text(''.join(dumps(record)+'\n' for record in records))
        atomic_json(directory/'source-locks.json',{'sources':locks})
        return {'format':identity['format'],'files':len(records),'bytes':sum(len(r['source'].encode()) for r in records)}
    return publish(spec.dataset_root,'corpora',identity,write)

def gold():
    spec=current();root=spec.dataset_root
    # Keep the established public pointer name alongside immutable corpora.
    pointer=json.loads((root/'current-corpus.json').read_text())
    folder=(root/pointer['directory']).resolve()
    if not folder.is_relative_to(root.resolve()) or file_hash(folder/'sample.json')!=pointer['manifestHash']:raise ValueError('Invalid corpus pointer')
    manifest=json.loads((folder/'sample.json').read_text())
    for name,expected in manifest['checksums'].items():
        if file_hash(folder/name)!=expected:raise ValueError('Corpus checksum mismatch')
    module=importlib.import_module(f'packs.{spec.id}.labeling.label')
    teacher_files={str(p.relative_to(REPOSITORY)):file_hash(p) for p in sorted((spec.directory/'labeling').rglob('*.py'))}
    provenance={'schemaHash':file_hash(spec.schema_path),'semanticContractHash':file_hash(spec.semantics_path),
                'teacherFiles':teacher_files,'compiler':{'implementation':platform.python_implementation(),
                'version':platform.python_version(),'executableSha256':file_hash(Path(sys.executable).resolve())}}
    if hasattr(module,'provenance'):provenance['teacherDependencies']=module.provenance()
    identity={'format':f'nsh-{spec.id}-gold-v1','corpusManifestHash':pointer['manifestHash'],'provenance':provenance,
              'pipelineHash':file_hash(Path(__file__))}
    schema=Schema.load(spec.schema_path)
    def write(directory):
        accepted=[];rejected=[]
        for record in map(json.loads,(folder/'sample.jsonl').read_text().splitlines()):
            try:
                result=module.label(source=record['source'],document_kind=record['documentKind'],profile=record['profile'])
                labeled={**record,'result':result,'features':result.get('features',[])}
                encode(labeled,schema);accepted.append(labeled)
            except (ValueError,SyntaxError,UnicodeError) as error:
                rejected.append({'repository':record['repository'],'path':record['path'],'contentHash':record['contentHash'],'error':str(error)})
        if not accepted:raise ValueError('No valid compiler Gold')
        (directory/'labeled-sample.jsonl').write_text(''.join(dumps(r)+'\n' for r in accepted))
        (directory/'rejected.jsonl').write_text(''.join(dumps(r)+'\n' for r in rejected))
        shutil.copyfile(folder/'source-locks.json',directory/'source-locks.json')
        return {'format':identity['format'],'files':len(accepted),'rejected':len(rejected),'provenance':provenance}
    return publish(root,'gold',identity,write)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['collect','label','validate'])
    args=parser.parse_args()
    if args.command=='collect':folder,manifest=collect()
    elif args.command=='label':folder,manifest=gold()
    else:
        spec=current();pointer=json.loads((spec.dataset_root/'current-gold.json').read_text());folder=spec.dataset_root/pointer['directory']
        if file_hash(folder/'sample.json')!=pointer['manifestHash']:raise ValueError('Gold manifest mismatch')
        manifest=json.loads((folder/'sample.json').read_text())
        for name,expected in manifest['checksums'].items():
            if file_hash(folder/name)!=expected:raise ValueError('Gold checksum mismatch')
        for record in map(json.loads,(folder/'labeled-sample.jsonl').read_text().splitlines()):encode(record,Schema.load(spec.schema_path))
    print(json.dumps({'directory':str(folder),'files':manifest['files'],'rejected':manifest.get('rejected',0)}))
