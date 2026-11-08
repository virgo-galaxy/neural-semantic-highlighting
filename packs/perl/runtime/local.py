"""Pure neural Perl runtime; no offline parser is imported."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack,main
class PerlPack(SharedPack):
    def __init__(self,**kwargs):super().__init__(pack_id="perl",**kwargs)
if __name__=="__main__":
    with using("perl"):main()
