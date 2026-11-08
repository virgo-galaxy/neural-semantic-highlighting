"""Pure neural SQL runtime; no database or offline lexer is used."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack,main
class SqlPack(SharedPack):
    def __init__(self,**kwargs):super().__init__(pack_id="sql",**kwargs)
if __name__=="__main__":
    with using("sql"):main()
