"""Pure neural Makefile inference; no Make execution or source parser."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class MakefilePack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="makefile", **kwargs)

if __name__ == "__main__":
    with using("makefile"):
        main()
