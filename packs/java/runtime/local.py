"""Pure neural Java inference; no JDK, parser or source repair."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class JavaPack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="java", **kwargs)

if __name__ == "__main__":
    with using("java"):
        main()
