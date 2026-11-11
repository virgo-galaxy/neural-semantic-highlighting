"""Original Scala 2/3 task families, independent of Golden and displays."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'function':'def @FN@(value: Int, extra: Int = @N@): Int = value + extra',
'block-function':'def @FN@(values: List[Int]): Int = { val selected = values.filter(_ > @N@); selected.sum }',
'curried':'def @FN@(left: Int)(right: Int): Int = left + right + @N@',
'generic':'def @FN@[A](value: A)(transform: A => String): String = transform(value)',
'generic-class':'class @TYPE@[A](val value: A) { def map[B](f: A => B): B = f(value) }',
'variance':'trait @TYPE@[+A] { def value: A }; trait Sink[-A] { def put(value: A): Unit }',
'bound':'def @FN@[A <: Comparable[A]](values: List[A]): List[A] = values.sorted',
'context-bound':'def @FN@[A: Ordering](values: List[A]) = values.sorted.take(@N@)',
'class':'class @TYPE@(val title: String, var count: Int) { def next(): Int = { count += @N@; count } }',
'case-class':'case class @TYPE@(id: Long, title: String)\ndef @FN@(item: @TYPE@) = item.copy(title = "@WORD@")',
'object':'object @TYPE@ { val limit = @N@; def name: String = "@WORD@" }',
'companion':'case class @TYPE@(value: Int)\nobject @TYPE@ { def initial = new @TYPE@(@N@) }',
'inheritance':'trait @TYPE@ { def name: String }; class Record extends @TYPE@ { override def name = "@WORD@" }',
'abstract':'abstract class @TYPE@ { def value: Int; def label = s"@WORD@ $value" }',
'sealed':'sealed trait @TYPE@; case class Ready(value: Int) extends @TYPE@; case object Empty extends @TYPE@',
'enum':'enum @TYPE@:\n  case Pending, Ready, Done\ndef @FN@(state: @TYPE@) = state match\n  case @TYPE@.Ready => @N@\n  case _ => 0',
'enum-data':'enum @TYPE@:\n  case Value(number: Int)\n  case Empty\ndef @FN@(n: Int) = @TYPE@.Value(n)',
'given':'given @FN@: Ordering[Int] with\n  def compare(left: Int, right: Int): Int = left - right',
'given-alias':'given @FN@: Int = @N@\ndef result(using value: Int): Int = value + 1',
'using':'def @FN@(text: String)(using logger: Logger): Unit = logger.log(s"@WORD@ $text")',
'extension':'extension (value: String)\n  def @FN@: String = value.trim + "@WORD@"',
'extension-generic':'extension [A](values: List[A])\n  def @FN@(f: A => String): List[String] = values.map(f)',
'opaque':'object @TYPE@ { opaque type Id = Long; def create(value: Long): Id = value + @N@ }',
'union':'type @TYPE@ = String | Int\ndef @FN@(value: @TYPE@): String = value match { case text: String => text; case number: Int => number.toString }',
'intersection':'trait First; trait Second\ndef @FN@(value: First & Second) = value.toString + "@WORD@"',
'lambda':'val @FN@ = (value: Int) => value + @N@',
'lambda-block':'def @FN@(values: List[Int]) = values.map { value => val next = value + @N@; next * 2 }',
'placeholder':'def @FN@(values: List[Int]) = values.filter(_ > @N@).map(_ * 2)',
'pattern':'def @FN@(value: Option[Int]): Int = value match { case Some(number) => number + @N@; case None => 0 }',
'pattern-guard':'def @FN@(value: Any): Int = value match { case n: Int if n > @N@ => n; case _ => 0 }',
'destructure':'def @FN@(pair: (String, Int)): String = { val (name, count) = pair; s"@WORD@ $name ${count + @N@}" }',
'for':'def @FN@(values: List[Int]) = for (value <- values if value > @N@) yield value * 2',
'for-indent':'def @FN@(values: List[Int]) =\n  for\n    value <- values\n    if value > @N@\n  yield value + 1',
'if-indent':'def @FN@(value: Int): String =\n  if value > @N@ then\n    "@WORD@"\n  else\n    "other"',
'while':'def @FN@(limit: Int): Int = { var n = @N@; while (n < limit) n += 1; n }',
'future':'import scala.concurrent.{ExecutionContext, Future}\ndef @FN@(value: Int)(using ec: ExecutionContext): Future[Int] = Future(value + @N@)',
'option':'def @FN@(value: Option[String]): String = value.map(_.trim).filter(_.nonEmpty).getOrElse("@WORD@")',
'either':'def @FN@(value: Either[String, Int]) = value.map(number => number + @N@)',
'collections':'def @FN@(values: List[Int]) = values.groupBy(_ % @N@).view.mapValues(_.sum).toMap',
'named-args':'def @FN@(title: String, enabled: Boolean = true) = if (enabled) title else "@WORD@"\nval result = @FN@(enabled = false, title = "source")',
'exception':'def @FN@(text: String): Int = try { text.toInt } catch { case problem: NumberFormatException => @N@ } finally { println("@WORD@") }',
'annotation':'@deprecated("use @WORD@", "1.0") def @FN@(value: Int) = value + @N@',
'imports':'import scala.collection.{mutable => m, _}\nval @FN@ = m.ListBuffer(@N@, 2, 3)',
'exports':'object @TYPE@ { val value = @N@ }\nobject Exposed { export @TYPE@.value }',
'package':'package example.@WORD@\nobject @TYPE@ { def @FN@ = @N@ }',
'interpolation':'def @FN@(name: String, count: Int) = s"@WORD@ $name: ${count + @N@}"',
'raw-interpolation':'def @FN@(name: String) = raw"C:\\@WORD@\\$name"',
'multiline':'def @FN@(name: String) = s"""\n@WORD@ $name\nCount ${@N@ + 1} 🌌\n""".stripMargin',
'plain-triple':'val @FN@ = """\n@WORD@ { "value": 1 }\nC:\\records\\raw\n// literal text\n"""',
'format':'def @FN@(value: Double) = f"@WORD@ $value%.2f"',
'backticks':'val `@WORD@ value` = @N@\ndef @FN@(`input value`: Int) = `input value` + `@WORD@ value`',
'comments':'/** @WORD@ report 🌌. */\ndef @FN@(value: Int) = /* outer /* inner */ comment */ value + @N@ // result\n',
'numbers':'val @FN@ = List(@N@L, 0xff, 1.25e-3, 2.5f)',
'sbt':'name := "@WORD@"\nversion := "1.0"\nlibraryDependencies += "org.example" %% "module" % "@N@.0"',
}
WORDS='alder bloom coral drift ember field glade haven ivy juniper kite lake moss night olive peak quill rain stone vale'.split()
def main():
 root=PackSpec.open('scala').dataset_root/'sources/curriculum-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   word=WORDS[(index+variant)%len(WORDS)];rng=random.Random(3111+index*101+variant)
   source=template.replace('@FN@',word+'Process').replace('@TYPE@',word.title()+'Value').replace('@WORD@',word).replace('@N@',str(rng.randrange(2,30)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{variant:02}.scala';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve previous Scala task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original Scala tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original Scala license')
 p.write_bytes(license);lock=dict(format='nsh-scala-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve previous Scala curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'tasks in',len(TEMPLATES),'families')
if __name__=='__main__':main()
