"""Offline BuildKit-checked original Dockerfile spans. Never imported by runtime."""
from __future__ import annotations

import atexit
from functools import lru_cache
import json
import re
import subprocess
import threading

from . import tools

_process = None
_lock = threading.Lock()
VARIABLE = re.compile(r'\$(?:\{(?:[^{}]|\{[^{}]*\})*\}|[A-Za-z_][A-Za-z_0-9]*|[0-9@*#?$!\-])')
NUMBER = re.compile(r'[+-]?(?:0[xX][\da-fA-F]+|\d+(?:\.\d+)?)\Z')
COMMANDS = {'add','arg','cmd','copy','entrypoint','env','expose','from','healthcheck','label',
            'maintainer','onbuild','run','shell','stopsignal','user','volume','workdir'}


def close():
    global _process
    if _process is not None:
        _process.stdin.close()
        try: _process.wait(timeout=5)
        except subprocess.TimeoutExpired: _process.terminate(); _process.wait(timeout=5)
        _process = None


atexit.register(close)


@lru_cache(maxsize=1)
def provenance():
    from packs.bash.labeling.label import provenance as shell_provenance
    from packs.json.labeling.tools import provenance as json_provenance
    return dict(parser=tools.provenance(), shell=shell_provenance(), json=json_provenance(),
                parseOnly=True, sourceExecution=False, runtimeParserRequired=False)


def parse(source):
    global _process
    provenance()
    with _lock:
        if _process is None or _process.poll() is not None:
            _process = subprocess.Popen([str(tools.binary())], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        text=True, encoding='utf-8')
        _process.stdin.write(json.dumps(dict(source=source), ensure_ascii=True) + '\n'); _process.stdin.flush()
        line = _process.stdout.readline()
        if not line: raise RuntimeError('Official Dockerfile parser stopped')
        result = json.loads(line)
        if result.get('error'): raise ValueError(result['error'])
        return result


def words(text, begin=0):
    """Docker words with original quotes/escapes, not shell execution/expansion."""
    cursor = begin
    while cursor < len(text):
        if text[cursor].isspace(): cursor += 1; continue
        start, quote = cursor, None
        while cursor < len(text):
            char = text[cursor]
            if char == '\\' and cursor + 1 < len(text): cursor += 2; continue
            if quote:
                if char == quote: quote = None
            elif char in '\"\'': quote = char
            elif char.isspace(): break
            cursor += 1
        if quote: raise ValueError('Unclosed Dockerfile word quote')
        yield start, cursor, text[start:cursor]


