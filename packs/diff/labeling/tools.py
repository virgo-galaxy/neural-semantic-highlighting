"""Use the existing Git parser in a read-only statistics mode; no patch is applied."""
from functools import lru_cache
from pathlib import Path
import os,shutil,subprocess,tempfile
from training.shared.spec import file_hash
GIT=Path('/Library/Developer/CommandLineTools/usr/bin/git')
if not GIT.exists():GIT=Path(shutil.which('git')or'/usr/bin/git')
FLAGS=['--no-optional-locks','--no-pager','apply','--numstat','-z','--no-index','--allow-empty','-']
def statistics(source):
 # No inherited repository/index/config variables, working-tree access or hooks.
 env={k:v for k,v in os.environ.items()if not k.startswith('GIT_')};env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL='/dev/null',GIT_TERMINAL_PROMPT='0',LC_ALL='C')
 p=subprocess.run([str(GIT),*FLAGS],input=source.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=tempfile.gettempdir(),env=env,timeout=8,check=False)
 if p.returncode:raise ValueError('Existing Git parser rejected patch: '+p.stderr.decode('utf-8',errors='replace')[:400])
 return p.stdout
@lru_cache(maxsize=1)
def provenance():
 version=subprocess.check_output([str(GIT),'--version'],text=True).strip()
 return dict(name='Existing Git unified-patch parser plus source-local range walker',gitVersion=version,gitExecutable=str(GIT),gitExecutableSha256=file_hash(GIT),parserFlags=FLAGS,reference='https://git-scm.com/docs/git-apply',labelerSha256=file_hash(Path(__file__).with_name('label.py')),appliesPatch=False,sourceExecution=False,globalInstall=False,newSDKInstalled=False)
def fetch():print(provenance())
if __name__=='__main__':fetch()
