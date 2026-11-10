const std = @import("std");

const document =
    \\{
    \\  "title": "星空 🌌",
    \\  "version": "0.17.1"
    \\}
;

fn @"print document"(text: []const u8) void {
    // Quoted identifiers and multiline strings retain their original bytes.
    std.debug.print("{s}\n", .{text});
}

pub fn main() void {
    @"print document"(document);
}
