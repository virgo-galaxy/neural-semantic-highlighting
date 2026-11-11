"""Original modern Kotlin task families, never Golden or Playground copies."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash

TEMPLATES={
'function':'fun @FN@(value: Int, extra: Int = @N@): Int = value + extra',
'locals':'fun @FN@(values: List<Int>): Int { var total = @N@; for (item in values) { total += item }; return total }',
'named-args':'fun @FN@(title: String, enabled: Boolean = true) = if (enabled) title else "@WORD@"\nval result = @FN@(enabled = false, title = "start")',
'vararg':'fun @FN@(vararg values: Int): Int = values.sum() + @N@',
'generic-function':'fun <T> @FN@(value: T, block: (T) -> String): String = block(value)',
'generic-class':'class @TYPE@<T>(val value: T) { fun <R> map(transform: (T) -> R): R = transform(value) }',
'generic-where':'fun <T> @FN@(values: List<T>): List<T> where T : Comparable<T> = values.sorted()',
'variance':'interface @TYPE@<out T> { fun get(): T }; class Sink<in T> { fun put(value: T) { println(value) } }',
'reified':'inline fun <reified T> @FN@(value: Any): Boolean = value is T',
'class':'class @TYPE@(val title: String, var count: Int = @N@) { fun next(): Int { count += 1; return count } }',
'data':'data class @TYPE@(val id: Long, val label: String, val active: Boolean = true)\nfun @FN@(value: @TYPE@) = value.copy(label = "@WORD@")',
'secondary':'class @TYPE@(val value: Int) { constructor(text: String) : this(text.toInt()); fun show() = value + @N@ }',
'constructor-init':'class @TYPE@(initial: Int) { val value: Int; init { value = initial + @N@ }; fun show() = value }',
'interface':'interface @TYPE@ { val name: String; fun process(input: String): String }; class Item : @TYPE@ { override val name = "@WORD@"; override fun process(input: String) = input.trim() }',
'abstract':'abstract class @TYPE@ { abstract val value: Int; open fun describe() = "@WORD@" }; class Item : @TYPE@() { override val value = @N@ }',
'object':'object @TYPE@ { const val LIMIT = @N@; fun label() = "@WORD@" }\nfun @FN@() = @TYPE@.label()',
'companion':'class @TYPE@(val value: Int) { companion object Factory { fun create() = @TYPE@(@N@) } }',
'enum':'enum class @TYPE@(val code: Int) { Ready(1), Waiting(@N@), Done(3) }; fun @FN@(value: @TYPE@) = value == @TYPE@.Ready',
'sealed':'sealed interface @TYPE@; data class Success(val value: Int) : @TYPE@; data object Empty : @TYPE@\nfun @FN@(value: @TYPE@): Int = when(value) { is Success -> value.value; Empty -> @N@ }',
'value-class':'@JvmInline value class @TYPE@(val value: String)\nfun @FN@(id: @TYPE@) = id.value + "@WORD@"',
'extension':'fun String.@FN@(): String = trim().lowercase() + "@WORD@"',
'extension-property':'val String.@FN@: Int get() = length + @N@',
'get-set':'class @TYPE@ { private var stored = @N@; var value: Int get() = stored; set(next) { stored = next.coerceAtLeast(0) } }',
'backing-field':'class @TYPE@ { var value: Int = @N@; set(next) { field = next.coerceAtLeast(0) } }',
'delegate':'class @TYPE@ { val message: String by lazy { "@WORD@" }; fun show() = message.length + @N@ }',
'observable':'import kotlin.properties.Delegates\nclass @TYPE@ { var count by Delegates.observable(@N@) { property, old, new -> println("${property.name}: $old -> $new") } }',
'lateinit':'class @TYPE@ { lateinit var title: String; fun ready() = this::title.isInitialized; fun show() = title + "@WORD@" }',
'lambda-explicit':'fun @FN@(values: List<Int>) = values.map { number -> number + @N@ }.filter { it > 0 }',
'lambda-typed':'val @FN@: (Int, Int) -> Int = { left: Int, right: Int -> left + right + @N@ }',
'implicit-it':'fun @FN@(values: List<String>) = values.filter { it.isNotBlank() }.map { it.trim() + "@WORD@" }',
'callable-ref':'fun @FN@(values: List<String>) = values.map(String::length).filter { it > @N@ }',
'destructuring':'fun @FN@(values: Map<String, Int>): Int { var sum = @N@; for ((key, value) in values) { println(key); sum += value }; return sum }',
'data-destructure':'data class @TYPE@(val x: Int, val y: Int)\nfun @FN@(point: @TYPE@): Int { val (left, right) = point; return left + right + @N@ }',
'nullable':'fun @FN@(text: String?): Int = text?.trim()?.length ?: @N@',
'nonnull':'fun @FN@(value: String?): String { requireNotNull(value); return value + "@WORD@" }',
'safe-cast':'fun @FN@(value: Any?): Int { val text = value as? String; return text?.length ?: @N@ }',
'smart-cast':'fun @FN@(value: Any): Int = if (value is String) value.length else @N@',
'when':'fun @FN@(code: Int): String = when(code) { 0 -> "@WORD@"; in 1..@N@ -> "active"; else -> "other" }',
'when-variable':'fun @FN@(text: String): Int = when (val size = text.length) { 0 -> @N@; else -> size * 2 }',
'loops':'fun @FN@(limit: Int): Int { var total = 0; for (index in 0 until limit step 2) total += index; while (total < @N@) total++; return total }',
'label':'fun @FN@(values: List<Int>): Int { var total = @N@; outer@ for (left in values) { for (right in values) { if (left == right) continue@outer; total += right } }; return total }',
'exception':'fun @FN@(text: String): Int = try { text.toInt() } catch (problem: NumberFormatException) { println(problem.message); @N@ } finally { println("@WORD@") }',
'suspend':'suspend fun @FN@(value: Int): String = "@WORD@ ${value + @N@}"',
'coroutines':'import kotlinx.coroutines.*\nsuspend fun @FN@(): Int = coroutineScope { val task = async { @N@ }; task.await() + 1 }',
'flow':'import kotlinx.coroutines.flow.*\nfun @FN@(values: List<Int>): Flow<Int> = values.asFlow().map { it + @N@ }.filter { it > 0 }',
'flow-builder':'import kotlinx.coroutines.flow.*\nfun @FN@(): Flow<String> = flow { emit("@WORD@"); emit("${@N@}") }',
'channel':'import kotlinx.coroutines.channels.Channel\nsuspend fun @FN@(channel: Channel<Int>) { for (value in channel) { println(value + @N@) } }',
'collections':'fun @FN@(values: List<Int>) = values.asSequence().filter { it > @N@ }.map { it * 2 }.toList()',
'map':'fun @FN@(words: List<String>): Map<String, Int> = words.associateWith { it.length + @N@ }',
'scope-functions':'fun @FN@(text: String?): String = text?.let { it.trim() }?.takeIf { it.isNotEmpty() } ?: "@WORD@"',
'infix':'infix fun Int.@FN@(other: Int): Int = this + other + @N@\nval result = 1 @FN@ 2',
'operator':'data class @TYPE@(val value: Int) { operator fun plus(other: @TYPE@) = @TYPE@(value + other.value); operator fun get(index: Int) = value + index }',
'interpolation':'fun @FN@(name: String, count: Int): String = "@WORD@ $name: ${count + @N@}"',
'raw-string':'val @FN@ = """C:\\@WORD@\\documents\n  literal "quotes" and /* text */\n""".trimIndent()',
'raw-template':'fun @FN@(name: String) = """\n@WORD@ $name\nCount: ${@N@ + 1} 🌌\n""".trimIndent()',
'multi-dollar':'fun @FN@(name: String): String = $$"""@WORD@ $literal $$name $${@N@ + 1}"""',
'escapes':r'fun @FN@(value: Int) = "@WORD@ \"quoted\" and \\ path\n$value"',
'characters':r"val @FN@ = listOf('a', '\n', '\u03a9', '\\')",
'comments':'/** Original @WORD@ 🌌 documentation. */\nfun @FN@(value: Int) = /* outer /* nested */ comment */ value + @N@ // end\n',
'annotations':'@Deprecated("use @WORD@") fun @FN@(value: Int) = value + @N@',
'use-site':'annotation class Mark\nclass @TYPE@(@field:Mark val name: String) { @get:Mark val value: Int get() = @N@ }',
'file-annotation':'@file:JvmName("@TYPE@")\npackage example.@WORD@\nfun @FN@() = @N@',
'context':'interface @TYPE@ { fun log(text: String) }\ncontext(logger: @TYPE@) fun @FN@(value: Int) { logger.log("@WORD@ $value") }',
'context-value':'class @TYPE@(val count: Int)\ncontext(data: @TYPE@) fun @FN@(): Int = data.count + @N@',
'backticks':'fun `@WORD@ process`(value: Int) = value + @N@\nval @FN@ = `@WORD@ process`(1)',
'compose':'import androidx.compose.runtime.Composable\nimport androidx.compose.material3.Text\n@Composable fun @FN@(name: String) { Text(text = "@WORD@ $name") }',
'compose-state':'import androidx.compose.runtime.*\nimport androidx.compose.material3.*\n@Composable fun @FN@() { var count by remember { mutableStateOf(@N@) }; Button(onClick = { count++ }) { Text("@WORD@: $count") } }',
'compose-list':'import androidx.compose.runtime.Composable\nimport androidx.compose.foundation.lazy.*\nimport androidx.compose.material3.Text\n@Composable fun @FN@(names: List<String>) { LazyColumn { items(names) { name -> Text("@WORD@ $name") } } }',
'numbers':'val @FN@ = listOf(1_000L, 0xff, 0b1010, @N@, 1.5e-3)',
}
SCRIPTS={
'plugins':'val release = "@N@.0"\nplugins { kotlin("jvm") version "2.4.21" }\nprintln("@WORD@ $release")',
'repositories':'val endpoint = "https://@WORD@.example"\nrepositories { mavenCentral(); maven { url = uri("$endpoint/releases") } }',
'dependencies':'val libraryVersion = "@N@.1"\ndependencies { implementation("example:@WORD@:$libraryVersion"); testImplementation(kotlin("test")) }',
'configuration':'val target = "@WORD@"\nkotlin { jvmToolchain(22); compilerOptions { freeCompilerArgs.add("-module-name=$target") } }',
'register-task':'val label = "@WORD@"\ntasks.register("announce") { doLast { println("$label ${@N@}") } }',
'process-values':'val @FN@ = listOf(@N@, 2, 3).filter { it > 1 }.map { "@WORD@ $it" }\n@FN@.forEach { println(it) }',
'file-text':'val folder = "@WORD@"\nval destination = "$folder/output.txt"\nval content = listOf("alpha", "beta").joinToString("\\n") { "$it @N@" }\nprintln("$destination $content")',
'functions':'fun @FN@(value: String): String = value.trim() + "@WORD@"\nval name = @FN@("  source  ")\nlistOf(name).forEach { println("$it ${@N@}") }',
'script-classes':'data class @TYPE@(val title: String)\nval entries = listOf(@TYPE@(title = "@WORD@"))\nentries.forEach { println("${it.title} @N@") }',
'options':'val mode: String? = "@WORD@"\nval label = mode?.let { "$it @N@" } ?: "default"\nprintln(label)',
'publishing':'val artifactName = "@WORD@"\npublishing { publications { create<MavenPublication>("release") { artifactId = "$artifactName-@N@" } } }',
'when':'val code = @N@\nval label = when (code) { 0 -> "idle"; else -> "@WORD@ $code" }\nlistOf(label).forEach { println(it) }',
'raw-script':'val name = "@WORD@"\nval text = """\nHi $name\nTotal ${@N@ + 1}\n"""\ntext.lines().filter { it.isNotBlank() }.forEach { println(it) }',
'extension':'fun String.@FN@() = trim().lowercase()\nval labels = listOf("@WORD@", "source").map { "${it.@FN@()} @N@" }\nprintln(labels)',
}
WORDS='aurora bridge cosmos delta ember forest galaxy harbor island juniper kernel lumen meteor nova orbit prism quasar river solar tundra'.split()
def main():
 for profile,templates,folder,suffix in [('kotlin',TEMPLATES,'curriculum-v1','.kt'),('kotlin-script',SCRIPTS,'scripts-v1','.kts')]:
  root=PackSpec.open('kotlin').dataset_root/'sources'/folder;files={}
  for index,(family,template) in enumerate(templates.items()):
   for variant in range(24):
    rng=random.Random(64221+index*101+variant);word=WORDS[(index+variant)%len(WORDS)]
    source=template.replace('@FN@',word+'Process').replace('@TYPE@',word.title()+'Value').replace('@N@',str(rng.randrange(2,30))).replace('@WORD@',word)+'\n'
    if variant%4==1:source=source.replace('\n','\r\n')
    raw=source.encode();path=root/family/f'{variant:02}{suffix}';path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve previous Kotlin task')
    if not path.exists():path.write_bytes(raw)
    files[str(path.relative_to(root))]=hashlib.sha256(raw).hexdigest()
  license=b'Original Kotlin code/script tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or displayed-source copies.\n'
  path=root/'LICENSE'
  if path.exists() and path.read_bytes()!=license:raise ValueError('Preserve Kotlin task license')
  path.write_bytes(license)
  lock=dict(format='nsh-kotlin-curriculum-v1',profile=profile,generatorSha256=file_hash(Path(__file__)),families=len(templates),files=files,licenseSha256=hashlib.sha256(license).hexdigest())
  path=root/'source.lock.json'
  if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Preserve previous Kotlin curriculum lock')
  path.write_text(json.dumps(lock,indent=2)+'\n');print(profile,len(files),'original tasks;',len(templates),'families')
if __name__=='__main__':main()
