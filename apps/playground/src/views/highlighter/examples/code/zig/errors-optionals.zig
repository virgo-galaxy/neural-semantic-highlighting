const std = @import("std");

fn parse(text: []const u8) !u32 {
    if (text.len == 0) return error.Empty;
    return try std.fmt.parseInt(u32, text, 10);
}

fn defaultValue(value: ?u32) u32 {
    return value orelse 42;
}

pub fn main() void {
    const number = parse("17") catch |err| {
        std.debug.print("Could not parse: {s}\n", .{@errorName(err)});
        return;
    };
    std.debug.print("{d} / {d}\n", .{number, defaultValue(null)});
}
