"""Independent Ruby namespace/call/literal tasks; preserve the initial curriculum."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'qualified-module':'module @TYPE@::Formatting\n  def self.@FN@(value)\n    "@WORD@ #{value}"\n  end\nend\nresult = @TYPE@::Formatting.@FN@(3)',
'qualified-chain':'def @FN@(value)\n  @TYPE@::Internal::Processor.new(value).call\nend',
'local-construction':'class @TYPE@\n  def initialize(value)\n    @value = value\n  end\n  def call = @value.to_s\nend\nrecord = @TYPE@.new(@N@)\nputs record.call',
'constant-reference':'module @TYPE@\n  DEFAULTS = {limit: @N@, label: "@WORD@"}\n  def self.config = DEFAULTS\nend\ndef @FN@ = @TYPE@::DEFAULTS.fetch(:limit)',
'class-call':'module @TYPE@\n  class Runner\n    def self.build(value) = new(value)\n    def initialize(value)\n      @value = value\n    end\n    def execute = @value + @N@\n  end\nend\nresult = @TYPE@::Runner.build(2).execute',
'heredoc-mixed':'module @TYPE@\n  def self.@FN@(value, count)\n    prefix = "@WORD@"\n    text = <<~BODY\n      #{prefix}: #{value}\n      { "amount": #{count + @N@} }\n      C:\\records\\raw\n    BODY\n    [prefix, text.strip].join("\\n")\n  end\nend',
'quoted-mixed':"module @TYPE@\n  def self.@FN@(value)\n    raw = <<'PAYLOAD'\n@WORD@ #{literal_not_code}\n# text C:\\records\\raw\nPAYLOAD\n    [raw, value.to_s].join(\"/\")\n  end\nend",
'pattern-mixed':'module @TYPE@\n  def self.@FN@(payload)\n    case payload\n    in {label:, amount: Integer => number} if number > @N@\n      "@WORD@ #{label}: #{number}"\n    in [head, *tail]\n      "#{head} / #{tail.size}"\n    else\n      "empty"\n    end\n  end\nend',
'string-join':'def @FN@(name, count)\n  part = "@WORD@ #{name.upcase}"\n  detail = %Q{<record>#{count + @N@}</record>}\n  [part, detail, name].join(" / ")\nend',
'string-neighbors':'module @TYPE@\n  def self.@FN@(value)\n    title = "@WORD@"\n    line = "#{title}: #{value}"\n    raw = %q{literal #{text} // # and "quotes"}\n    words = %W[@WORD@ #{value} source]\n    [line, raw, words.join(", ")].join("\\n")\n  end\nend',
'regex-mixed':'module @TYPE@\n  def self.@FN@(suffix)\n    escaped = Regexp.escape(suffix)\n    pattern = %r{\\A@WORD@/#{escaped}/[0-9]{1,@N@}\\z}i\n    [pattern.source, suffix.to_s]\n  end\nend',
'defaults-blocks':'module @TYPE@\n  def self.@FN@(values, offset: @N@)\n    values.filter_map do |value|\n      next if value.nil?\n      label = "@WORD@ #{value}"\n      [label, value + offset]\n    end\n  end\nend',
}
WORDS='acorn breeze creek dahlia echo fir glen heath jade kelp lilac moor nectar ocean plum quartz ridge spruce tulip willow'.split()
def main():
 root=PackSpec.open('ruby').dataset_root/'sources/mixed-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   word=WORDS[(index+variant)%len(WORDS)];rng=random.Random(9153+index*101+variant);source=template.replace('@FN@',word+'_render').replace('@TYPE@',word.title()+'Toolkit').replace('@WORD@',word).replace('@N@',str(rng.randrange(2,30)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{variant:02}.rb';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve previous Ruby mixed task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original Ruby mixed tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original Ruby mixed license')
 p.write_bytes(license);lock=dict(format='nsh-ruby-mixed-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve previous Ruby mixed curriculum')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'tasks in',len(TEMPLATES),'families')
if __name__=='__main__':main()
