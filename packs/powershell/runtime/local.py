"""Pure neural PowerShell runtime, without source execution or offline lexers."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack,main
class PowerShellPack(SharedPack):
    def __init__(self,**kwargs):super().__init__(pack_id="powershell",**kwargs)
if __name__=="__main__":
    with using("powershell"):main()
