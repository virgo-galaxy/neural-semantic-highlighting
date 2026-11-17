"""Generate selected browser descriptors without dropping optional decoder state."""
from pathlib import Path
import argparse
import json

IDS=['typescript','go','css','html','vue','python','bash','perl','awk','sql','powershell','bat','assembly','java','csharp','c','cpp','php','svelte','rust','zig','dart','swift','kotlin','r','scala','ruby','lua','json','yaml','toml','ini','dotenv','xml','markdown','dockerfile']


def generate(pack_id):
    metadata=json.loads((Path('packs')/pack_id/'browser/model.json').read_text())
    record={'id':pack_id,'manifest':metadata['manifest'],'sha256':metadata['model']['sha256'],
            'contextBytes':metadata['contextBytes'],'schema':metadata['schema'],
            'modifierThreshold':metadata['modifierThreshold'],'decoder':metadata['decoder']}
    if metadata.get('structuredDecoder') is not None:record['structuredDecoder']=metadata['structuredDecoder']
    text='import type { BrowserModel } from "@nsh/browser";\n'
    if pack_id=='php':text+='import html from "./html.js";\n'
    if pack_id in {'html','vue','svelte'}:text+='import typescript from "./typescript.js";\nimport css from "./css.js";\n'
    text+='\nconst model: BrowserModel = {\n'+json.dumps(record,indent=2)[2:-2]+',\n  modelUrl: () => new URL("../models/'+pack_id+'.onnx", import.meta.url).href,\n'
    if pack_id=='php':text+='  dependencies: [html],\n'
    if pack_id in {'html','vue','svelte'}:text+='  dependencies: [typescript, css],\n'
    text+='};\nexport default model;\n'
    (Path('packages/highlighter/src/languages')/(pack_id+'.ts')).write_text(text)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack',choices=IDS,help='Regenerate only this descriptor; preserve all other files')
    args=parser.parse_args()
    for pack_id in ([args.pack]if args.pack else IDS):generate(pack_id)
    if args.pack:return
    imports=''.join(f'import {pack_id} from "./languages/{pack_id}.js";\n'for pack_id in IDS)
    Path('packages/highlighter/src/index.ts').write_text(imports+'import { createHighlighter as createConfiguredHighlighter, type HighlighterOptions } from "./highlighter.js";\n\nexport type { BrowserHighlighter, HighlightedCode, HighlighterOptions } from "./highlighter.js";\nexport function createHighlighter(options: HighlighterOptions = {}) {\n  return createConfiguredHighlighter({ ...options, languages: options.languages ?? ['+', '.join(IDS)+'] });\n}\n')
    for alias,parent,description in [('flutter','dart','Flutter source shares the selected Dart model and its single model asset.'),('jsonc','json','JSONC shares the selected JSON-family model and its single asset.'),('svg','xml','SVG shares the selected XML model and its single asset.')]:
        Path('packages/highlighter/src/languages/'+alias+'.ts').write_text('/** '+description+' */\nexport { default } from "./'+parent+'.js";\n')


if __name__=='__main__':main()
