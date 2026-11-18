"""Original protobuf structure families; no source/Golden/display copying."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'basic':'syntax = "proto3";\npackage @w@.v1;\nmessage @T@ { string name=1; int64 id=2; bool active=3; }',
'scalar':'syntax="proto3"; message @T@ { double ratio=1; float size=2; int32 count=3; uint64 total=4; bytes body=5; }',
'integer':'message @T@ { sint32 delta=1; sint64 offset=2; fixed32 mask=3; fixed64 bits=4; sfixed32 low=5; sfixed64 high=6; }',
'optional':'syntax="proto3";\nmessage @T@ { optional string nickname=1; optional int32 count=2; repeated string tags=3; }',
'repeated':'syntax="proto3"; message @T@ { repeated Item@T@ entries=1; repeated int64 values=2 [packed=true]; } message Item@T@ { string title=1; }',
'nested':'message @T@ { message Detail { string caption=1; } Detail info=1; repeated Detail history=2; }',
'map':'message @T@ { map<string, int64> counts=1; map<uint32, Item@T@> entries=2; map<bool, string> flags=3; }',
'oneof':'message @T@ { oneof result { string text=1; bytes raw=2; Failure@T@ error=3; } }',
'enum':'enum @T@Status { @U@_UNKNOWN=0; @U@_ACTIVE=1; @U@_DONE=2; } message @T@ { @T@Status status=1; }',
'negative-enum':'enum @T@Code { option allow_alias=true; @U@_NONE=0; @U@_ERROR=-1; @U@_ALIAS=-1; }',
'enum-options':'enum @T@Mode { @U@_DEFAULT=0; @U@_LEGACY=1 [deprecated=true]; @U@_STABLE=2; }',
'service':'service @T@Service { rpc Read(Read@T@Request) returns (Read@T@Response); rpc Delete(Delete@T@Request) returns (Empty); }',
'stream-server':'service @T@Feed { rpc Watch(Watch@T@Request) returns (stream @T@Event); } message @T@Event { string topic=1; }',
'stream-client':'service @T@Upload { rpc Write(stream @T@Chunk) returns (@T@Summary); } message @T@Chunk { bytes data=1; }',
'stream-bidi':'service @T@Session { rpc Exchange(stream @T@Frame) returns (stream @T@Frame); } message @T@Frame { int64 seq=1; string body=2; }',
'rpc-options':'service @T@API { rpc Find(@T@Request) returns (@T@Response) { option deprecated=true; option (http.rule)={ get:"/v1/@w@/{id}" }; } }',
'imports':'syntax="proto3"; import "google/protobuf/timestamp.proto"; import public "@w@/types.proto"; message @T@ { google.protobuf.Timestamp created=1; }',
'qualified':'package @w@.v2; message @T@ { .shared.v1.Identifier id=1; @w@.v1.Record record=2; }',
'options':'syntax="proto3"; option java_package="com.example.@w@"; option go_package="example.test/@w@;@w@pb"; option java_multiple_files=true;',
'custom-option':'message @T@ { string label=1 [(validate.rules).string={ min_len:@n@ max_len:128 }]; int64 id=2 [(validate.rules).int64.gt=0]; }',
'aggregate':'option (@w@.config)={ name:"@w@" enabled:true scale:-1.25e2 mode:STRICT count:@n@ }; message @T@ { string key=1; }',
'aggregate-list':'option (@w@.schema)={ tags:["one","two"] ranks:[1,2,3] mappings:{ key:"@w@" value:"text" } };',
'aggregate-any':'option (@w@.policy)={ [type.googleapis.com/shared.Policy]: { enabled:true } }; message @T@ {}',
'reserved-numbers':'message @T@ { reserved 2, 4 to 7, 20 to max; string name=1; reserved "old_name", "legacy_id"; }',
'editions':'edition="2023"; package @w@.v1; option features.field_presence=EXPLICIT; message @T@ { string name=1; int64 count=2; }',
'editions-2024':'edition="2024"; import option "@w@/options.proto"; export message @T@ { string title=1; } local enum @T@Mode { @U@_UNKNOWN=0; }',
'editions-2026':'edition="2026"; package @w@.v1; message @T@ { reserved obsolete, legacy; string value=1; }',
'proto2-default':'syntax="proto2"; message @T@ { required int64 id=1; optional string name=2 [default="@w@"]; optional double ratio=3 [default=-2.5]; }',
'extensions':'syntax="proto2"; message @T@ { extensions 100 to 199; optional string name=1; } extend @T@ { optional int32 @w@_count=100; }',
'group':'syntax="proto2"; message @T@ { optional group Detail=1 { required string name=2; } }',
'comments':'// @T@ original 🌌\nmessage @T@ {\n /* Keep original field notes. */\n string name=1; // inline @w@\n}',
'concatenated':'option (@w@.note)="Original @w@ text" /* keep note */ " plus a second literal"; message @T@ {}',
'escapes':'option (@w@.text)="A \\"quote\\" \\n \\t \\u661f \\U0001F30C"; message @T@ { string path=1; }',
'unicode':'// @w@ 星空 👩🏽‍💻\noption (@w@.title)="星空 🌌 café"; message @T@ { string title=1; }',
'long-comment':'/*\n'+('Original @w@ context with 🌌, {braces}, option and message words.\n'*24)+'*/\nmessage @T@ { string tail=1; }',
'long-line-comment':'// @w@ '+('Original schema comment 🌌 with fields and punctuation. '*23)+'\nmessage @T@ { bool done=1; }',
'long-string':'option (@w@.description)="'+('Original @w@ text with spaces 🌌 and # marks. '*24)+'";\nmessage @T@ { int64 tail=1; }',
'field-options':'message @T@ { repeated string values=1 [deprecated=true, json_name="@w@Values"]; bytes data=2 [(validate.rules).bytes.min_len=@n@]; }',
'radices':'option (@w@.numbers)={ mask:0xFF perms:0755 value:+@n@ fraction:.25 scale:1e-3 }; message @T@ {}',
'bom':'\ufeffsyntax="proto3";\npackage @w@.v1; message @T@ { string value=1; }',
'dense':'syntax="proto3";message @T@{string name=1;int32 count=2;repeated string labels=3;}',
'large-message':'syntax="proto3";\nmessage @T@ {\n'+''.join(' string section_'+str(i)+'='+str(i)+';\n'for i in range(1,40))+'}',
}
WORDS='acacia birch cedar dogwood elm fir ginkgo hazel iris juniper kelp larch maple nettle oak pine quince reed sage thyme'.split()
def main():
 root=PackSpec.open('protobuf').dataset_root/'sources/curriculum-v1';files={}
 for i,(family,template)in enumerate(TEMPLATES.items()):
  for v in range(20):
   w=WORDS[(i+v)%len(WORDS)];s=template.replace('@T@',w.title()).replace('@w@',w).replace('@U@',w.upper()).replace('@n@',str(3+v))+'\n'
   if v%4==1:s=s.replace('\n','\r\n')
   raw=s.encode();p=root/family/f'{v:02}.proto';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve original curriculum')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original protobuf tasks authored for Neural Semantic Highlighting.\nPrivate dataset; no upstream, Golden or visible display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve curriculum license')
 p.write_bytes(license);lock=dict(format='nsh-protobuf-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original protobuf tasks')
if __name__=='__main__':main()
