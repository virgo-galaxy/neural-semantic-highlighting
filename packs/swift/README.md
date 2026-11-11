# Swift pack

Original `.swift` source, including common SwiftUI view/builder code. Functions,
types/protocols/extensions, generics, enums/patterns, closures, async/actors,
attributes, property wrappers and original literal forms share one model.

See the [semantic contract](SEMANTICS.md), [dataset](dataset/README.md),
[independent Golden](fixtures/README.md) and [training commands](../../training/swift/README.md).
Offline Gold uses the already installed official Swift 6.4.2 SwiftParser, without
resolving imports, typechecking projects, expanding macros or executing input.
The [official parser](https://github.com/swiftlang/swift-syntax) provides syntax;
source-local semantic roles remain approximations. No SDK is a browser dependency.
