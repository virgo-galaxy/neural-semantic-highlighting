"""Pure neural AWK runtime, without source execution or offline lexers."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack,main
class AwkPack(SharedPack):
    def __init__(self,**kwargs):super().__init__(pack_id="awk",**kwargs)
if __name__=="__main__":
    with using("awk"):main()
