"""Pure neural Dockerfile inference; no Docker, Go or source parser."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class DockerfilePack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="dockerfile", **kwargs)

if __name__ == "__main__":
    with using("dockerfile"):
        main()
