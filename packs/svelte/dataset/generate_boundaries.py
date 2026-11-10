"""Original mixed-body and directive tasks motivated by validation-only review."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

MARKUP={
'fieldset':'<fieldset><legend>{heading}</legend><input bind:value={entry} /><button onclick={reset}>Reset {entry}</button></fieldset>',
'list-actions':'<div><h3>{heading}</h3><ol><li><button on:click={reset}>{entry}</button></li></ol></div>',
'details':'<details open={active}><summary>{heading}</summary><p>{entry}</p><input bind:value={entry} /></details>',
'figure':'<figure class:active={active}><figcaption>{heading}: {entry}</figcaption><button on:click|once={reset}>Reset</button></figure>',
'nav-list':'<nav aria-label={heading}><ul><li><a href="/home">{entry}</a></li></ul><button onclick={reset}>Clear</button></nav>',
'definition':'<dl><dt>{heading}</dt><dd><input bind:value={entry} /><em>{entry}</em></dd></dl>',
'header-main':'<header><span>{heading}</span></header><main><section class:active><output>{entry}</output></section></main>',
'footer-form':'<footer><form on:submit|preventDefault={reset}><label>{heading}<input bind:value={entry} /></label><button>{entry}</button></form></footer>',
'key-controls':'{#key heading}<section><h4>{heading}</h4><input bind:value={entry} /><meter value="2" max="10" /></section>{/key}',
'conditional':'<aside>{#if active}<h3>{heading}</h3><textarea bind:value={entry} />{:else}<code>{entry}</code>{/if}</aside>',
'choices':'<form><select bind:value={entry}><option value="one">{heading}</option></select><output>{entry}</output></form>',
'fieldset-check':'<fieldset disabled={!active}><label><input type="checkbox" bind:checked={active} />{heading}</label><b>{entry}</b></fieldset>',
'button-group':'<div role="group"><button onclick={reset}>{heading}</button><button class:active>{entry}</button><small>{active}</small></div>',
'paragraphs':'<article><p><strong>{heading}</strong> — {entry}</p><p>{active ? heading : entry}</p></article>',
'slot-wrapper':'<section><slot name="title">{heading}</slot><div><slot {entry}>{entry}</slot></div><button on:click={reset} /></section>',
'snippet-card':'{#snippet detail(value)}<dl><dt>{heading}</dt><dd>{value}</dd></dl>{/snippet}<aside>{@render detail(entry)}</aside>',
'await-section':'<section>{#await Promise.resolve(entry) then value}<h5>{heading}</h5><p>{value}</p>{/await}</section>',
'each-section':'<section><h5>{heading}</h5>{#each [entry] as value, index}<p>{index}: {value}</p>{/each}</section>',
'component-wrap':'<Widget title={heading} bind:value={entry}><button on:click={reset}>{entry}</button><span>{heading}</span></Widget>',
'window-form':'<svelte:window on:focus={reset} /><form><label>{heading}</label><input bind:value={entry} /><p>{entry}</p></form>',
}

def main():
 root=PackSpec.open('svelte').dataset_root/'sources/boundaries-v1';files={}
 for family,markup in MARKUP.items():
  for i in range(24):
   typed=i%2==0;lang=['css','scss','less'][i%3]
   script=('let heading'+(': string' if typed else '')+' = "Nebula";\nlet entry = "item"; let active = true;\nfunction reset() { entry = ""; active = false; }\n')
   if i%4==0:script+='// Template-like text remains script: <article> {#if ready}\nconst sample = "<span>{value}</span>";\n'
   style={'css':'.group { color: #356; padding: 6px; }\n.group:hover { opacity: .7; }','scss':'$accent: #39a;\n.group { color: $accent; &:hover { opacity: .7; } }','less':'@gap: 6px;\n.group { padding: @gap; & > span { color: #39a; } }'}[lang]
   if i>=12:script+='\n'.join('const item'+str(n)+' = { name: "星 🌌", value: '+str(n)+' };' for n in range(18))+'\n'
   source='<script'+(' lang="ts"' if typed else '')+'>\n'+script+'</script>\n'+markup+'\n<style'+(' lang="'+lang+'"' if lang!='css' else '')+'>\n'+style+'\n</style>\n'
   if i%5==0:source=source.replace('\n','\r\n')
   raw=source.encode();path=root/family/f'{i:02}.svelte';path.parent.mkdir(parents=True,exist_ok=True)
   if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve prior boundaries corpus')
   if not path.exists():path.write_bytes(raw)
   files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=root/'LICENSE'
 if not license.exists():license.write_text('Original mixed Svelte tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream/Golden/Playground copies.\n')
 lock=dict(format='nsh-svelte-boundaries-v1',generatorSha256=file_hash(Path(__file__)),files=files);path=root/'source.lock.json'
 if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve prior boundaries lock')
 path.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'mixed Svelte tasks')
if __name__=='__main__':main()
