"""Pure neural Assembly inference; no assembler, lexer or source execution."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class AssemblyPack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="assembly", **kwargs)

if __name__ == "__main__":
    with using("assembly"):
        main()
