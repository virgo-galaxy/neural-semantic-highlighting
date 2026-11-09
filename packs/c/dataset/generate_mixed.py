"""Original multiline C tasks; never copied from development probes."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
from .generate_curriculum import WORDS

PROGRAMS={
'formatted-output':'''#include <stdio.h>

static int {fn}(const char *{arg}, unsigned count)
{{
    const char *prefix = "{word} status: ";
    return printf("%s%s has %u items\\n", prefix, {arg}, count);
}}

int {other}(void)
{{
    return {fn}("{word} space inside", {n});
}}
''',
'stored-text':'''/* {word} text storage */
static const char *{arg} = "Multiple words stay in one literal 🌿";
static const double {other} = 0x1.ap-2;

char {fn}(unsigned index)
{{
    const char *message = "quoted \\\"{word}\\\" value\\n";
    return index < {n} ? {arg}[index] : message[0];
}}
''',
'code-in-text':'''#include <stdio.h>

int {fn}(const char *{arg})
{{
    char buffer[512];
    return snprintf(buffer, sizeof buffer,
        "{{\\\"name\\\": \\\"%s\\\", \\\"state\\\": \\\"{word} ready\\\"}}\\n",
        {arg});
}}
''',
'pointer-work':'''typedef struct {tag} {{
    int size;
    struct {tag} *tail;
}} {item};

int {fn}(const {item} *{arg})
{{
    int total = {n};
    while ({arg} != 0) {{
        total += {arg}->size;
        {arg} = {arg}->tail;
    }}
    return total;
}}
''',
'move-fields':'''typedef struct {tag} {{
    float width;
    float height;
}} {item};

void {fn}({item} *{arg}, float factor)
{{
    {arg}->width *= factor;
    {arg}->height *= factor;
}}

float {other}({item} box)
{{
    return box.width * box.height + {n}.0f;
}}
''',
'macro-output':'''#include <stdio.h>
#define {upper}_REPORT(format, ...) \\
    printf(format, __VA_ARGS__)
#define {upper}_MAX {n2}

int {fn}(unsigned {arg})
{{
    if ({arg} > {upper}_MAX) {{
        return {upper}_REPORT("{word} limit: %u\\n", {arg});
    }}
    return 0;
}}
''',
'macro-map':'''#ifndef {upper}_VALUES_H
#define {upper}_VALUES_H
#define {upper}_TWICE(x) \\
    ((x) + (x))

typedef struct {tag} {{
    unsigned value;
}} {item};

static inline unsigned {fn}(const {item} *{arg})
{{
    return {upper}_TWICE({arg}->value) + {n}U;
}}
#endif
''',
'callback-iteration':'''typedef int (*{item})(int value, void *state);

int {fn}(const int *{arg}, unsigned length,
         {item} accept, void *state)
{{
    int sum = 0;
    for (unsigned offset = 0; offset < length; ++offset) {{
        int value = {arg}[offset];
        if (accept(value, state)) {{
            sum += value;
        }}
    }}
    return sum + {n};
}}
''',
'modern-counter':'''#include <stdint.h>
#include <stdatomic.h>
_Static_assert(sizeof(uint64_t) >= 8, "{word} capacity");
static _Atomic uint64_t {arg} = {n};

uint64_t {fn}(uint64_t amount)
{{
    uint64_t before = atomic_fetch_add(&{arg}, amount);
    return before + amount;
}}
''',
'character-branches':'''/* Validate the {word} alphabet. */
int {fn}(char {arg})
{{
    if ({arg} >= 'a' && {arg} <= 'z') {{
        return {arg} - 'a' + {n};
    }}
    if ({arg} >= 'A' && {arg} <= 'Z') {{
        return {arg} - 'A';
    }}
    return -1;
}}
''',
'cleanup':'''#include <stdlib.h>
#include <string.h>

int {fn}(const char *{arg})
{{
    char *copy = malloc(strlen({arg}) + 1);
    if (!copy) goto failed;
    strcpy(copy, {arg});
    int length = (int)strlen(copy) + {n};
    free(copy);
    return length;
failed:
    return -1;
}}
''',
'conditional-header':'''#ifndef {upper}_H
#define {upper}_H
#include <stddef.h>

#if defined({upper}_WIDE)
typedef unsigned long {item};
#else
typedef unsigned {item};
#endif

static inline {item} {fn}({item} {arg})
{{
    /* A module-local operation with spaced source. */
    return {arg} + {n};
}}
#endif
''',
}
def main():
 root=PackSpec.open('c').dataset_root/'sources/mixed-v1';hashes={}
 for index,(family,template) in enumerate(PROGRAMS.items()):
  for variant in range(24):
   rng=random.Random(31817+107*index+variant);w=rng.sample(WORDS,7);values=dict(fn=w[0]+'_convert',other=w[1]+'_send',arg=w[2],item=w[3].title()+'Data',tag=w[4]+'_data',word=w[5],upper=w[6].upper(),n=rng.randrange(2,25),n2=rng.randrange(30,100))
   source=template.format(**values)
   indent=['    ','  ','\t'][variant%3];source=source.replace('    ',indent)
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();target=root/family/f'{variant:02d}.c';target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve existing source; use a new revision')
   if not target.exists():target.write_bytes(raw)
   hashes[target.relative_to(root).as_posix()]=hashlib.sha256(raw).hexdigest()
 license=root/'LICENSE'
 if not license.exists():license.write_text('Original multiline C syntax tasks for Neural Semantic Highlighting.\nPrivate development dataset; no Golden, Playground or upstream copies.\n')
 lock={'format':'nsh-c-mixed-v1','generatorSha256':file_hash(Path(__file__)),'files':hashes};target=root/'source.lock.json'
 if target.exists() and json.loads(target.read_text())!=lock:raise ValueError('Preserve existing mixed lock')
 target.write_text(json.dumps(lock,indent=2)+'\n');print(len(hashes),'C mixed tasks across',len(PROGRAMS),'families')
if __name__=='__main__':main()
