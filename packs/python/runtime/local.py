"""Python neural runtime; compiler teacher is an offline-only dependency."""
from training.shared.runtime import LocalPack
from training.shared.spec import using

class PythonLocalPack(LocalPack):
    def __init__(self, **kwargs): super().__init__(pack_id='python', **kwargs)

def main():
    from training.shared.runtime import main as shared_main
    with using('python'): shared_main()

if __name__=='__main__':main()
