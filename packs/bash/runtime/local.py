"""Parser-free Shell neural runtime."""
from training.shared.runtime import LocalPack
from training.shared.spec import using
class BashLocalPack(LocalPack):
    def __init__(self, **kwargs):super().__init__(pack_id="bash",**kwargs)
def main():
    from training.shared.runtime import main as shared_main
    with using("bash"):shared_main()
if __name__=="__main__":main()
