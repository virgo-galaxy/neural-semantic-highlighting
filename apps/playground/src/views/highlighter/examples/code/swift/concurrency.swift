import Foundation

actor DocumentCache {
    private var entries: [String: String] = [:]

    func store(_ content: String, for key: String) {
        entries[key] = content
    }

    func content(for key: String) -> String? {
        entries[key]
    }
}

func loadDocument(_ key: String, cache: DocumentCache) async throws -> String {
    if let existing = await cache.content(for: key) {
        return existing
    }
    try await Task.sleep(for: .milliseconds(10))
    let content = "Document: \(key)"
    await cache.store(content, for: key)
    return content
}
