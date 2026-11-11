import Foundation

func message(for name: String, count: Int) -> String {
    let path = #"/Users/virgo/Documents/\(literal)/data"#
    let raw = ##"Raw interpolation: \##(count), ordinary \(text)"##
    let details = """
    Hello, \(name) 🌌
    You have \(count) documents. \
    Keep creating.
    """
    let pattern = #/[a-z]+@[a-z]+\.[a-z]+/#
    let matches = "hello@virgo.dev".wholeMatch(of: pattern) != nil
    return "\(path)\n\(raw)\n\(details)\nEmail: \(matches)"
}
