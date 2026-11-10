"""Original component tasks. Variants stay in one directory family."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'counter':'<script>let count = @N@; function increment() { count += 1; }</script>\n<button on:click={increment}>Count: {count}</button>\n<style>button { color: navy; padding: 8px; }</style>',
'runes-counter':'<script lang="ts">let count = $state(@N@); const doubled = $derived(count * 2);</script>\n<button onclick={() => count++}>{count} / {doubled}</button>',
'legacy-props':'<script>export let name = "@WORD@"; export let active = true;</script>\n<section class:active><h2>Hello {name}</h2><slot /></section>',
'runes-props':'<script lang="ts">let { title = "@WORD@", children } = $props();</script>\n<article><h2>{title}</h2>{@render children?.()}</article>',
'if-else':'<script>export let visible = true;</script>\n{#if visible}<aside role="note">@WORD@</aside>{:else}<p>Hidden</p>{/if}',
'if-elseif':'<script>let status = @N@;</script>\n{#if status > 2}<b>Ready</b>{:else if status > 0}<i>Loading</i>{:else}<em>Empty</em>{/if}',
'keyed-list':'<script lang="ts">export let rows: { id: number; name: string }[] = [];</script>\n<ul>{#each rows as row, i (row.id)}<li data-index={i}>{row.name}</li>{:else}<li>No rows</li>{/each}</ul>',
'each-destructure':'<script>let entries = [{ id: @N@, label: "@WORD@" }];</script>\n{#each entries as {id, label}}<label for={id}>{label}</label>{/each}',
'await-all':'<script>export let promise;</script>\n{#await promise}<progress />{:then result}<output>{result}</output>{:catch error}<p class="error">{error.message}</p>{/await}',
'await-short':'<script>const task = Promise.resolve("@WORD@");</script>\n{#await task then message}<p>{message}</p>{/await}',
'key-block':'<script>export let revision = @N@;</script>\n{#key revision}<section transition:fade><p>{revision}</p></section>{/key}',
'snippet-basic':'<script>let title = "@WORD@";</script>\n{#snippet greeting(name)}<strong>Hello {name}</strong>{/snippet}\n{@render greeting(title)}',
'snippet-list':'<script lang="ts">let values = [@N@, 2, 3];</script>\n{#snippet cell(value, index)}<td>{index}: {value}</td>{/snippet}\n<table><tbody>{#each values as value, i}<tr>{@render cell(value, i)}</tr>{/each}</tbody></table>',
'snippet-optional':'<script>let { header, footer } = $props();</script>\n<header>{@render header?.()}</header><main>@WORD@</main><footer>{@render footer?.()}</footer>',
'const-tag':'<script>let items = [{ value: @N@ }];</script>\n{#each items as item}{@const doubled = item.value * 2}<output>{doubled}</output>{/each}',
'raw-html':'<script>export let markup = "<b>@WORD@</b>";</script>\n<div class="content">{@html markup}</div>',
'debug-tag':'<script>let value = @N@;</script>\n{@debug value}<pre>{value}</pre>',
'bindings':'<script>let name = "@WORD@"; let agreed = false;</script>\n<form><input bind:value={name} /><input type="checkbox" bind:checked={agreed} /><p>{name}</p></form>',
'events-modifiers':'<script>function submit(event) { event.preventDefault(); }</script>\n<form on:submit|preventDefault={submit}><button type="submit">@WORD@</button></form>',
'spread-attrs':'<script>let props = { title: "@WORD@" }; let disabled = false;</script>\n<button {...props} {disabled} aria-label="Action">Run</button>',
'class-style':'<script>let active = true; let color = "red";</script>\n<div class:active style:color={color} style:width="@N@px">{color}</div>',
'action-transition':'<script>import { fade } from "svelte/transition"; function focus(node) { node.focus(); }</script>\n<input use:focus transition:fade placeholder="@WORD@" />',
'animate':'<script>import { flip } from "svelte/animate"; let items = [@N@, 2];</script>\n{#each items as item (item)}<div animate:flip>{item}</div>{/each}',
'head-window':'<script>let width = @N@; let title = "@WORD@";</script>\n<svelte:head><title>{title}</title><meta name="description" content="Example" /></svelte:head>\n<svelte:window bind:innerWidth={width} /><output>{width}</output>',
'dynamic-component':'<script>export let component; let name = "@WORD@";</script>\n<svelte:component this={component} {name} /><svelte:element this="aside">{name}</svelte:element>',
'slots':'<script>export let item = { label: "@WORD@" };</script>\n<slot name="header" {item}><h1>Default</h1></slot><slot />',
'component-events':'<script>import Item from "./Item.svelte"; let value = @N@;</script>\n<Item bind:value on:change={(e) => value = e.detail}><span slot="label">@WORD@</span></Item>',
'module-legacy':'<script context="module">export const version = @N@;</script>\n<script>let label = "@WORD@";</script>\n<p data-version={version}>{label}</p>',
'module-modern':'<script module lang="ts">export type Entry = { name: string };</script>\n<script lang="ts">let item: Entry = { name: "@WORD@" };</script>\n<article>{item.name}</article>',
'effect':'<script lang="ts">let size = $state(@N@); $effect(() => { console.log(size); });</script>\n<input type="range" bind:value={size} /><span>{size}</span>',
'store':'<script>import { writable } from "svelte/store"; const count = writable(@N@);</script>\n<button on:click={() => $count++}>{$count}</button>',
'reactive':'<script>let first = @N@; $: total = first * 2;</script>\n<input type="number" bind:value={first} /><output>{total}</output>',
'css':'<script>export let tone = "@WORD@";</script>\n<div class="card" data-tone={tone}>{tone}</div>\n<style>.card { display: grid; gap: @N@px; } @media (width > 600px) { .card { padding: 1rem; } }</style>',
'scss':'<script lang="ts">let heading: string = "@WORD@";</script>\n<h1 class="title">{heading}</h1>\n<style lang="scss">$tone: #a855f7; .title { color: $tone; &:hover { opacity: .8; } }</style>',
'less':'<script>let label = "@WORD@";</script>\n<aside class="panel">{label}</aside>\n<style lang="less">@gap: @N@px; .panel { padding: @gap; & > span { color: blue; } }</style>',
'style-first':'<style>.badge { border-radius: @N@px; background: #eee; }</style>\n<script>let text = "@WORD@";</script>\n<span class="badge">{text}</span>',
'entities':'<!-- @WORD@ component -->\n<p>Fish &amp; chips &#169; 星 🌌</p><a href="/docs?x=1&amp;y=2">Read &rarr;</a>',
'nested-template':'<script>let groups = [{ name: "@WORD@", items: [@N@] }];</script>\n{#each groups as group}<section><h2>{group.name}</h2>{#each group.items as item}{#if item}<b>{item}</b>{/if}{/each}</section>{/each}',
'custom-element':'<script>let value = "@WORD@";</script>\n<my-widget data-value={value}><span>{value}</span></my-widget>',
'multiline-expression':'<script lang="ts">let items: number[] = [@N@];</script>\n<p>{items\n .filter((item) => item > 0)\n .map((item) => item * 2).join(", ")}</p>',
'foreign-svg':'<script>let label = "@WORD@";</script>\n<svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="@N@" /><text x="1" y="15">{label}</text></svg>',
'options':'<svelte:options immutable={true} /><script>export let name = "@WORD@";</script><p>{name}</p>',
}

def main():
    root=PackSpec.open('svelte').dataset_root/'sources/curriculum-v1';files={}
    for family,template in TEMPLATES.items():
        for i in range(16):
            source=template.replace('@N@',str(i+3)).replace('@WORD@',['Aurora','Orbit','Nova','Cosmos'][i%4])+'\n'
            if i%5==0:source=source.replace('\n','\r\n')
            if i%7==0:source='<!-- 星 🌌 -->'+source
            raw=source.encode();path=root/family/f'variant-{i:02}.svelte';path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve prior curriculum')
            if not path.exists():path.write_bytes(raw)
            files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
    raw=b'Original Svelte component tasks authored for Neural Semantic Highlighting.\nPrivate development dataset. No Golden, Playground or upstream copies.\n';path=root/'LICENSE'
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve original license')
    path.write_bytes(raw)
    lock=dict(format='nsh-svelte-curriculum-v1',generatorHash=file_hash(Path(__file__)),files=files,licenseSha256=hashlib.sha256(raw).hexdigest())
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve prior curriculum lock')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original Svelte curriculum files')
if __name__=='__main__':main()
