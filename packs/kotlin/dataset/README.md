# Kotlin dataset

Use `make dataset-kotlin`. Original source and licenses stay under
`~/Datasets/neural-semantic-highlighting/kotlin`, or `$NSH_DATASET_ROOT/kotlin`.
Full training checkpoints remain under `artifacts/kotlin`; neither is committed.

`upstreams.json` pins every original Git source/license blob from Kotlin stdlib,
Kotlinx Coroutines, Kotlinx Serialization and Android Compose samples. Capture
includes 225 `.kt` files and 54 `.kts` files with complete original licenses/notices,
unchanged bytes and source locks. No collected project, import, annotation, script,
Gradle dependency or compiler plugin runs. Original task generators create 69
language and 14 script families, with 24 variants per family and retained seeds.
Golden, tests and Playground never enter collection roots.

The shared pipeline publishes immutable corpus/Gold/prepared snapshots, excludes
exact/lexical/normalized cross-family copies before windows and freezes intact
source families before training. Kotlin and script natural/focus evidence stays
separate. Future revisions preserve every initial assignment and previous snapshot.

Gold reuses JDK 22.0.1 and pinned official Kotlin 2.4.21 Maven parser components in
`artifacts/tools/kotlin-gold`. Maven checksums, strong local JAR hashes, original
embedded licenses, helper source/build hashes and JDK provenance remain recorded.
`make dataset-kotlin-tools` prepares this isolated cache; it installs no Kotlin SDK,
Gradle, Android SDK or global dependency. `NSH_KOTLIN_JAVA_HOME` can select an
existing matching JDK. The parser's LF input adapter restores original UTF-16
positions for CRLF/CR and BOM while preserving all collected/training source bytes.
Parse errors, unknown tokens and original coverage/Unicode errors fail closed.
