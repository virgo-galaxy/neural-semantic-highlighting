import SwiftUI

struct CounterCard: View {
    let title: String
    @State private var count = 0

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
            Text("Count: \(count)")
                .monospacedDigit()
            Button("Add one", systemImage: "plus") {
                count += 1
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
    }
}
