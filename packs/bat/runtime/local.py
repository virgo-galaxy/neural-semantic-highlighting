"""Pure neural Bat runtime, without source execution or offline lexers."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack,main
class BatPack(SharedPack):
    def __init__(self,**kwargs):super().__init__(pack_id="bat",**kwargs)
if __name__=="__main__":
    with using("bat"):main()
