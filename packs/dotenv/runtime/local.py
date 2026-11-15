"""Pure neural Dotenv inference; no compiler or source parser."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class DotenvPack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="dotenv", **kwargs)

if __name__ == "__main__":
    with using("dotenv"):
        main()
