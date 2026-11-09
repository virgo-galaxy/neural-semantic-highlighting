"""Original C syntax tasks; all variants remain in one source family."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'function':'''#include <stddef.h>
static int {fn}(int {arg}, int limit) {{
  int total = {arg} + {n};
  return total > limit ? total : limit;
}}
int {other}(void) {{ return {fn}({n2}, {n}); }}
''',
'prototype':'''int {fn}(const char *name, unsigned count);
static void {other}(int *value);
int {item}(void) {{ int value={n}; {other}(&value); return {fn}("{word}", value); }}
''',
'struct':'''typedef struct {tag} {{ int count; const char *name; }} {item};
static int {fn}({item} *{arg}) {{ return {arg}->count + {n}; }}
int {other}(void) {{ {item} entry={{ .count={n}, .name="{word}" }}; return {fn}(&entry); }}
''',
'union':'''typedef union {tag} {{ unsigned bits; float value; }} {item};
float {fn}(unsigned {arg}) {{ {item} slot={{ .bits={arg} }}; return slot.value; }}
''',
'enum':'''enum {tag} {{ {upper}_NEW, {upper}_READY={n}, {upper}_DONE }};
static int {fn}(enum {tag} {arg}) {{
 switch ({arg}) {{ case {upper}_NEW: return 0; case {upper}_READY: return {n2}; default: return -1; }}
}}
''',
'callback':'''typedef int (*{item})(int value, void *context);
int {fn}({item} callback, void *{arg}) {{
  int result=callback({n}, {arg});
  return result;
}}
''',
'callback-field':'''struct {tag} {{ void (*emit)(const char *text); unsigned count; }};
void {fn}(struct {tag} *{arg}) {{ {arg}->emit("{word}"); {arg}->count++; }}
''',
'callback-table':'''typedef int (*{item})(int code);
static int {fn}(int value) {{ return value+{n}; }}
int {other}(int {arg}) {{ {item} handlers[]={{ {fn}, {fn} }}; return handlers[0]({arg}); }}
''',
'pointer':'''#include <stddef.h>
int {fn}(const int *{arg}, size_t count) {{
 int sum=0;
 for (size_t i=0; i<count; ++i) {{ sum += *({arg}+i); }}
 return sum+{n};
}}
''',
'array':'''static const unsigned {arg}[]={{ {n}, {n2}, 0x2aU }};
int {fn}(unsigned index) {{ return index < sizeof({arg})/sizeof({arg}[0]) ? {arg}[index] : -1; }}
''',
'multidimensional':'''int {fn}(int {arg}[3][3]) {{
 int total={n};
 for(int row=0;row<3;++row) for(int col=0;col<3;++col) total+={arg}[row][col];
 return total;
}}
''',
'linked-list':'''typedef struct {tag} {{ int value; struct {tag} *next; }} {item};
int {fn}(const {item} *{arg}) {{ int count=0; while ({arg}) {{ count += {arg}->value; {arg}={arg}->next; }} return count; }}
''',
'allocation':'''#include <stdlib.h>
typedef struct {tag} {{ int value; }} {item};
{item} *{fn}(int {arg}) {{ {item} *entry=malloc(sizeof *entry); if(entry) entry->value={arg}; return entry; }}
void {other}({item} *entry) {{ free(entry); }}
''',
'strings':'''#include <stdio.h>
#include <string.h>
int {fn}(const char *{arg}) {{
 char buffer[128];
 snprintf(buffer,sizeof buffer,"{word}=%s\\n",{arg});
 return (int)strlen(buffer);
}}
''',
'adjacent-strings':'''#include <stdio.h>
static const char *{arg}="{word}: " "ready\\n";
int {fn}(void) {{ return printf("%s",{arg}); }}
''',
'escape-strings':'''int {fn}(void) {{ const char *{arg}="path\\\\{word}\\t\\\"quoted\\\""; char end='\\n'; return {arg}[0]+end+{n}; }}
''',
'format-macro':'''#include <stdio.h>
#define {upper}_LOG(fmt, ...) printf(fmt, __VA_ARGS__)
int {fn}(int {arg}) {{ return {upper}_LOG("{word}=%d\\n", {arg}); }}
''',
'function-macro':'''#define {upper}_CLAMP(x, low, high) ((x)<(low)?(low):((x)>(high)?(high):(x)))
int {fn}(int {arg}) {{ return {upper}_CLAMP({arg}, {n}, {n2}); }}
''',
'object-macro':'''#define {upper}_LIMIT {n2}U
#define {upper}_NAME "{word}"
const char *{fn}(unsigned {arg}) {{ return {arg} < {upper}_LIMIT ? {upper}_NAME : ""; }}
''',
'continuation-macro':'''#define {upper}_APPLY(x) \\
  (((x) * {n}) + \\
   {n2})
int {fn}(int {arg}) {{ return {upper}_APPLY({arg}); }}
''',
'paste-macro':'''#define {upper}_JOIN(a, b) a ## b
#define {upper}_TEXT(x) #x
const char *{fn}(void) {{ return {upper}_TEXT({word}); }}
''',
'header-guards':'''#ifndef {upper}_API_H
#define {upper}_API_H
#include <stddef.h>
typedef struct {tag} {{ size_t length; char *data; }} {item};
int {fn}({item} *{arg});
#endif
''',
'conditional-directives':'''#define {upper}_VERSION {n}
#if defined({upper}_VERSION) && {upper}_VERSION > 1
static int {fn}(int {arg}) {{ return {arg}+{n}; }}
#else
static int {fn}(int {arg}) {{ return {arg}; }}
#endif
''',
'pragma':'''#pragma once
#include <stdint.h>
typedef struct {tag} {{ uint32_t flags; }} {item};
static inline unsigned {fn}(const {item} *{arg}) {{ return {arg}->flags & {n}U; }}
''',
'loops':'''int {fn}(unsigned {arg}) {{ int total=0; for(unsigned i=0;i<{arg};++i) {{ if(i%{n}==0) continue; total+=(int)i; }} return total; }}
''',
'do-while':'''int {fn}(int {arg}) {{ int count=0; do {{ ++count; {arg}/={n}; if(count>{n2}) break; }} while({arg}>0); return count; }}
''',
'goto':'''#include <stdlib.h>
int {fn}(unsigned {arg}) {{ void *data=malloc({arg}+{n}); if(!data) goto fail; free(data); return 0; fail: return -1; }}
''',
'bit-fields':'''struct {tag} {{ unsigned ready:1; unsigned code:7; }};
int {fn}(struct {tag} {arg}) {{ return {arg}.ready ? {arg}.code : {n}; }}
''',
'bitwise':'''unsigned {fn}(unsigned {arg}, unsigned shift) {{ unsigned mask=1U<<shift; return ({arg}|mask)^({n}U & ~mask); }}
''',
'compound-literal':'''typedef struct {tag} {{ double x; double y; }} {item};
{item} {fn}(double {arg}) {{ return ({item}){{ .x={arg}, .y={n}.0 }}; }}
''',
'flexible-array':'''#include <stddef.h>
struct {tag} {{ size_t count; unsigned char bytes[]; }};
size_t {fn}(const struct {tag} *{arg}) {{ return sizeof(*{arg})+{arg}->count; }}
''',
'qualifiers':'''static volatile unsigned {arg}={n};
static inline unsigned {fn}(const unsigned *restrict input) {{ {arg}+=*input; return {arg}; }}
''',
'atomic':'''#include <stdatomic.h>
static _Atomic int {arg}={n};
int {fn}(int delta) {{ return atomic_fetch_add(&{arg},delta); }}
''',
'static-assert':'''#include <stdint.h>
_Static_assert(sizeof(uint32_t)==4,"{word}");
uint32_t {fn}(uint32_t {arg}) {{ return {arg}+{n}U; }}
''',
'generic':'''#define {upper}_KIND(x) _Generic((x), int: "integer", double: "decimal", default: "other")
const char *{fn}(int {arg}) {{ return {upper}_KIND({arg}); }}
''',
'numbers':'''double {fn}(unsigned {arg}) {{ double scale=0x1.fp+2; unsigned mask=0xffUL; float ratio=1.25e-2f; return ({arg}&mask)*scale+ratio+{n}.0; }}
''',
'unicode':'''// 原始数据 🌙 {word}
const char *{fn}(int {arg}) {{ const char *title="星空 🌌 {word}"; return {arg}>{n} ? title : ""; }}
''',
'comments':'''/* {word}: a function(int) inside a comment */
int {fn}(int {arg}) {{
 // return, #define and pointers stay comments
 return {arg}+{n}; /* finish */
}}
''',
'designated-array':'''enum {tag} {{ {upper}_A, {upper}_B, {upper}_C }};
static const int {arg}[]={{ [{upper}_A]={n}, [{upper}_C]={n2} }};
int {fn}(enum {tag} state) {{ return {arg}[state]; }}
''',
'pointer-return':'''#include <stddef.h>
const char *{fn}(const char *{arg}, char value) {{ while(*{arg}) {{ if(*{arg}==value) return {arg}; ++{arg}; }} return NULL; }}
''',
'file-io':'''#include <stdio.h>
int {fn}(const char *{arg}) {{ FILE *stream=fopen({arg},"r"); if(!stream) return -1; int count=0; while(fgetc(stream)!=EOF) ++count; fclose(stream); return count+{n}; }}
''',
'sorting':'''#include <stdlib.h>
static int {fn}(const void *a,const void *b) {{ return *(const int *)a-*(const int *)b; }}
void {other}(int *{arg}, unsigned count) {{ qsort({arg},count,sizeof *{arg},{fn}); }}
''',
}
WORDS='atlas cedar delta ember flora glade harbor ivory jade kernel lagoon maple nova orbit prism quartz river solar tundra umber violet willow xenon yellow zenith aurora breeze canyon dawn echo forest grove horizon iris juniper meadow north opal pine'.split()
def main():
 root=PackSpec.open('c').dataset_root/'sources/curriculum-v1';hashes={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   rng=random.Random(20743+101*index+variant);w=rng.sample(WORDS,7)
   values=dict(fn=w[0]+'_read',other=w[1]+'_apply',arg=w[2],item=w[3].title()+'Entry',tag=w[4]+'_entry',word=w[5],upper=w[6].upper(),n=rng.randrange(2,24),n2=rng.randrange(25,99))
   source=template.format(**values)
   if variant%3==1:source=source.replace('\n','\r\n')
   if variant%4==2:source=source.replace('  ','\t')
   raw=source.encode();target=root/family/f'{variant:02d}.c';target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve original curriculum; create a new revision')
   if not target.exists():target.write_bytes(raw)
   hashes[target.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
 p=root/'LICENSE'
 if not p.exists():p.write_text('Original C syntax tasks authored for Neural Semantic Highlighting.\nPrivate development dataset. No Golden/Playground or upstream examples copied.\n')
 lock={'format':'nsh-c-curriculum-v1','generatorSha256':file_hash(Path(__file__)),'files':hashes};p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve existing curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'C tasks across',len(TEMPLATES),'families')
if __name__=='__main__':main()
