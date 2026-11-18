"""Original GraphQL families; no Golden, display or held-out source copies."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'lookup':'query Locate@T@($key: ID!) { @w@(id: $key) { id name createdAt } }',
'pagination':'query Browse@T@($limit: Int = @n@, $cursor: String) { @w@(first: $limit, after: $cursor) { edges { cursor node { id title } } pageInfo { hasNextPage endCursor } } }',
'mutation':'mutation Add@T@($input: New@T@Input!) { create@T@(input: $input) { record { id name } errors { message code } } }',
'subscription':'subscription Observe@T@($topic: String!) { @w@Changed(topic: $topic) { id action timestamp } }',
'alias':'query Pair@T@ { primary: @w@(id: "main") { id label } secondary: @w@(id: "backup") { id label } }',
'fragments':'fragment @T@Fields on @T@ { id name description }\nquery Read@T@ { @w@ { ...@T@Fields } }',
'inline':'query Explore@T@ { @w@ { __typename ... on @T@ { id name } ... on Other@T@ { code } } }',
'conditional':'query Optional@T@($show: Boolean!, $hide: Boolean = false) { @w@ { id title @include(if: $show) secret @skip(if: $hide) } }',
'objects':'query Match@T@ { @w@(filter: {name: "@w@", active: true, status: READY, count: @n@, after: null}) { id } }',
'lists':'query Pick@T@($ids: [ID!]!) { @w@(ids: $ids, tags: ["blue", "green"], weights: [1, -@n@, 2.5e-3]) { name } }',
'block':'query Text@T@ { @w@(text: """\nA @w@ description with # marks and {braces}.\nA second line.\n""") { id } }',
'escape':'query Escaped@T@ { @w@(text: "@w@ \\"quoted\\" \\n \\u{1F30C}") { id } }',
'comment':'# @T@ operation 🌌\nquery Comment@T@ {\n # Fetch the original fields\n @w@ { id name } # End note\n}',
'sdl-object':'type @T@ { id: ID! name: String! count: Int ratio: Float enabled: Boolean items: [@T@!]! }',
'sdl-interface':'interface @T@Node { id: ID! }\ntype @T@ implements @T@Node { id: ID! title: String }',
'sdl-input':'input @T@Filter { query: String count: Int = @n@ active: Boolean = true tags: [String!] state: @T@State = OPEN }\nenum @T@State { OPEN CLOSED }',
'sdl-args':'type @T@Query { @w@(id: ID!, limit: Int = @n@, filter: @T@Filter): [@T@!]! }',
'sdl-union':'union @T@Result = @T@ | Other@T@\ntype @T@ { id: ID! }\ntype Other@T@ { title: String }',
'sdl-enum':'"Available @w@ states"\nenum @T@State { UNKNOWN ACTIVE @deprecated(reason: "Use READY") READY }',
'sdl-scalar':'"""A custom @w@ value.\nOriginal description."""\nscalar @T@Time @specifiedBy(url: "https://example.test/@w@")',
'sdl-schema':'schema { query: @T@Query mutation: @T@Mutation subscription: @T@Subscription }\ntype @T@Query { @w@: String }',
'sdl-directive':'directive @@w@(reason: String!, level: Int = @n@) repeatable on FIELD | OBJECT | FIELD_DEFINITION\ntype @T@ @@w@(reason: "policy") { id: ID! }',
'sdl-oneof':'input @T@Choice @oneOf { id: ID name: String }\ntype @T@ { lookup(choice: @T@Choice): String }',
'sdl-extend':'extend type @T@ { extra: String count: Int }\nextend input @T@Input { active: Boolean }\nextend enum @T@State { PENDING }',
'sdl-federation':'extend schema @link(url: "https://specs.apollo.dev/federation/v2.3", import: ["@key"])\ntype @T@ @key(fields: "id") { id: ID! name: String }',
'descriptions':'"""The @w@ schema."""\ntype @T@ {\n "The identifier"\n id: ID!\n """A multiline\n field description."""\n name: String\n}',
'keyword-fields':'query Spelling@T@ { @w@ { query type mutation true null enum scalar input } }',
'fragment-directive':'fragment Extra@T@ on @T@ { id name }\nquery Details@T@($ok: Boolean!) { @w@ { ...Extra@T@ @include(if: $ok) ... @skip(if: false) { timestamp } } }',
'deep':'query Nested@T@ { @w@ { owner { profile { contacts { primary { email } } } } labels { name color } } }',
'values-compact':'{ @w@(a:@n@,b:-3.25,c:true,d:null,e:MODE,f:{x:1,y:["one","two"]}) { id } }',
'extensions':'extend interface @T@Node { name: String }\nextend union @T@Result = Other@T@\nextend scalar @T@Time @specifiedBy(url: "https://example.test")',
'unicode':'# @w@ 星空 👩🏽‍💻\nquery Unicode@T@ { @w@(q: "星空 🌌 café", filter: {text: "\\u661f"}) { id title } }',
'numeric-defaults':'query Range@T@($min: Float = -@n@.25, $max: Float = 1e3) { @w@(min: $min, max: $max) { count } }',
'fragments-nested':'fragment Small@T@ on @T@ { id }\nfragment Full@T@ on @T@ { ...Small@T@ owner { name } }\n{ @w@ { ...Full@T@ } }',
'array-defaults':'query Batch@T@($ids: [ID!] = ["first", "second"], $filter: @T@Filter = {enabled: true}) { @w@(ids: $ids, filter: $filter) { id } }',
'long-description':'"""\n'+('The @w@ description retains # signs, $values, {braces}, and Unicode 🌌.\n'*16)+'"""\ntype @T@ { id: ID! }',
'long-selection':'query Long@T@ { @w@ {\n'+''.join(' section'+str(i)+' { id name description }\n'for i in range(28))+'} }',
'long-comment': '# @w@ '+('Original comment 🌌 with punctuation { } $ and spaces. '*24)+'\nquery LongNote@T@ { @w@ { id } }',
'bom':'\ufeffquery Bom@T@ { @w@(limit: @n@) { id name } }',
'multi-op':'query First@T@ { @w@ { id } }\nmutation Second@T@ { update@T@(name: "@w@") { ok } }',
}
WORDS='alder birch cedar dahlia elm fir ginkgo hazel iris juniper kelp larch maple nettle oak pine quince reed sage thyme'.split()
def main():
 root=PackSpec.open('graphql').dataset_root/'sources/curriculum-v1';files={}
 for index,(family,template)in enumerate(TEMPLATES.items()):
  for variant in range(20):
   word=WORDS[(index+variant)%len(WORDS)];source=template.replace('@T@',word.title()).replace('@w@',word).replace('@n@',str(3+variant))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{variant:02}.graphql';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists()and p.read_bytes()!=raw:raise ValueError('Preserve original curriculum')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original GraphQL tasks authored for Neural Semantic Highlighting.\nPrivate dataset; no upstream, Golden or visible display copies.\n';p=root/'LICENSE'
 if p.exists()and p.read_bytes()!=license:raise ValueError('Preserve curriculum license')
 p.write_bytes(license);lock=dict(format='nsh-graphql-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists()and json.loads(p.read_text())!=lock:raise ValueError('Preserve curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'original GraphQL tasks')
if __name__=='__main__':main()
