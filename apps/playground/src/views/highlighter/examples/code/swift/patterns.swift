enum LoadState<Value> {
    case idle
    case loading(progress: Double)
    case loaded(Value)
    case failed(message: String)
}

func describe(_ state: LoadState<[String]>) -> String {
    switch state {
    case .idle:
        "Ready"
    case .loading(let progress):
        "Loading: \(Int(progress * 100))%"
    case .loaded(let documents) where !documents.isEmpty:
        "\(documents.count) documents"
    case .loaded:
        "No documents"
    case .failed(let message):
        message
    }
}
