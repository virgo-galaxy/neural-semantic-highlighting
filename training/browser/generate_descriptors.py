from pathlib import Path
import json
ids=['typescript','go','css','html','vue','python','bash','perl','awk','sql','powershell','bat','assembly','java','csharp','c','cpp','php','svelte','rust','zig','dart','swift','kotlin','r','scala','ruby','lua']
for id in ids:
 m=json.loads((Path('packs')/id/'browser/model.json').read_text())
 record={'id':id,'manifest':m['manifest'],'sha256':m['model']['sha256'],'contextBytes':m['contextBytes'],'schema':m['schema'],'modifierThreshold':m['modifierThreshold'],'decoder':m['decoder']}
 text='import type { BrowserModel } from "@nsh/browser";\n'
 if id == 'php':text+='import html from "./html.js";\n'
 if id in {'html','vue','svelte'}:text+='import typescript from "./typescript.js";\nimport css from "./css.js";\n'
 text+='\nconst model: BrowserModel = {\n'+json.dumps(record,indent=2)[2:-2]+',\n  modelUrl: () => new URL("../models/'+id+'.onnx", import.meta.url).href,\n'
 if id == 'php':text+='  dependencies: [html],\n'
 if id in {'html','vue','svelte'}:text+='  dependencies: [typescript, css],\n'
 text+='};\nexport default model;\n';(Path('packages/highlighter/src/languages')/(id+'.ts')).write_text(text)
imports=''.join(f'import {id} from "./languages/{id}.js";\n' for id in ids)
Path('packages/highlighter/src/index.ts').write_text(imports+'import { createHighlighter as createConfiguredHighlighter, type HighlighterOptions } from "./highlighter.js";\n\nexport type { BrowserHighlighter, HighlightedCode, HighlighterOptions } from "./highlighter.js";\nexport function createHighlighter(options: HighlighterOptions = {}) {\n  return createConfiguredHighlighter({ ...options, languages: options.languages ?? ['+', '.join(ids)+'] });\n}\n')
Path('packages/highlighter/src/languages/flutter.ts').write_text('/** Flutter source shares the selected Dart model and its single model asset. */\nexport { default } from "./dart.js";\n')
