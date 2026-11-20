const std = @import("std");

const Counter = struct {
    value: u32 = 0,

    fn increment(self: *Counter) void {
        self.value += 1;
    }
};

const State = enum { idle, ready };

pub fn main() void {
    var counter: Counter = .{};
    counter.increment();
    const state: State = .ready;
    std.debug.print("Count: {d}, state: {s}\n", .{counter.value, @tagName(state)});
}
