"""Existing CPython Expat validation; no SDK, network or package install."""
from functools import lru_cache
from pathlib import Path
import json,platform,sys,pyexpat
from training.shared.spec import file_hash
@lru_cache(maxsize=1)
def provenance():
 return dict(name='CPython pyexpat',version=platform.python_version(),expatVersion=pyexpat.EXPAT_VERSION,reference='https://docs.python.org/3.12/library/pyexpat.html',extensionSha256=file_hash(Path(pyexpat.__file__).resolve()),pythonExecutableSha256=file_hash(Path(sys.executable).resolve()),labelerSha256=file_hash(Path(__file__).with_name('label.py')),options=dict(namespaceValidation=True,orderedAttributes=True,externalEntities=False,parameterEntities=False,internalEntityDeclarations=False,sourceExecution=False),newSDKInstalled=False)
def fetch():
 print('Using existing CPython Expat; no download or install')
 print(json.dumps(provenance(),indent=2))
if __name__=='__main__':fetch()
