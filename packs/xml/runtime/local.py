"""Pure neural Xml inference; no compiler or source parser."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class XmlPack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="xml", **kwargs)

if __name__ == "__main__":
    with using("xml"):
        main()
