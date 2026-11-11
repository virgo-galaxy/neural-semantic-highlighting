"""Pinned official parser JARs in project cache; reuse JDK 22, never install an SDK."""
from functools import lru_cache
from pathlib import Path
import hashlib,json,os,subprocess
from training.shared.spec import REPOSITORY,file_hash,dumps

CONFIG=Path(__file__).with_name('tools.json')
SOURCE=Path(__file__).with_name('KotlinTree.java')
DIRECTORY=REPOSITORY/'artifacts/tools/kotlin-gold/maven-2.4.21'

def jdk_home():
 root=Path(os.environ.get('NSH_KOTLIN_JAVA_HOME',str(Path.home()/'Library/Java/JavaVirtualMachines/openjdk-22.0.1/Contents/Home'))).expanduser().resolve()
 if '22.0.1' not in (root/'release').read_text():raise ValueError('Offline Gold requires the existing pinned JDK 22.0.1')
 return root

def fetch():
 DIRECTORY.mkdir(parents=True,exist_ok=True)
 for item in json.loads(CONFIG.read_text())['artifacts']:
  p=DIRECTORY/item['url'].rsplit('/',1)[-1]
  if not p.exists():
   raw=subprocess.check_output(['curl','--fail','--silent','--show-error','--location','--retry','3','--connect-timeout','15','--max-time','240',item['url']])
   if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Official parser artifact differs')
   p.write_bytes(raw)
  if file_hash(p)!=item['sha256']:raise ValueError('Preserve modified parser JAR: '+p.name)
 print('Pinned Kotlin parse-only components:',DIRECTORY)

@lru_cache(maxsize=1)
def provenance():
 config=json.loads(CONFIG.read_text());jars={}
 for item in config['artifacts']:
  p=DIRECTORY/item['url'].rsplit('/',1)[-1]
  if not p.exists() or file_hash(p)!=item['sha256']:raise ValueError('Run make dataset-kotlin-tools for the pinned isolated parser')
  jars[p.name]=item['sha256']
 home=jdk_home()
 return {'name':'Official Kotlin 2.4.21 parse-only PSI and lexer','version':'2.4.21','configSha256':file_hash(CONFIG),'jars':jars,'jdkReleaseSha256':file_hash(home/'release'),'javacModuleSha256':file_hash(home/'jmods/jdk.compiler.jmod'),'helperSourceSha256':file_hash(SOURCE),'builderSha256':file_hash(Path(__file__)),'newlineAdapter':'parser LF text with exact UTF-16 mapping to original CRLF/CR source; original training bytes unchanged','sourceAnalysis':False,'scriptEvaluation':False,'compilerPlugins':False,'SDKInstalled':False}

def classpath():return os.pathsep.join(str(DIRECTORY/name) for name in provenance()['jars'])

def executable():
 identity=provenance();folder=REPOSITORY/'artifacts/tools/kotlin-gold/helpers'/hashlib.sha256(dumps(identity).encode()).hexdigest();binary=folder/'KotlinTree.class';lock=folder/'build.json'
 if binary.exists():
  r=json.loads(lock.read_text())
  if r['identity']!=identity or r['binarySha256']!=file_hash(binary):raise ValueError('Preserve previous Kotlin helper build')
 else:
  folder.mkdir(parents=True,exist_ok=True)
  command=[str(jdk_home()/'bin/javac'),'-proc:none','-cp',classpath(),'-d',str(folder),str(SOURCE)]
  p=subprocess.run(command,capture_output=True,text=True)
  if p.returncode:raise ValueError('Kotlin parse-only helper build failed: '+p.stderr)
  lock.write_text(json.dumps({'identity':identity,'command':command,'binarySha256':file_hash(binary)},indent=2)+'\n')
 return [str(jdk_home()/'bin/java'),'-Djava.awt.headless=true','-Xmx768m','-cp',str(folder)+os.pathsep+classpath(),'KotlinTree']

if __name__=='__main__':fetch();print(executable())
