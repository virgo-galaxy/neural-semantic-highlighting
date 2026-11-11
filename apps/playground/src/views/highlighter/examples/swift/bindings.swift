import SwiftUI

struct DocumentEditor: View {
    @Binding var title: String
    @State private var isPublished = false

    var body: some View {
        Form {
            Section("Document") {
                TextField("Title", text: $title)
                Toggle("Published", isOn: $isPublished)
            }
            Section {
                if title.isEmpty {
                    Label("Add a title", systemImage: "info.circle")
                        .foregroundStyle(.secondary)
                } else {
                    Text("Preview: \(title)")
                }
            }
        }
    }
}
