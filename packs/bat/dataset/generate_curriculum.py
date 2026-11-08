"""Original bounded CMD/BAT tasks; no Windows execution or copied probes."""
from pathlib import Path
import hashlib,json
from training.shared.spec import PackSpec,file_hash
TASKS={
 'variables-set':'@echo off\nset "name=record-{n}"\necho %name%\n',
 'variables-delayed':'@echo off\nsetlocal EnableDelayedExpansion\nset /a count={n}\nset /a count+=1\necho !count!\nendlocal\n',
 'variables-arguments':'@echo off\nset "root=%~dp0"\necho %~nx0 %1 %2 %*\n',
 'variables-substring':'@echo off\nset "name=account-{n}"\necho %name:~0,4%\necho %name:account=record%\n',
 'variables-env':'@echo off\nset "output=%TEMP%\\report-{n}.txt"\necho %USERNAME% %CD% %ERRORLEVEL%\n',
 'loop-files':'@echo off\nfor %%F in (*.txt) do (\n  echo %%~nxF\n)\n',
 'loop-lines':'@echo off\nfor /f "tokens=1,2 delims=," %%A in (records.csv) do (\n  echo %%A %%B {n}\n)\n',
 'loop-numeric':'@echo off\nfor /l %%N in (1,1,{n}) do echo %%N\n',
 'loop-directories':'@echo off\nfor /d %%D in (*) do (\n  if exist "%%D\\index.txt" echo %%D\n)\n',
 'loop-recursive':'@echo off\nfor /r "src" %%F in (*.js) do echo %%~fF\n',
 'loop-delayed':'@echo off\nsetlocal EnableDelayedExpansion\nset /a count=0\nfor %%F in (*.log) do (\n  set /a count+=1\n  echo !count! %%F\n)\nendlocal\n',
 'condition-exist':'@echo off\nif exist "input-{n}.txt" (\n  echo ready\n) else (\n  echo missing\n)\n',
 'condition-defined':'@echo off\nif defined BUILD_MODE echo %BUILD_MODE%\nif not defined BUILD_MODE set "BUILD_MODE=release-{n}"\n',
 'condition-string':'@echo off\nif /i "%1"=="release" (\n  echo release-{n}\n) else (\n  echo debug\n)\n',
 'condition-number':'@echo off\nif %count% GEQ {n} echo complete\nif %count% LSS {n} echo waiting\n',
 'label-subroutine':'@echo off\ncall :{label} "source-{n}"\ngoto :eof\n\n:{label}\necho Selected %~1\nexit /b 0\n',
 'label-error':'@echo off\nnode build.js\nif errorlevel 1 goto {label}\necho success\nexit /b 0\n:{label}\necho failed-{n}\nexit /b 1\n',
 'label-argument':'@echo off\nif "%~1"=="" goto {label}\necho %1\nexit /b 0\n:{label}\necho argument required {n}\nexit /b 2\n',
 'label-loop':'@echo off\nset /a count={n}\n:{label}\necho %count%\nset /a count-=1\nif %count% GTR 0 goto {label}\n',
 'label-call-multiple':'@echo off\ncall :{label} {n}\ncall :{label} 2\nexit /b 0\n:{label}\necho Processed %1\nexit /b\n',
 'label-choice':'@echo off\nif /i "%1"=="test" goto {label}\necho build-{n}\nexit /b\n:{label}\necho tests\nexit /b\n',
 'redirect-files':'@echo off\necho report-{n} > output.txt\nnode build.js >> output.txt 2>&1\n',
 'command-chain':'@echo off\nnode check.js && echo ready-{n} || echo failed\n',
 'command-path':'@echo off\ncall "%~dp0helpers.cmd" %*\nnode "%~dp0index.js" --limit {n}\n',
 'quoted-path':'@echo off\nset "source=%~dp0input files"\ncopy /Y "%source%\\record-{n}.txt" "%TEMP%\\record.txt"\n',
 'pipe-find':'@echo off\ndir /b *.txt | findstr /i "ready-{n}"\n',
 'push-directory':'@echo off\npushd "%~dp0"\nnode scripts\\build.js --count {n}\npopd\n',
 'continuations':'@echo off\nnode build.js ^\n  --mode release ^\n  --count {n}\n',
 'comment-lines':'@echo off\nrem Original report task {n}\n:: Source display note 星空 🌌\necho Ready\n',
 'arithmetic':'@echo off\nset /a total=({n}+2)*3\nset /a total-=1\necho %total%\n',
}
def main():
 root=PackSpec.open('bat').dataset_root/'sources/curriculum-v1';files={}
 for family,template in TASKS.items():
  for i in range(32):
   source=template.format(n=i+7,label=['render_report','show_record','check_source','write_summary'][i%4])
   source=['','rem Original task\n','\n',':: Short script\n'][(i//8)%4]+source
   if i%3==1:source=source.replace('\n','\r\n')
   if i%7==3:source=source.upper()
   extension='.bat' if i%2==0 else '.cmd';files[f'{family}/{i:02}'+extension]=source.encode()
 files['LICENSE']=b'Original private neural-semantic-highlighting BAT/CMD curriculum. No additional license grant.\n'
 for name,raw in files.items():
  path=root/name
  if path.exists() and path.read_bytes()!=raw:raise ValueError('Preserve original source')
  path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
 lock={'format':'nsh-bat-original-tasks-v1','generatorHash':file_hash(Path(__file__)),'files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()}}
 p=root/'source.lock.json'
 if p.exists() and json.loads(p.read_text())!=lock:raise ValueError('Preserve source lock')
 p.write_text(json.dumps(lock,indent=2)+'\n');print(root,len(files)-1,'original source tasks')
if __name__=='__main__':main()
