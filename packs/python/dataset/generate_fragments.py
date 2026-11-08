"""Original short-fragment revision; v1 corpus and frozen holdouts stay intact."""
from pathlib import Path
import hashlib
import json
from training.shared.spec import PackSpec, file_hash

TEMPLATES={
 'module-imports':'import {module} as {alias}\nfrom {module} import {cls}\n{alias}.fetch()\n',
 'module-imports-call':'from {module}.tools import build as {fn}\nimport os, sys\nresult = {fn}({n})\n',
 'module-imports-attributes':'import {module}\n{alias} = {module}.client\n{alias}.close()\n',
 'decorator-bare':'@{deco}\ndef {fn}({arg}):\n    return {arg}\n',
 'decorator-call':'@{deco}(limit={n})\ndef {fn}():\n    return False\n',
 'decorator-namespaced':'@{module}.{deco}(enabled=True)\nclass {cls}:\n    pass\n',
 'async-short':'async def {fn}():\n    return await {other}()\n',
 'async-yield-short':'async def {fn}():\n    yield await {other}()\n',
 'async-parameter':'async def {fn}({arg}):\n    await {arg}.send({n})\n',
 'ordinary-return':'def {fn}({arg}: float) -> float:\n    return {arg} ** {n}\n',
 'ordinary-power':'{var} = {n} ** 3\n{var} //= 2\n{fn}({var})\n',
 'ordinary-generator':'def {fn}({arg}):\n    yield {arg}\n    return\n',
 'shadow-builtins':'def {fn}(len, {arg}):\n    return len({arg})\n',
 'shadow-print':'def {fn}(print):\n    print({n})\n    return print\n',
 'shadow-types':'def {fn}(list, {arg}):\n    return list({arg})\n',
 'lambda-shadow':'{var} = lambda len, {arg}: len({arg})\n',
 'match-wildcard':'match {var}:\n    case _:\n        pass\n',
 'match-literals':'match {var}:\n    case {n}: return_value = True\n    case _:\n        return_value = False\n',
 'match-capture':'match {var}:\n    case [item, *others]:\n        {fn}(item, others)\n    case _:\n        pass\n',
 'soft-name':'match = {n}\ncase = match + 1\ntype = case\n',
 'adjacent-fstring':'{var} = f"Value: {{{arg}!r}}" " tail"\n{fn}({var})\n',
 'adjacent-tstring':'{var} = t"Hello {{{arg}}}"\n{other} = f"{{{arg}}}" "!"\n',
 'literal-expressions':'{var} = f"{{{arg}.name}}: {{{n}:04d}}"\n{fn}({var}, end="")\n',
 'comment-unicode':'# 星空 🚀\n{var} = "星 🌌"; {fn}({var})\n',
 'module-unicode':'# 你好 🌌\n文字 = "🚀"; print(文字)\n{var} = {n}\n',
 'unicode-pair':'名字 = "星系"\n星 = f"你好 {{名字}} 🪐"\nprint(星)\n',
 'semicolon-short':'{var} = "🪐"; {other} = {n}; print({var}, {other})\n',
 'annotations-short':'def {fn}({arg}: str) -> str:\n    return {arg}.strip()\n',
 'parameters-default':'def {fn}({arg}={n}, *, enabled=True):\n    return {arg} if enabled else None\n',
 'generics-short':'type {cls}[T] = tuple[T, T]\n',
 'generic-bounds':'def {fn}[T: int]({arg}: T) -> T:\n    return {arg} + {n}\n',
 'type-class':'class {cls}[T]:\n    value: T\n    def get(self) -> T:\n        return self.value\n',
 'triple-string':'{var} = """Heading\nOriginal documentation for {fn}.\nEnding."""\nprint({var})\n',
 'string-escape':'{var} = r"\\d+\\s*"\n{other} = b"a\\x00b"\n',
 'exception-short':'try:\n    {fn}()\nexcept ValueError as {var}:\n    print({var})\n',
 'keyword-args':'{var} = {fn}(size={n}, name="entry")\n{var}.save(force=True)\n',
}

def main():
    root=PackSpec.open('python').dataset_root/'sources/fragments-v1'
    files={}
    for family,template in TEMPLATES.items():
        for i in range(16):
            values={'module':['network','storage','widgets','signals'][i%4],
                'alias':['net','store','lib','api'][i%4], 'cls':['Entry','Panel','Item','Record'][i%4],
                'fn':['apply','convert','publish','select','encode','read'][i%6],
                'other':['send','restore','receive','prepare','pack'][i%5],
                'deco':['cached','trace','validate','retry'][i%4],
                'arg':['data','item','value','input','record'][i%5],
                'var':['output','message','result','entry','state'][i%5],'n':i+3}
            source=template.format(**values)
            # Vary leading positions and line endings instead of memorizing
            # one file-length/layout per grammar family.
            if i%4==1:source='# Original fragment\n'+source
            elif i%4==2:source='\n\n'+source
            elif i%4==3:source='"""Small code example."""\n\n'+source
            if i%3==1:source=source.replace('\n','\r\n')
            files[f'{family}/{i:02}.py']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting curriculum. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Existing fragment revision differs')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-python-original-fragments-v1','generatorHash':file_hash(Path(__file__)),
          'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing fragment lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'original fragments')

if __name__=='__main__':main()
