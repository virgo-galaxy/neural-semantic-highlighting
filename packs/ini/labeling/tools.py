"""Existing CPython ConfigParser supervision; no SDK or package installation."""
from functools import lru_cache
from pathlib import Path
import configparser,json,platform,sys
from training.shared.spec import file_hash
@lru_cache(maxsize=1)
def provenance():
 return dict(name='CPython configparser',version=platform.python_version(),reference='https://docs.python.org/3.12/library/configparser.html',stdlibFile=str(Path(configparser.__file__).resolve()),stdlibSha256=file_hash(Path(configparser.__file__).resolve()),pythonExecutableSha256=file_hash(Path(sys.executable).resolve()),labelerSha256=file_hash(Path(__file__).with_name('label.py')),options=dict(interpolation=None,strict=False,allowNoValue=True,delimiters=['=',':'],commentPrefixes=['#',';'],inlineCommentPrefixes=None,emptyLinesInValues=True,casePreserved=True,syntheticValidationRoot=True),sourceExecution=False,globalInstall=False,newSDKInstalled=False)
def fetch():
 print('Using existing CPython ConfigParser; no download or install')
 print(json.dumps(provenance(),indent=2))
if __name__=='__main__':fetch()
