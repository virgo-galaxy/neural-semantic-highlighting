import Foundation

func greeting(for name: String, excited: Bool = false) -> String {
    let title = name.trimmingCharacters(in: .whitespacesAndNewlines)
    return "Hello, \(title)" + (excited ? "!" : ".")
}

let names = ["Virgo", "星空 🌌", "Swift"]
for name in names {
    print(greeting(for: name, excited: true))
}
