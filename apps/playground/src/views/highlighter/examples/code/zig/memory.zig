const std = @import("std");

pub fn main() !void {
    const gpa = std.heap.page_allocator;
    var values: std.ArrayList(u32) = .empty;
    defer values.deinit(gpa);

    try values.append(gpa, 17);
    try values.appendSlice(gpa, &.{21, 42});

    const text = try gpa.dupeSentinel(u8, "Current Zig", 0);
    defer gpa.free(text);

    std.debug.print("{s}: {any}\n", .{text, values.items});
}
