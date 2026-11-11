"""Independent mixed Kotlin tasks; preserve the initial curriculum and split families."""
from pathlib import Path
import hashlib
import json
import random

from training.shared.spec import PackSpec, file_hash


LITERALS = {
    'raw-lines': '"""\nRecord @WORD@\nThe requested value is $value.\nResult ${value.length + @N@} units\n""".trimIndent()',
    'raw-quotes': '"""\n{ "kind": "@WORD@", "value": "$value", "limit": ${@N@ + 1} }\n""".trimIndent()',
    'raw-path': '"""\nC:\\workspace\\@WORD@\nA "quoted" value: $value\n/* string text, not comment */\n"""',
    'dollar-raw': '$$"""\n{ "$id": "@WORD@", "result": "$$value", "size": $${value.length + @N@} }\n"""',
    'triple-dollar': '$$$"""\n$ and $$ are text for @WORD@\nActual value: $$$value, size: $$${value.length}\n"""',
    'nested-template': '"result ${value.trim().ifEmpty { "@WORD@" }}: ${value.length + @N@}"',
    'plain-template': '"@WORD@ $value -> ${value.uppercase()} / ${@N@ + value.length}"',
    'raw-comment-text': '"""\n# @WORD@\n// value $value\n/* ${value.length} */\ncharacters \\n \\t stay raw\n"""',
}


def main():
    root = PackSpec.open('kotlin').dataset_root / 'sources/mixed-v1'
    files = {}
    for family_index, family in enumerate([*LITERALS, 'nested-types', 'context-call', 'lambda-scope', 'nested-comments']):
        for variant in range(24):
            rng = random.Random(82421 + family_index * 100 + variant)
            word = ['cedar', 'falcon', 'lagoon', 'meadow', 'nebula', 'orchid'][variant % 6]
            count = str(rng.randrange(3, 90))
            suffix = str(variant)
            if family in LITERALS:
                literal = LITERALS[family].replace('@WORD@', word).replace('@N@', count)
                source = f'''package tasks.{word}

data class Entry{suffix}(val title: String, val count: Int)

fun format{suffix}(value: String, enabled: Boolean): String {{
    val prefix = value.trim()
    val text = {literal}
    val selected = if (enabled) text else prefix
    return selected + " / $prefix"
}}

fun entries{suffix}(items: List<Entry{suffix}>): List<String> =
    items.filter {{ it.count > {count} }}.map {{ item -> format{suffix}(item.title, true) }}
'''
            elif family == 'nested-types':
                source = f'''interface Keyed{suffix}<Identity> {{ val key: Identity }}
class Store{suffix}<Identity, Element : Keyed{suffix}<Identity>>(private val records: List<Element>) {{
    fun lookup(key: Identity): Element? = records.firstOrNull {{ it.key == key }}
    fun <Output> project(transform: (Element) -> Output): List<Output> = records.map {{ transform(it) }}
}}
sealed interface Outcome{suffix} {{
    data object Waiting : Outcome{suffix}
    data class Available(val payload: String) : Outcome{suffix}
}}
'''
            elif family == 'context-call':
                source = f'''interface Reporter{suffix} {{ fun write(line: String) }}
context(reporter: Reporter{suffix})
fun publish{suffix}(text: String) {{
    val normalized = text.trim()
    reporter.write("{word}: $normalized / ${{normalized.length + {count}}}")
}}
class Console{suffix} : Reporter{suffix} {{ override fun write(line: String) {{ println(line) }} }}
'''
            elif family == 'lambda-scope':
                source = f'''fun transform{suffix}(input: List<String>): List<String> {{
    val prefix = "{word}"
    return input.filter {{ it.isNotBlank() }}.map {{ raw ->
        val clean = raw.trim()
        clean.takeIf {{ it.length > {count} }}?.let {{ "$prefix/$it" }} ?: clean
    }}
}}
'''
            else:
                source = f'''/** {word} report, with a nested /* interior */ comment. */
fun compute{suffix}(amount: Int): Int {{
    // A literal dollar $ does not start a template here.
    val offset = {count} /* outer /* inner */ tail */
    return amount + offset
}}
'''
            if variant % 4 == 1:
                source = source.replace('\n', '\r\n')
            raw = source.encode()
            path = root / family / f'{variant:02}.kt'
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != raw:
                raise ValueError('Preserve previous Kotlin mixed task')
            if not path.exists():
                path.write_bytes(raw)
            files[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
    license = b'Original Kotlin mixed tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or displayed-source copies.\n'
    path = root / 'LICENSE'
    if path.exists() and path.read_bytes() != license:
        raise ValueError('Preserve original license')
    path.write_bytes(license)
    lock = dict(format='nsh-kotlin-mixed-v1', generatorSha256=file_hash(Path(__file__)),
                families=12, files=files, licenseSha256=hashlib.sha256(license).hexdigest())
    path = root / 'source.lock.json'
    if path.exists() and json.loads(path.read_text()) != lock:
        raise ValueError('Preserve previous Kotlin mixed lock')
    path.write_text(json.dumps(lock, indent=2) + '\n')
    print(len(files), 'original mixed tasks in 12 independent families')


if __name__ == '__main__':
    main()
