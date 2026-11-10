"""Original Zig 0.17.1 tasks; one family contains every source variant."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'functions':'''fn add(a:u32,b:u32) u32 { return a+b; } test "@WORD@" { try std.testing.expectEqual(@as(u32,@N@+2),add(@N@,2)); }''',
'mutable':'''test "@WORD@" { var n:u32=@N@; n+=1; try std.testing.expectEqual(@as(u32,@N@+1),n); }''',
'constant':'''const limit:u32=@N@; test "@WORD@" { try std.testing.expect(limit>0); }''',
'struct':'''const Point=struct { x:i32,y:i32, fn total(self:@This()) i32 { return self.x+self.y; } }; test "@WORD@" { const p=Point{.x=@N@,.y=2}; try std.testing.expectEqual(@as(i32,@N@+2),p.total()); }''',
'method-pointer':'''const Counter=struct { value:u32=0, fn next(self:*@This()) u32 { self.value+=1; return self.value; } }; test "@WORD@" { var c:Counter=.{}; try std.testing.expectEqual(@as(u32,1),c.next()); }''',
'enum':'''const Status=enum{idle,ready}; test "@WORD@" { const status:Status=.ready; try std.testing.expectEqual(@as(u8,1),@as(u8,@backingInt(status))); }''',
'enum-explicit':'''const Code=enum(u8){one=1,other=@N@}; test "@WORD@" { const c:Code=@fromBackingInt(@as(u8,@N@)); try std.testing.expect(c==.other); }''',
'union':'''const Value=union(enum){number:u32,text:[]const u8}; fn read(v:Value) usize { return switch(v){.number=>|n|n,.text=>|s|s.len}; } test "@WORD@" { try std.testing.expectEqual(@as(usize,@N@),read(.{.number=@N@})); }''',
'packed':'''const Flags=packed struct { active:bool, count:u7 }; test "@WORD@" { const f=Flags{.active=true,.count=@N@}; try std.testing.expect(f.active); }''',
'extern-layout':'''const Pair=extern struct { left:u32,right:u32 }; test "@WORD@" { try std.testing.expectEqual(@as(usize,8),@sizeOf(Pair)); }''',
'opaque':'''const Handle=opaque{}; test "@WORD@" { try std.testing.expectEqual(@sizeOf(usize),@sizeOf(*Handle)); }''',
'error-set':'''const Failure=error{Missing,Busy}; fn load(n:u8) Failure!u8 { if(n==0)return error.Missing; return n; } test "@WORD@" { try std.testing.expectError(Failure.Missing,load(0)); }''',
'error-try':'''fn inc(n:u8) !u8 { if(n==0)return error.Empty; return n+1; } fn run() !u8 { return try inc(@N@); } test "@WORD@" { try std.testing.expectEqual(@as(u8,@N@+1),try run()); }''',
'error-catch':'''fn read(ok:bool) !u8 { if(!ok)return error.NotReady; return @N@; } test "@WORD@" { const n=read(false) catch |err| switch(err){error.NotReady=>0}; try std.testing.expectEqual(@as(u8,0),n); }''',
'error-capture':'''fn read() !u8 { return error.Missing; } test "@WORD@" { if(read()) |value| { _=value; return error.Unexpected; } else |err| { try std.testing.expect(err==error.Missing); } }''',
'optional':'''fn get(v:?u32) u32 { return v orelse @N@; } test "@WORD@" { try std.testing.expectEqual(@as(u32,@N@),get(null)); }''',
'optional-capture':'''fn get(v:?u32) u32 { if(v) |n| return n+1; return 0; } test "@WORD@" { try std.testing.expectEqual(@as(u32,@N@+1),get(@N@)); }''',
'while-capture':'''fn next(n:*u8) ?u8 { if(n.*==0)return null; n.*-=1; return n.*; } test "@WORD@" { var n:u8=@N@; var count:u32=0; while(next(&n)) |v| { count+=v; } try std.testing.expectEqual(@as(u8,0),n); try std.testing.expectEqual(@as(u32,@N@*(@N@-1)/2),count); }''',
'for-index':'''test "@WORD@" { const items=[_]u32{2,3,4}; var sum:u32=0; for(items,0..) |item,index| { sum+=item+@as(u32,@intCast(index)); } try std.testing.expectEqual(@as(u32,12),sum); }''',
'pointer-capture':'''test "@WORD@" { var values=[_]u8{1,2}; for(&values) |*v| v.*+=@N@; try std.testing.expectEqual(@as(u8,@N@+1),values[0]); }''',
'loop-label':'''test "@WORD@" { var result:u32=0; outer: for(0..10) |i| { if(i==3)break :outer; result+=@intCast(i); } try std.testing.expectEqual(@as(u32,3),result); }''',
'block-label':'''test "@WORD@" { const value=blk:{ const n:u32=@N@; break :blk n*2; }; try std.testing.expectEqual(@as(u32,@N@*2),value); }''',
'generic-type':'''fn Box(comptime T:type) type { return struct{value:T}; } test "@WORD@" { const value=Box(u32){.value=@N@}; try std.testing.expectEqual(@as(u32,@N@),value.value); }''',
'generic-count':'''fn fill(comptime N:usize) [N]u8 { return @splat(@N@); } test "@WORD@" { const a=fill(4); try std.testing.expectEqual(@as(u8,@N@),a[0]); }''',
'comptime':'''fn square(comptime n:u32) u32 { return n*n; } test "@WORD@" { const n=comptime square(@N@); try std.testing.expectEqual(@as(u32,@N@*@N@),n); }''',
'inline-for':'''test "@WORD@" { const types=.{u8,u16,u32}; inline for(types) |T| { const n:T=@N@; try std.testing.expect(n>0); } }''',
'cast':'''fn convert(n:u32) u8 { return @intCast(n); } test "@WORD@" { try std.testing.expectEqual(@as(u8,@N@),convert(@N@)); }''',
'bitcast':'''test "@WORD@" { const bits:u32=@bitCast(@as(f32,1.0)); try std.testing.expectEqual(@as(u32,0x3f800000),bits); }''',
'reflection':'''const Item=struct{value:u32}; test "@WORD@" { const info=@typeInfo(Item); try std.testing.expectEqual(@as(usize,1),info.@"struct".field_names.len); try std.testing.expect(@hasField(Item,"value")); }''',
'array':'''test "@WORD@" { const items=[_]u8{1,2,3,@N@}; const view=items[1..3]; try std.testing.expectEqual(@as(usize,2),view.len); }''',
'sentinel':'''test "@WORD@" { const text:[:0]const u8="@WORD@"; try std.testing.expect(text.len>0); try std.testing.expectEqual(@as(u8,0),text[text.len]); }''',
'pointer':'''fn inc(n:*u32) void { n.*+=1; } test "@WORD@" { var n:u32=@N@; inc(&n); try std.testing.expectEqual(@as(u32,@N@+1),n); }''',
'array-list':'''test "@WORD@" { const gpa=std.testing.allocator; var list:std.ArrayList(u32)=.empty; defer list.deinit(gpa); try list.append(gpa,@N@); try std.testing.expectEqual(@as(u32,@N@),list.items[0]); }''',
'hash-map':'''test "@WORD@" { const gpa=std.testing.allocator; var map:std.AutoHashMapUnmanaged(u8,u32)=.empty; defer map.deinit(gpa); try map.put(gpa,1,@N@); try std.testing.expectEqual(@as(u32,@N@),map.get(1).?); }''',
'dupe-sentinel':'''test "@WORD@" { const gpa=std.testing.allocator; const text=try gpa.dupeSentinel(u8,"@WORD@",0); defer gpa.free(text); try std.testing.expectEqualStrings("@WORD@",text); }''',
'json':'''test "@WORD@" { const gpa=std.testing.allocator; const text=try std.json.Stringify.valueAlloc(gpa,.{.value=@as(u32,@N@)},.{}); defer gpa.free(text); try std.testing.expect(text.len>0); }''',
'callconv':'''fn echo(n:u32) callconv(.c) u32 { return n; } test "@WORD@" { try std.testing.expectEqual(@as(u32,@N@),echo(@N@)); }''',
'quoted-ident':'''fn @"return value"(n:u32) u32 { return n; } test "@WORD@" { try std.testing.expectEqual(@as(u32,@N@),@"return value"(@N@)); }''',
'multiline':'''const text=
\\\\first "quoted" @WORD@
\\\\second 🌌
; test "@WORD@" { try std.testing.expect(std.mem.indexOf(u8,text,"first")!=null); }''',
'literals':'''test "@WORD@" { const char='星'; const text="🌌 \\n"; const number:u32=0xff; try std.testing.expect(char>0); try std.testing.expect(text.len>0); try std.testing.expectEqual(@as(u32,255),number); }''',
'comments':'''//! Current 0.17.1 container documentation.
/// Increment a value.
fn inc(n:u32) u32 { // 星空 🌌
 return n+1; }
test "@WORD@" { try std.testing.expectEqual(@as(u32,@N@+1),inc(@N@)); }''',
'error-defer':'''fn fail(ok:bool) !void { errdefer std.debug.print("",.{}); if(!ok)return error.Failure; } test "@WORD@" { try std.testing.expectError(error.Failure,fail(false)); }''',
}
WORDS='aurora bridge cosmos delta ember forest galaxy harbor island juniper kernel lumen meteor nova orbit prism quasar river solar tundra'.split()
def source_for(template,index):
 source=template.replace('@N@',str(3+index%20)).replace('@WORD@',WORDS[index%len(WORDS)])+'\n'
 prefix='const std=@import("std");\n'
 if source.startswith('//!'):
  first,source=source.split('\n',1);prefix=first+'\n'+prefix
 return prefix+source
def main():
 root=PackSpec.open('zig').dataset_root/'sources/curriculum-0.17.1-v1';files={}
 for family,template in TEMPLATES.items():
  for variant in range(24):
   source=source_for(template,variant)
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{variant:02}.zig';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve earlier Zig curriculum')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 p=root/'LICENSE'
 if not p.exists():p.write_text('Original Zig 0.17.1 syntax tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream/Golden/Playground copies.\n')
 lock=dict(format='nsh-zig-0.17.1-curriculum-v1',generatorSha256=file_hash(Path(__file__)),files=files);p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve earlier curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'current Zig tasks in',len(TEMPLATES),'families')
if __name__=='__main__':main()