def label(*, source, document_kind='dockerfile', profile=None):
    if not isinstance(source, str) or document_kind != 'dockerfile' or (profile or document_kind) != 'dockerfile':
        raise ValueError('Expected matching Dockerfile source kind/profile')
    source.encode('utf-8')
    if '\r' in source.replace('\r\n', '') or any(ord(c) < 32 and c not in '\t\n\r' for c in source):
        raise ValueError('Unsupported Dockerfile control or bare CR')
    ast = parse(source)
    spans, features, units = [], set(), [0]
    for char in source: units.append(units[-1] + (2 if ord(char) > 0xffff else 1))
    offsets, lines, cursor = [], [], 0
    pieces = source.split('\n')
    for index, piece in enumerate(pieces):
        raw = piece + ('\n' if index < len(pieces) - 1 else '')
        offsets.append(cursor); lines.append(raw); cursor += len(raw)
    occupied = [False] * len(source)
    body_lines, comment_lines, directive_lines = set(), set(), set()

    def add(a, b, role, modifiers=()):
        if a >= b: return
        if any(occupied[a:b]): raise ValueError('Overlapping Dockerfile supervision')
        occupied[a:b] = [True] * (b - a)
        span = dict(start=units[a], end=units[b], tokenType=role)
        if modifiers: span['modifiers'] = list(modifiers)
        spans.append(span)

    if source.startswith('\ufeff'): add(0, 1, 'punctuation'); features.add('bom')
    for directive in ast.get('directives') or []:
        row = directive['Location'][0]['Start']['Line'] - 1
        text = lines[row].rstrip('\r\n'); base = offsets[row]
        if row == 0 and text.startswith('\ufeff'): text = text[1:]; base += 1
        match = re.fullmatch(r'(\s*)(#)(\s*)([A-Za-z]+)(\s*)(=)(\s*)(.*?)(\s*)', text)
        if not match: raise ValueError('Unmapped official Dockerfile directive')
        for group, role in [(2,'punctuation'),(4,'keyword'),(6,'operator'),(8,'string')]:
            add(base + match.start(group), base + match.end(group), role)
        directive_lines.add(row); features.add('directives')

    shell_kind = 'bash'
    escape = ast['escape']
    for node in ast['instructions']:
        # Reconstruct only the parser's logical header, retaining a checked
        # character -> original map. Body lines and removed escapes never move.
        mapping, logical = [], ''
        row = node['startLine'] - 1
        while row < node['endLine']:
            text = lines[row].rstrip('\r\n'); base = offsets[row]
            if row == 0 and text.startswith('\ufeff'): text = text[1:]; base += 1
            if row == node['startLine'] - 1:
                n = len(text) - len(text.lstrip(' \t')); text = text[n:]; base += n
            if text.lstrip(' \t').startswith('#'):
                a = len(text) - len(text.lstrip(' \t')); add(base+a,base+len(text),'comment')
                comment_lines.add(row); row += 1; continue
            if not text.strip():
                row += 1; continue
            end = len(text.rstrip(' \t'))
            continuation = end > 0 and text[end-1] == escape and (end < 2 or text[end-2] != escape)
            if continuation:
                add(base+end-1,base+end,'punctuation'); features.add('continuations'); end -= 1
            else: end = len(text)
            logical += text[:end]; mapping.extend(range(base, base+end)); row += 1
            if not continuation: break
        if logical.strip() != node['original'].strip():
            raise ValueError('Original Dockerfile header differs from official AST')

        def emit(a, b, role, modifiers=()):
            if a >= b: return
            begin, previous = mapping[a], mapping[a]
            for original in mapping[a+1:b]:
                if original != previous + 1:
                    add(begin, previous+1, role, modifiers); begin = original
                previous = original
            add(begin, previous+1, role, modifiers)

        def foreign(text, start, kind):
            if not text.strip(): return
            if kind == 'json':
                from packs.json.labeling.label import label as foreign_label
                result = foreign_label(source=text, document_kind='json')
            elif kind in {'bash','posix','zsh','csh'}:
                from packs.bash.labeling.label import label as foreign_label
                result = foreign_label(source=text, document_kind='bash', profile=kind)
            else:
                emit(start,start+len(text),'string'); return
            coordinates, unit = {0:0}, 0
            for i, char in enumerate(text): unit += 2 if ord(char)>0xffff else 1; coordinates[unit]=i+1
            for span in result['spans']:
                modifiers = [m for m in span.get('modifiers',[]) if m in {'declaration','default-library'}]
                emit(start+coordinates[span['start']],start+coordinates[span['end']],span['tokenType'],modifiers)

        def literal(a, b, role='string'):
            text = logical[a:b]
            if len(text) > 1 and text[0] in '\"\'' and text[-1] == text[0]: emit(a,b,'string'); return
            cursor = a
            for match in VARIABLE.finditer(logical,a,b):
                if match.start()>cursor: emit(cursor,match.start(),role)
                emit(match.start(),match.end(),'variable'); cursor=match.end(); features.add('variables')
            if cursor<b: emit(cursor,b,'number' if role=='string' and NUMBER.fullmatch(logical[cursor:b]) else role)

        tokens = list(words(logical))
        if not tokens or tokens[0][2].lower() != node['keyword'].lower(): raise ValueError('Dockerfile instruction range mismatch')
        a, end, keyword = tokens.pop(0); emit(a,end,'keyword'); keyword=keyword.lower(); features.add('instructions')
        if keyword=='from': shell_kind='bash'
        if keyword=='onbuild':
            if not tokens: raise ValueError('Missing ONBUILD instruction')
            a,end,nested=tokens.pop(0); keyword=nested.lower()
            if keyword not in COMMANDS: raise ValueError('Unsupported ONBUILD instruction')
            emit(a,end,'keyword'); features.add('onbuild')
        for flag in node.get('flags') or []:
            if not tokens or tokens[0][2]!=flag: raise ValueError('Dockerfile flag differs from official AST')
            a,end,_=tokens.pop(0);emit(a,end,'parameter');features.add('flags')
        if keyword=='healthcheck':
            if not tokens: raise ValueError('Missing HEALTHCHECK command')
            a,end,cmd=tokens.pop(0)
            if cmd.lower() not in {'cmd','none'}: raise ValueError('Unsupported HEALTHCHECK form')
            emit(a,end,'keyword'); keyword='run' if cmd.lower()=='cmd' else 'healthcheck'
        start = tokens[0][0] if tokens else len(logical)
        args = logical[start:]
        heredocs = node.get('heredocs') or []
        markers=[]
        if heredocs:
            for a,b,text in tokens:
                match=re.fullmatch(r'(\d*<<-?)(.+)',text)
                if match:
                    emit(a,a+len(match[1]),'operator');emit(a+len(match[1]),b,'label',['declaration']);markers.append((a,b))
            if len(markers)!=len(heredocs): raise ValueError('Heredoc marker/AST count mismatch')
            features.add('heredocs')

        if keyword in {'run','cmd','entrypoint'} and not args.startswith('['):
            features.add('shell-form')
            masked=list(args)
            for a,b in markers: masked[a-start:b-start]=[' ']*(b-a)
            foreign(''.join(masked),start,shell_kind)
        elif args.startswith('['):
            foreign(args,start,'json');features.add('json-form')
            if keyword=='shell':
                shell=json.loads(args)
                if not shell or not shell[0]:raise ValueError('SHELL requires a nonempty command')
                command=shell[0].replace('\\','/').rsplit('/',1)[-1].lower()
                shell_kind={'sh':'posix','bash':'bash','ash':'posix','zsh':'zsh','csh':'csh','tcsh':'csh'}.get(command,'opaque')
        elif keyword in {'arg','env','label'}:
            role='property' if keyword=='label' else 'variable'
            if tokens and '=' not in tokens[0][2] and keyword in {'env','label'} and len(tokens)>1:
                a,b,_=tokens[0];emit(a,b,role,['declaration']);literal(tokens[1][0],len(logical))
            else:
                for a,b,text in tokens:
                    equal=text.find('=')
                    if equal>=0:
                        emit(a,a+equal,role,['declaration']);emit(a+equal,a+equal+1,'operator');literal(a+equal+1,b)
                    else:emit(a,b,role,['declaration'])
            features.add('variables')
        elif keyword=='from':
            for i,(a,b,text) in enumerate(tokens):
                if i==1 and text.lower()=='as':emit(a,b,'keyword');features.add('stages')
                elif i and tokens[i-1][2].lower()=='as':emit(a,b,'label',['declaration'])
                else:literal(a,b,'namespace')
        else:
            for a,b,text in tokens:
                if (a,b)not in markers:literal(a,b)

        # BuildKit supplies exact heredoc identity/order. Locate delimiters in
        # original physical lines and retain CRLF, tabs and blank body lines.
        for hdoc in heredocs:
            first=row; body_start=offsets[row]; stop=None
            while row < node['endLine']:
                text=lines[row].rstrip('\r\n')
                if (text.lstrip('\t') if hdoc['Chomp'] else text)==hdoc['Name']: stop=row;break
                row+=1
            if stop is None:raise ValueError('Original heredoc terminator differs from official AST')
            body=source[body_start:offsets[stop]]
            # Official content normalizes CRLF only; never alter original spans.
            if body.replace('\r\n','\n')!=hdoc['Content'].replace('\r\n','\n'):
                raise ValueError('Original heredoc body differs from official AST')
            body_lines.update(range(first,stop+1))
            remaining=[text for a,b,text in tokens if (a,b)not in markers]
            script=keyword=='run' and (not remaining or remaining[0]in {'sh','bash','ash','/bin/sh','/bin/bash'})
            if script and not body.lstrip().startswith('#!') and shell_kind!='opaque':
                from packs.bash.labeling.label import label as shell_label
                result=shell_label(source=body,document_kind='bash',profile=shell_kind)
                lookup={0:0};u=0
                for i,char in enumerate(body):u+=2 if ord(char)>0xffff else 1;lookup[u]=i+1
                for span in result['spans']:
                    add(body_start+lookup[span['start']],body_start+lookup[span['end']],span['tokenType'],span.get('modifiers',[]))
            else:add(body_start,offsets[stop],'string')
            text=lines[stop].rstrip('\r\n');leading=len(text)-len(text.lstrip('\t')) if hdoc['Chomp'] else 0
            add(offsets[stop]+leading,offsets[stop]+len(text),'label');row=stop+1
        if row != node['endLine']:raise ValueError('Original instruction line coverage differs from AST')

    for row,raw in enumerate(lines):
        if row in body_lines or row in comment_lines or row in directive_lines:continue
        text=raw.rstrip('\r\n');a=offsets[row]
        if row==0 and text.startswith('\ufeff'):text=text[1:];a+=1
        leading=len(text)-len(text.lstrip(' \t'))
        if text[leading:].startswith('#'):add(a+leading,a+len(text),'comment');features.add('comments')
    for i,char in enumerate(source):
        if not char.isspace() and not occupied[i]:raise ValueError('Uncovered original Dockerfile source at '+str(i))
    if '\r\n' in source:features.add('crlf')
    if any(ord(c)>127 for c in source):features.add('unicode')
    spans.sort(key=lambda s:(s['start'],s['end']))
    canonical=[]
    for span in spans:
        if (canonical and span['tokenType']=='string' and canonical[-1]['tokenType']=='string'
                and canonical[-1]['end']==span['start'] and canonical[-1].get('modifiers',[])==span.get('modifiers',[])):
            canonical[-1]['end']=span['end']
        else:canonical.append(span)
    return dict(offsetEncoding='utf-16',spans=canonical,features=sorted(features))
