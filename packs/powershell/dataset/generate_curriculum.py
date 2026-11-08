"""Original short PowerShell tasks with independent source-family grouping."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash
TASKS={
 'function-name':'function {fn} {{ param([string]$Name) Write-Output "Ready: $Name" }}\n{fn} -Name \'Virgo\'\n',
 'function-count':'function {fn} {{ param([int]$Count = {n}) return $Count * 2 }}\n$result = {fn} -Count {n}\n',
 'function-pipeline':'function {fn} {{ process {{ $_ | Select-Object Name, Id }} }}\nGet-Process | {fn}\n',
 'function-switch':'function {fn} {{ param([switch]$Force) if ($Force) {{ Write-Output \'forced\' }} else {{ Write-Output \'normal\' }} }}\n',
 'function-validation':'function {fn} {{ [CmdletBinding()] param([Parameter(Mandatory)][string]$Path) Get-Content -LiteralPath $Path }}\n',
 'function-hash':'function {fn} {{ param([string]$Name) return @{{ Name = $Name; Count = {n} }} }}\n$data = {fn} -Name \'sample\'\n',
 'pipeline-filter':'Get-ChildItem -Path \'./src\' -Recurse | Where-Object {{ $_.Length -gt {n} }} | Select-Object Name, Length\n',
 'pipeline-sort':'Get-Process | Sort-Object CPU -Descending | Select-Object -First {n} Name, Id\n',
 'pipeline-each':'1..{n} | ForEach-Object {{ Write-Output ($_ * 2) }}\n',
 'pipeline-group':'Get-Service | Group-Object Status | Sort-Object Count -Descending\n',
 'hashtable-config':'$config = @{{ Name = \'Virgo\'; Port = {n}; Enabled = $true }}\nWrite-Output $config.Name\n',
 'hashtable-splat':'$options = @{{ Path = \'./input.txt\'; Encoding = \'utf8\' }}\nGet-Content @options | Select-Object -First {n}\n',
 'hashtable-nested':'$settings = @{{ App = @{{ Name = \'site\'; Port = {n} }}; Enabled = $true }}\n$settings.App.Name\n',
 'hashtable-ordered':'$row = [ordered]@{{ Id = {n}; Label = \'record\' }}\n[pscustomobject]$row | ConvertTo-Json\n',
 'array-foreach':'$names = @(\'alpha\', \'beta\', \'gamma\')\nforeach ($name in $names) {{ Write-Output "$name-{n}" }}\n',
 'loop-for':'for ($i = 0; $i -lt {n}; $i++) {{ Write-Output $i }}\n',
 'loop-while':'$remaining = {n}\nwhile ($remaining -gt 0) {{ $remaining--; Write-Output $remaining }}\n',
 'condition-compare':'if ($count -ge {n} -and $ready) {{ Write-Output \'complete\' }} elseif ($null -eq $count) {{ return }} else {{ Write-Output \'waiting\' }}\n',
 'switch-values':'switch ($state) {{ \'ready\' {{ Write-Output {n} }} \'stopped\' {{ break }} default {{ Write-Output \'unknown\' }} }}\n',
 'try-catch':'try {{ Get-Content -LiteralPath \'input.txt\' -ErrorAction Stop }} catch {{ Write-Warning $_.Exception.Message }} finally {{ Write-Output \'finished\' }}\n',
 'type-method':'$value = [int]::Parse(\'{n}\')\n$text = [string]::Format(\'count={{0}}\', $value)\nWrite-Output $text\n',
 'class-members':'class Item {{ [string]$Name; [int]$Count; Item([string]$name) {{ $this.Name = $name; $this.Count = {n} }} }}\n',
 'strings-literal':"$text = 'It''s prepared; $HOME stays literal'\nWrite-Output $text\n",
 'strings-expand':'$name = \'Virgo\'\n$message = "Hello $name; total=$($items.Count)"\nWrite-Output $message\n',
 'strings-escape':'$text = "line`nvalue`" quoted`" {n}"\nWrite-Output $text\n',
 'comments-block':'<# Original nested comment <# inner #> ends here #>\n# line note\nWrite-Output \'星空 🌌\'\n',
 'operators-modern':'$name = $inputName ?? \'guest\'\n$count ??= {n}\n$result = $ready ? \'yes\' : \'no\'\n',
 'here-single-set':"$message = @'\n{body}\n'@\nWrite-Output $message\n",
 'here-double-set':'$message = @"\n{body}\n"@\nWrite-Output $message\n',
 'here-single-call':"Write-Output @'\n{body}\n'@\nGet-Date\n",
 'here-double-return':'function {fn} {{\n  return @"\n{body}\n"@\n}}\n{fn}\n',
 'here-single-hash':"$config = @{{ Content = @'\n{body}\n'@\n  Count = {n}\n}}\n$config.Count\n",
 'here-double-mixed':'$name = \'Virgo\'\n$text = @"\n{body}\n"@\nGet-ChildItem | Select-Object -First {n}\n',
}
def main():
 root=PackSpec.open('powershell').dataset_root/'sources/curriculum-v1';files={}
 for family,template in TASKS.items():
  for i in range(32):
   body=['Hello $name\nThe report is ready.',"It is a literal body; 'quotes' and $HOME remain text.",'星空 🌌\n$count = 42 # still string text','A longer note for the selected account\nsecond line is ready'][(i//2)%4]
   if i%2:body='  '+body.replace('\n','\n  ')
   source=template.format(fn=['Get-Summary','Format-Record','Measure-Count','Get-DisplayName'][i%4],n=i+5,body=body)
   source=['','# Original PowerShell task\n','\n','<# Short source fragment #>\n'][(i//8)%4]+source
   if i%5==2:source=source.replace('\n','\r\n')
   files[f'{family}/{i:02}.ps1']=source.encode()
 files['LICENSE']=b'Original private neural-semantic-highlighting PowerShell tasks. No additional license grant.\n'
 for name,raw in files.items():
  path=root/name
  if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve existing source')
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 lock={'format':'nsh-powershell-original-tasks-v1','generatorHash':file_hash(Path(__file__)),'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
 target=root/'source.lock.json'
 if target.exists() and json.loads(target.read_text())!=lock:raise ValueError('Preserve old lock')
 target.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'original source tasks')
if __name__=='__main__':main()
