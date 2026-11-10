const std = @import("std");

const User = struct {
    name: []const u8,
    active: bool = true,
};

pub fn main() void {
    const info = @typeInfo(User).@"struct";
    inline for (info.field_names, info.field_types) |name, T| {
        std.debug.print("{s}: {s}\n", .{name, @typeName(T)});
    }
    std.debug.print("Has name: {}\n", .{@hasField(User, "name")});
}
