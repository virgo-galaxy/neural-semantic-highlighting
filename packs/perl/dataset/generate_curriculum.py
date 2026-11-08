"""Original Perl programs, short positions and mixed-feature source families."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash

TASKS={
 'imports':'use strict;\nuse warnings;\nuse File::Spec;\nmy $path = File::Spec->catfile("src", "entry-{n}.pl");\nprint $path;\n',
 'lexical-list':'my ($name, $count) = ("item-{n}", {n});\nour $total = $count + 2;\nlocal $mode = "preview";\nsay $name, $total;\n',
 'array-map':'my @values = (1, {n}, 9);\nmy @doubled = map {{ $_ * 2 }} @values;\nprint join(",", @doubled);\n',
 'hash-reference':'my $entry = {{ name => "record-{n}", size => {n} }};\nprint $entry->{{name}}, $entry->{{size}};\n',
 'hash-each':'my %scores = (alpha => {n}, beta => 2);\nwhile (my ($key, $value) = each %scores) {{\n  printf "%s=%d\\n", $key, $value;\n}}\n',
 'function-arguments':'sub {fn} {{\n  my ($name, $limit) = @_;\n  return uc($name) if $limit > {n};\n  return lc $name;\n}}\n{fn}("Virgo", {n});\n',
 'object-call':'package {pkg};\nsub new {{ my ($class) = @_; return bless {{}}, $class; }}\nsub name {{ return "record-{n}"; }}\nmy $object = {pkg}->new();\nsay $object->name();\n',
 'regexp-filter':'my @items = qw(alpha beta gamma);\nfor my $item (@items) {{\n  if ($item =~ /a[[:alpha:]]+/i) {{ print $item; }}\n}}\n',
 'regexp-substitute':'my $text = "build-{n}";\n$text =~ s/build/release/g;\n$text =~ tr/a-z/A-Z/;\nprint $text;\n',
 'regexp-object':'my $rule = qr{{^[A-Z][a-z]{{2,{n}}}$}}i;\nmy $ok = "Virgo" =~ $rule;\nsay $ok ? "yes" : "no";\n',
 'loop-count':'my $sum = 0;\nfor (my $i = 0; $i < {n}; $i++) {{ $sum += $i; }}\nsay $sum;\n',
 'loop-read':'while (my $line = <STDIN>) {{\n  chomp $line;\n  next if $line =~ /^#/;\n  print "$line\\n";\n}}\n',
 'condition-default':'my $limit = $ENV{{LIMIT}} // {n};\nunless ($limit > 0) {{ die "invalid"; }}\nif ($limit > 4) {{ warn "large"; }} else {{ say "small"; }}\n',
 'exceptions':'my $value = eval {{ {fn}({n}) }};\nif ($@) {{ warn $@; }}\n$value //= "fallback";\nprint $value;\n',
 'quote-forms':'my @words = qw(one two three);\nmy $raw = q{{literal $name}};\nmy $message = qq(hello $words[0], version {n});\nsay $raw, $message;\n',
 'unicode-values':'use utf8;\nmy $名字 = "星空 🌌 {n}";\nprint "$名字 🚀";\n',
 'pod-function':'=pod\n\nOriginal {fn} notes for build {n}.\n\n=cut\n\nsub {fn} {{ return shift; }}\nsay {fn}("ready");\n',
 'data-section':'my $line = <DATA>;\nprint $line;\n__DATA__\nOriginal data record {n}\n',
 'heredoc-single':"my $message = <<'TEXT';\n$name and $(literal) build {n}\nTEXT\nprint $message;\n",
 'heredoc-double':'my $name = "Virgo";\nmy $message = <<"GREETING";\nHello $name, version {n}\nGREETING\nsay $message;\n',
 'heredoc-indent':"my $note = <<~'NOTE';\n  Content {n} with $literal\n  NOTE\nprintf '%s', $note;\n",
 'heredoc-queue':"my ($first, $second) = (<<A, <<'B');\nfirst-{n}\nA\n$literal second\nB\nsay $first, $second;\n",
 'heredoc-function':"sub {fn} {{\n  return <<'BODY';\nfunction example() {{ echo {n}; }}\nBODY\n}}\nprint {fn}();\n",
 'heredoc-lines':"for my $name (qw(alpha beta)) {{\n  print <<LABEL;\nHello $name {n}\nLABEL\n}}\nsay 'complete';\n",
 'mixed-normalize':'sub {fn} {{\n  my ($value) = @_;\n  $value =~ s/\\s+/-/g;\n  return $value;\n}}\nfor my $line ("alpha beta", "gamma-{n}") {{\n  if (length $line > 3) {{ say {fn}($line); }}\n}}\n',
 'mixed-validate':'sub {fn} {{\n  my ($value) = @_;\n  return $value =~ qr{{^[a-z][a-z0-9_]*$}}i;\n}}\nmy @items = ("alpha", "item_{n}");\nfor my $item (@items) {{ next unless {fn}($item); print "$item\\n"; }}\n',
 'mixed-count':'sub {fn} {{ my ($x) = @_; return $x + {n}; }}\nmy %counts;\nfor my $word (qw(alpha beta alpha)) {{\n  if ($word =~ /a/) {{ $counts{{$word}}++; }}\n}}\nsay {fn}(scalar keys %counts);\n',
 'mixed-select':'sub {fn} {{\n  my @items = @_;\n  return grep {{ /entry/ }} @items;\n}}\nmy @selected = {fn}("entry-{n}", "other");\nforeach my $item (@selected) {{ if (defined $item) {{ print $item; }} }}\n',
 'stateful-sub':'use feature "state";\nsub {fn} {{ state $count = {n}; return ++$count; }}\nsay {fn}();\n',
 'signature-sub':'use feature "signatures";\nno warnings "experimental::signatures";\nsub {fn} ($name, $limit = {n}) {{ return "$name:$limit"; }}\nsay {fn}("Virgo");\n',
}

def main():
    root=PackSpec.open('perl').dataset_root/'sources/curriculum-v1';files={}
    for family,template in TASKS.items():
        for index in range(20):
            source=template.format(n=3+index,fn=['normalize','render','convert','summarize','validate'][index%5],pkg=['Virgo::Entry','App::Record','Preview::Item'][index%3])
            if index%4==1:source='# Original Perl source\n'+source
            elif index%4==2:source='\n\n'+source
            elif index%4==3:source='use strict;\nuse warnings;\n'+source
            if index%5==3:source=source.replace('\n','\r\n')
            files[f'{family}/{index:02}.pl']=source.encode()
    files['LICENSE']=b'Original private neural-semantic-highlighting Perl curriculum. No additional license grant.\n'
    root.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():
        path=root/name
        if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing Perl curriculum')
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    lock={'format':'nsh-perl-original-curriculum-v1','generatorHash':file_hash(Path(__file__)),'files':{name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}}
    path=root/'source.lock.json'
    if path.exists() and json.loads(path.read_text())!=lock:raise ValueError('Existing Perl source lock differs')
    path.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'original programs')

if __name__=='__main__':main()
