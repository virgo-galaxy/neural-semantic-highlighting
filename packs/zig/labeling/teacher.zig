// Offline only. Read original source, use the pinned official AST/tokenizer,
// emit syntax metadata. Never compile/evaluate the input or follow imports.
const std = @import("std");
const Ast = std.zig.Ast;
const gpa = std.heap.page_allocator;
extern "c" fn getchar() c_int;
extern "c" fn write(c_int, [*]const u8, usize) isize;
const Token = struct { tag: []const u8, start: usize, end: usize, primitive: bool };
const Param = struct { name: u32, type_node: ?u32, comptime_token: ?u32 };
const Capture = struct { name: u32, first: u32, last: u32 };
const Record = struct {
    tag: []const u8,
    main: u32,
    first: u32,
    last: u32,
    name: ?u32 = null,
    type_node: ?u32 = null,
    init: ?u32 = null,
    callee: ?u32 = null,
    left: ?u32 = null,
    child_type: ?u32 = null,
    fields: ?[]const u32 = null,
    members: ?[]const u32 = null,
    container: ?[]const u8 = null,
    params: ?[]const Param = null,
    captures: ?[]const Capture = null,
    label: ?u32 = null,
    tuple_field: bool = false,
};
fn idx(n: Ast.Node.Index) u32 {
    return @backingInt(n);
}
fn opt(n: Ast.Node.OptionalIndex) ?u32 {
    return if (n.unwrap()) |v| idx(v) else null;
}
fn capture(tree: *const Ast, items: *std.ArrayList(Capture), start: ?u32, body: Ast.Node.Index) !void {
    var ti = start orelse return;
    while (ti < tree.tokens.len and tree.tokenTag(ti) != .pipe) : (ti += 1) {
        if (tree.tokenTag(ti) == .identifier) try items.append(gpa, .{ .name = ti, .first = ti, .last = tree.lastToken(body) });
    }
}
pub fn main() !void {
    if (comptime !std.mem.eql(u8, @import("builtin").zig_version_string, "0.17.1")) @compileError("Use the pinned Zig 0.17.1 SDK");
    var input: std.ArrayList(u8) = .empty;
    while (true) {
        const c = getchar();
        if (c < 0) break;
        try input.append(gpa, @intCast(c));
    }
    const source = try gpa.dupeSentinel(u8, input.items, 0);
    var tree = try Ast.parse(gpa, source, .{ .recover = false });
    defer tree.deinit(gpa);
    if (tree.errors.len != 0) return error.InvalidZigSyntax;
    var tokens: std.ArrayList(Token) = .empty;
    var tokenizer = std.zig.Tokenizer.init(source);
    while (true) {
        const t = tokenizer.next();
        try tokens.append(gpa, .{ .tag = @tagName(t.tag), .start = t.loc.start, .end = t.loc.end, .primitive = t.tag == .identifier and std.zig.primitives.isPrimitive(source[t.loc.start..t.loc.end]) });
        if (t.tag == .eof) break;
    }
    var nodes: std.ArrayList(Record) = .empty;
    for (0..tree.nodes.len) |i| {
        const n: Ast.Node.Index = @fromBackingInt(@intCast(i));
        const tag = tree.nodeTag(n);
        var r: Record = .{ .tag = @tagName(tag), .main = tree.nodeMainToken(n), .first = tree.firstToken(n), .last = tree.lastToken(n) };
        if (tree.fullVarDecl(n)) |v| {
            r.name = v.ast.mut_token + 1;
            r.type_node = opt(v.ast.type_node);
            r.init = opt(v.ast.init_node);
        }
        var fn_buf: [1]Ast.Node.Index = undefined;
        if (tree.fullFnProto(&fn_buf, n)) |f| {
            r.name = f.name_token;
            r.type_node = opt(f.ast.return_type);
            var params: std.ArrayList(Param) = .empty;
            var it = f.iterate(&tree);
            while (it.next()) |p| if (p.name_token) |name| {
                try params.append(gpa, .{ .name = name, .type_node = if (p.type_expr) |t| idx(t) else null, .comptime_token = p.comptime_noalias });
            };
            r.params = params.items;
        }
        var members_buf: [2]Ast.Node.Index = undefined;
        if (tree.fullContainerDecl(&members_buf, n)) |c| {
            var members: std.ArrayList(u32) = .empty;
            for (c.ast.members) |m| try members.append(gpa, idx(m));
            r.members = members.items;
            r.container = if (i == 0) "root" else @tagName(tree.tokenTag(c.ast.main_token));
        }
        if (tree.fullContainerField(n)) |f| {
            r.name = f.ast.main_token;
            r.type_node = opt(f.ast.type_expr);
            r.init = opt(f.ast.value_expr);
            r.tuple_field = f.ast.tuple_like;
        }
        var struct_buf: [2]Ast.Node.Index = undefined;
        if (tree.fullStructInit(&struct_buf, n)) |value| {
            r.type_node = opt(value.ast.type_expr);
            var fields: std.ArrayList(u32) = .empty;
            for (value.ast.fields) |field| {
                const first = tree.firstToken(field);
                if (first >= 3 and tree.tokenTag(first - 1) == .equal and tree.tokenTag(first - 2) == .identifier and tree.tokenTag(first - 3) == .period) try fields.append(gpa, first - 2);
            }
            r.fields = fields.items;
        }
        var call_buf: [1]Ast.Node.Index = undefined;
        if (tree.fullCall(&call_buf, n)) |call| r.callee = idx(call.ast.fn_expr);
        if (tree.fullPtrType(n)) |p| r.child_type = idx(p.ast.child_type);
        if (tree.fullArrayType(n)) |a| r.child_type = idx(a.ast.elem_type);
        switch (tag) {
            .field_access => {
                r.left = idx(tree.nodeData(n).node_and_token[0]);
                r.name = tree.nodeData(n).node_and_token[1];
            },
            .optional_type => r.child_type = idx(tree.nodeData(n).node),
            .error_union => r.child_type = idx(tree.nodeData(n).node_and_node[1]),
            .@"break", .@"continue" => r.label = if (tree.nodeData(n).opt_token_and_opt_node[0].unwrap()) |t| t else null,
            else => {},
        }
        var captures: std.ArrayList(Capture) = .empty;
        if (tree.fullIf(n)) |v| {
            try capture(&tree, &captures, v.payload_token, v.ast.then_expr);
            if (v.error_token) |t| if (v.ast.else_expr.unwrap()) |b| try capture(&tree, &captures, t, b);
        }
        if (tree.fullWhile(n)) |v| {
            try capture(&tree, &captures, v.payload_token, v.ast.then_expr);
            r.label = v.label_token;
            if (v.error_token) |t| if (v.ast.else_expr.unwrap()) |b| try capture(&tree, &captures, t, b);
        }
        if (tree.fullFor(n)) |v| {
            try capture(&tree, &captures, v.payload_token, v.ast.then_expr);
            r.label = v.label_token;
        }
        if (tree.fullSwitchCase(n)) |v| try capture(&tree, &captures, v.payload_token, v.ast.target_expr);
        switch (tag) {
            .@"catch" => if (tree.tokenTag(r.main + 1) == .pipe) {
                try capture(&tree, &captures, r.main + 2, tree.nodeData(n).node_and_node[1]);
            },
            .@"errdefer" => if (tree.tokenTag(r.main + 1) == .pipe) {
                try capture(&tree, &captures, r.main + 2, tree.nodeData(n).node);
            },
            else => {},
        }
        if (captures.items.len != 0) r.captures = captures.items;
        try nodes.append(gpa, r);
    }
    const output = try std.json.Stringify.valueAlloc(gpa, .{ .version = "0.17.1", .tokens = tokens.items, .nodes = nodes.items }, .{});
    var sent: usize = 0;
    while (sent < output.len) {
        const count = write(1, output.ptr + sent, output.len - sent);
        if (count <= 0) return error.WriteFailed;
        sent += @intCast(count);
    }
}
