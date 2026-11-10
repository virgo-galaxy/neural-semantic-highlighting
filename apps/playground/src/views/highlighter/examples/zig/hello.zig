const std = @import("std");

pub fn main(init: std.process.Init) !void {
    var buffer: [1024]u8 = undefined;
    var output: std.Io.File.Writer = .init(.stdout(), init.io, &buffer);
    const writer = &output.interface;

    try greet(writer, "Zig 0.17.1");
    try writer.flush();
}

fn greet(writer: *std.Io.Writer, name: []const u8) !void {
    try writer.print("Hello, {s}!\n", .{name});
}
