"""Original Ruby task families, never Golden/display copies."""
from pathlib import Path
import hashlib,json,random
from training.shared.spec import PackSpec,file_hash
TEMPLATES={
'function':'def @FN@(value, extra = @N@)\n  value + extra\nend',
'endless':'def @FN@(value) = value + @N@',
'keyword-params':'def @FN@(title:, enabled: true)\n  enabled ? title : "@WORD@"\nend',
'variadic':'def @FN@(*values, **options, &callback)\n  callback.call(values.sum + @N@, options)\nend',
'forwarding':'def @FN@(...)\n  target(...)\nend',
'locals':'def @FN@(values)\n  total = @N@\n  values.each { |value| total += value }\n  total\nend',
'class':'class @TYPE@\n  def initialize(title)\n    @title = title\n  end\n  def label = "@WORD@ #{@title}"\nend',
'attr':'class @TYPE@\n  attr_reader :title\n  attr_accessor :count\n  def initialize(title, count = @N@)\n    @title, @count = title, count\n  end\nend',
'constant':'module @TYPE@\n  LIMIT = @N@\n  LABEL = "@WORD@"\nend',
'module':'module @TYPE@\n  def @FN@(value)\n    value.to_s + "@WORD@"\n  end\nend',
'inheritance':'class @TYPE@ < BaseRecord\n  include Comparable\n  def <=>(other)\n    @count <=> other.count\n  end\nend',
'singleton':'class @TYPE@\n  def self.create(title:)\n    new(title)\n  end\nend',
'singleton-class':'class @TYPE@\n  class << self\n    def limit = @N@\n  end\nend',
'visibility':'class @TYPE@\n  def public_value = hidden + @N@\n  private\n  def hidden = @N@\nend',
'block':'def @FN@(values)\n  values.map { |number| number + @N@ }.select { |number| number.positive? }\nend',
'do-block':'def @FN@(values)\n  values.each_with_index do |item, index|\n    puts "@WORD@ #{index}: #{item}"\n  end\nend',
'block-locals':'def @FN@(values)\n  values.map { |value; scratch| scratch = value + @N@; scratch * 2 }\nend',
'numbered':'def @FN@(values)\n  values.map { _1 + @N@ }\nend',
'implicit-it':'def @FN@(values)\n  values.map { it.to_s + "@WORD@" }\nend',
'lambda':'@FN@ = ->(value, extra = @N@) { value + extra }\n@FN@.call(1)',
'proc':'@FN@ = proc { |value| value * @N@ }\n@FN@.call(3)',
'closure':'def @FN@(start)\n  count = start\n  ->(step) { count += step + @N@ }\nend',
'array':'def @FN@(values)\n  [@N@, *values, nil].compact.uniq.sort\nend',
'hash':'@FN@ = { title: "@WORD@", count: @N@, active: true }\n@FN@.fetch(:title)',
'keyword-call':'def @FN@(value)\n  render(json: value, status: @N@, layout: false)\nend',
'safe-navigation':'def @FN@(record)\n  record&.title&.strip || "@WORD@"\nend',
'range':'def @FN@(limit)\n  (0...limit).select { |n| n % @N@ == 0 }\nend',
'for':'def @FN@(values)\n  total = 0\n  for value in values\n    next if value < @N@\n    total += value\n  end\n  total\nend',
'while':'def @FN@(limit)\n  n = @N@\n  n += 1 while n < limit\n  n\nend',
'unless':'def @FN@(value)\n  return "@WORD@" unless value\n  value.to_s\nend',
'case':'def @FN@(code)\n  case code\n  when 0 then :idle\n  when 1..@N@ then :active\n  else :unknown\n  end\nend',
'pattern-array':'def @FN@(value)\n  case value\n  in [first, *rest]\n    first + rest.sum + @N@\n  else\n    0\n  end\nend',
'pattern-hash':'def @FN@(value)\n  case value\n  in {title:, count: number} if number > @N@\n    "@WORD@ #{title}: #{number}"\n  else\n    "none"\n  end\nend',
'right-assignment':'def @FN@(value)\n  value => {title:, count:}\n  "@WORD@ #{title}: #{count + @N@}"\nend',
'pattern-pinned':'def @FN@(values, expected)\n  case values\n  in [^expected, item]\n    item + @N@\n  else\n    nil\n  end\nend',
'rescue':'def @FN@(text)\n  Integer(text)\nrescue ArgumentError => problem\n  warn problem.message\n  @N@\nensure\n  puts "@WORD@"\nend',
'begin':'def @FN@(path)\n  begin\n    File.read(path)\n  rescue IOError => problem\n    "@WORD@ #{problem.message}"\n  end\nend',
'file-block':'def @FN@(path)\n  File.open(path, "w") do |file|\n    file.write("@WORD@\\n")\n  end\nend',
'rails':'class @TYPE@ < ApplicationRecord\n  belongs_to :owner\n  validates :title, presence: true\n  scope :recent, -> { order(created_at: :desc).limit(@N@) }\nend',
'rack':'class @TYPE@\n  def call(env)\n    [200, {"content-type" => "text/plain"}, ["@WORD@ #{env["PATH_INFO"]}"]]\n  end\nend',
'rake':'namespace :@WORD@ do\n  desc "@WORD@ task"\n  task :build do\n    puts "count #{@N@}"\n  end\nend',
'gemfile':'source "https://rubygems.org"\ngem "example-@WORD@", "~> @N@.0"\ngroup :test do\n  gem "rspec"\nend',
'interpolation':'def @FN@(name, count)\n  "@WORD@ #{name}: #{count + @N@}"\nend',
'percent-literal':'@FN@ = %q{C:\\@WORD@\\records # literal #{name}}',
'percent-interpolation':'def @FN@(value)\n  %Q{<@WORD@>#{value.upcase}</@WORD@>}\nend',
'word-array':'def @FN@(name)\n  %W[@WORD@ #{name} source]\nend',
'symbols':'@FN@ = %i[@WORD@ ready done]\nresult = {kind: :@WORD@, count: @N@}',
'regex':'def @FN@(value)\n  value.match?(/\\A[a-z]+\\d{1,@N@}\\z/i)\nend',
'regex-interpolation':'def @FN@(suffix)\n  %r{\\A@WORD@/#{Regexp.escape(suffix)}\\z}i\nend',
'heredoc':'def @FN@(name)\n  text = <<~MESSAGE\n    @WORD@ #{name}\n    Count #{@N@ + 1}\n  MESSAGE\n  text.strip\nend',
'heredoc-quoted':"@FN@ = <<'TEXT'\n@WORD@ # raw #{not_code}\nC:\\records\\raw\nTEXT",
'heredoc-indent':'def @FN@(value)\n  text = <<-DETAIL\n  @WORD@ #{value} # text\n  DETAIL\n  text\nend',
'heredoc-call':'def @FN@(path, value)\n  File.write(path, <<~CONTENT)\n    @WORD@ #{value}\n    { "count": @N@ }\n  CONTENT\nend',
'multi-heredoc':'@FN@ = [<<~FIRST, <<~SECOND]\n@WORD@ one\nFIRST\n@WORD@ two\nSECOND',
'comments':'# @WORD@ 🌌 report\ndef @FN@(value)\n  value + @N@ # result\nend',
'numbers':'@FN@ = [@N@, 0xff, 0b1010, 1_000, 1.5e-3, 2r, 3i]',
}
WORDS='aster brook cloud dune elm frost grass hill iris jet kiwi leaf mint nova oak pool quiet rose sky thyme'.split()
def main():
 root=PackSpec.open('ruby').dataset_root/'sources/curriculum-v1';files={}
 for index,(family,template) in enumerate(TEMPLATES.items()):
  for variant in range(24):
   word=WORDS[(index+variant)%len(WORDS)];rng=random.Random(5231+index*101+variant);source=template.replace('@FN@',word+'_process').replace('@TYPE@',word.title()+'Record').replace('@WORD@',word).replace('@N@',str(rng.randrange(2,30)))+'\n'
   if variant%4==1:source=source.replace('\n','\r\n')
   raw=source.encode();p=root/family/f'{variant:02}.rb';p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=raw:raise ValueError('Preserve previous Ruby task')
   if not p.exists():p.write_bytes(raw)
   files[str(p.relative_to(root))]=hashlib.sha256(raw).hexdigest()
 license=b'Original Ruby tasks authored for Neural Semantic Highlighting.\nPrivate development dataset; no upstream, Golden or display copies.\n';p=root/'LICENSE'
 if p.exists() and p.read_bytes()!=license:raise ValueError('Preserve original Ruby license')
 p.write_bytes(license);lock=dict(format='nsh-ruby-curriculum-v1',generatorSha256=file_hash(Path(__file__)),families=len(TEMPLATES),files=files,licenseSha256=hashlib.sha256(license).hexdigest());p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve previous Ruby curriculum lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(len(files),'tasks in',len(TEMPLATES),'families')
if __name__=='__main__':main()
