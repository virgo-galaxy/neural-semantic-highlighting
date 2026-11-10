const std = @import("std");

fn Vector(comptime T: type, comptime size: usize) type {
    return struct {
        values: [size]T,

        fn sum(self: @This()) T {
            var total: T = 0;
            inline for (self.values) |value| total += value;
            return total;
        }
    };
}

pub fn main() void {
    const Vec = Vector(u32, 3);
    const vector: Vec = .{.values = .{1, 2, 3}};
    std.debug.print("Sum: {d}\n", .{vector.sum()});
}
