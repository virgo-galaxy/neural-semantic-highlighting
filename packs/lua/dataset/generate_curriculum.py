"""Original Lua 5.x task families, separate from Golden and displayed source."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'function':'local function @FN@(value, extra)\n  return value + extra + @N@\nend',
'global-function':'function @FN@(value)\n  return value + @N@\nend',
'function-value':'local @FN@ = function(value)\n  return value * @N@\nend\nprint(@FN@(2))',
'varargs':'local function @FN@(...)\n  local values = {...}\n  return table.concat(values, "@WORD@")\nend',
'named-varargs':'local function @FN@(...values)\n  return values[1], ...\nend',
'closure':'local function @FN@(step)\n  local total = @N@\n  return function(value)\n    total = total + value + step\n    return total\n  end\nend',
'recursive':'local function @FN@(value)\n  if value <= 1 then return 1 end\n  return value * @FN@(value - 1)\nend',
'local-shadow':'local function @FN@(value)\n  do\n    local value = value + @N@\n    print(value)\n  end\n  return value\nend',
'module':'local M = {}\nfunction M.@FN@(value)\n  return "@WORD@ " .. tostring(value)\nend\nreturn M',
'method':'local @FN@ = {count = @N@}\nfunction @FN@:add(amount)\n  self.count = self.count + amount\n  return self.count\nend\n@FN@:add(2)',
'metatable':'local @FN@ = {}\n@FN@.__index = @FN@\nfunction @FN@.new(title)\n  return setmetatable({title = title, count = @N@}, @FN@)\nend',
'callable-table':'local @FN@ = setmetatable({}, {__call = function(self, value) return value + @N@ end})\nprint(@FN@(3))',
'table':'local @FN@ = {title = "@WORD@", views = @N@, enabled = true}\nprint(@FN@.title, @FN@["views"])',
'nested-table':'local @FN@ = {header = {title = "@WORD@"}, items = {1, 2, @N@}}\nreturn @FN@.header.title',
'computed-key':'local key = "@WORD@"\nlocal @FN@ = {[key] = @N@, [1] = "one"}\nreturn @FN@[key]',
'field-function':'local @FN@ = {run = function(value) return value + @N@ end, label = "@WORD@"}\nreturn @FN@.run(1)',
'array':'local @FN@ = {"@WORD@", "source", "code"}\ntable.insert(@FN@, "last")\nreturn table.concat(@FN@, ", ")',
'multiple-assignment':'local first, second = @N@, "@WORD@"\nfirst, second = second, first\nlocal @FN@ = {first, second}',
'generic-loop':'local function @FN@(records)\n  local total = 0\n  for key, value in pairs(records) do\n    total = total + value + @N@\n  end\n  return total\nend',
'array-loop':'local function @FN@(records)\n  local labels = {}\n  for index, record in ipairs(records) do\n    labels[index] = "@WORD@ " .. record.title\n  end\n  return labels\nend',
'numeric-loop':'local function @FN@(limit)\n  local sum = 0\n  for index = 1, limit, 2 do sum = sum + index + @N@ end\n  return sum\nend',
'loop-shadow':'local function @FN@(index)\n  for index = index, @N@ do print(index) end\n  return index\nend',
'while':'local function @FN@(limit)\n  local value = @N@\n  while value < limit do value = value + 1 end\n  return value\nend',
'repeat':'local function @FN@(limit)\n  local count = @N@\n  repeat\n    local done = count >= limit\n    count = count + 1\n  until done\n  return count\nend',
'condition':'local function @FN@(value)\n  if value > @N@ then return "@WORD@" elseif value == 0 then return "zero" else return "other" end\nend',
'boolean':'local function @FN@(value)\n  return value and value.title or "@WORD@"\nend',
'break':'local function @FN@(values)\n  for index, value in ipairs(values) do\n    if value > @N@ then break end\n    print(index, value)\n  end\nend',
'labels':'local function @FN@(values)\n  for _, value in ipairs(values) do\n    if value < @N@ then goto skip end\n    print(value)\n    ::skip::\n  end\nend',
'constant':'local @FN@ <const> = @N@\nlocal value = @FN@ + 1\nreturn value',
'close':'local function @FN@(path)\n  local file <close> = assert(io.open(path, "r"))\n  return file:read("@WORD@")\nend',
'globals':'global print, tostring\nglobal @FN@ = @N@\nprint(tostring(@FN@))',
'global-const':'global<const> @FN@ = @N@\nlocal value = @FN@ + 1\nreturn value',
'global-none':'global none\nglobal print\nglobal function @FN@(value)\n  print(value)\n  return value + @N@\nend',
'global-wildcard':'global<const> *\nlocal function @FN@(value) return tostring(value) .. "@WORD@" end',
'global-keyword-name':'local global, none = @N@, "@WORD@"\nlocal function @FN@() return global, none end',
'coroutine':'local function @FN@(values)\n  return coroutine.create(function()\n    for _, value in ipairs(values) do coroutine.yield(value + @N@) end\n  end)\nend',
'pcall':'local function @FN@(callback, value)\n  local ok, result = pcall(callback, value)\n  if not ok then return nil, tostring(result) end\n  return result, @N@\nend',
'xpcall':'local function @FN@(callback)\n  return xpcall(callback, function(problem) return "@WORD@ " .. tostring(problem) end)\nend',
'require':'local utils = require("@WORD@.utils")\nlocal function @FN@(value) return utils.transform(value, @N@) end\nreturn @FN@',
'neovim':'local M = {}\nfunction M.@FN@(buffer)\n  local lines = vim.api.nvim_buf_get_lines(buffer, 0, -1, false)\n  vim.notify("@WORD@ " .. #lines)\n  return lines\nend\nreturn M',
'callback':'local function @FN@(callback, values)\n  local output = {}\n  for i, value in ipairs(values) do output[i] = callback(value + @N@) end\n  return output\nend',
'event-handler':'local @FN@ = {on_change = function(event) return event.value .. "@WORD@" end}\nreturn @FN@',
'string':'local @FN@ = "@WORD@ # text \\"quoted\\"\\nC:\\\\records\\\\raw"',
'long-string':'local @FN@ = [[\n@WORD@ # text ${not_code}\nC:\\records\\raw\n]]',
'delimited-long':'local @FN@ = [==[\n@WORD@ [[nested-looking]] ]=] text\n-- literal comment\n]==]',
'patterns':'local function @FN@(text)\n  return text:match("^@WORD@%d+$"), text:gsub("%s+", "_")\nend',
'format':'local function @FN@(title, count)\n  return string.format("@WORD@ %s: %d 🌌", title, count + @N@)\nend',
'comments':'-- @WORD@ 🌌 report\nlocal function @FN@(value)\n  return value + @N@ -- result\nend',
'long-comment':'--[==[\n@WORD@ comment with [[markers]]\nlocal fake = "code"\n]==]\nlocal @FN@ = @N@',
'numbers':'local @FN@ = {1, @N@, 0xff, 1.25e-3, 0x1.fp2}\nreturn @FN@',
'operators':'local function @FN@(value)\n  return (value << 1) ~ (value & @N@), value // 2, value % 3, #tostring(value)\nend',
'long-mixed':'local function @FN@(title)\n  local header = "@WORD@ " .. title\n  local text = [=[\n{ "kind": "@WORD@", "value": "literal" }\n-- not a comment\nC:\\workspace\\records\n]=]\n  return header .. "\\n" .. text\nend',
}
WORDS='aspen bay clover dew elm fern grove heath island juniper key lotus mist north olive pine quartz reed silver thyme'.split()
def main():
 root=PackSpec.open('lua').dataset_root/'sources/curriculum-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   word=WORDS[(index+variant)%len(WORDS)];rng=random.Random(5505+index*101+variant);source=template.replace('@FN@',word+'_process').replace('@WORD@',word).replace('@N@',str(rng.randrange(2,30)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{variant:02}.lua';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve previous Lua task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original Lua tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original Lua license')
 p.write_bytes(license);lock=dict(format='nsh-lua-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve previous Lua curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'tasks in',len(TEMPLATES),'families')
if __name__=='__main__':main()
