"""Pure neural C# inference; no .NET SDK, compiler or source parser."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class CSharpPack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="csharp", **kwargs)

if __name__ == "__main__":
    with using("csharp"):
        main()
