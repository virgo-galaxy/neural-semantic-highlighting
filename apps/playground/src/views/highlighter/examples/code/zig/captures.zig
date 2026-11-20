const std = @import("std");

const Result = union(enum) { count: u32, name: []const u8 };

pub fn main() void {
    var values = [_]u32{2, 4, 8};
    for (&values, 0..) |*value, index| {
        value.* += @intCast(index);
    }

    const maybe: ?u32 = values[0];
    if (maybe) |value| std.debug.print("First: {d}\n", .{value});

    const result: Result = .{.name = "Aurora"};
    switch (result) {
        .count => |count| std.debug.print("{d}\n", .{count}),
        .name => |name| std.debug.print("{s}\n", .{name}),
    }
}
