"""Python command backed by shared training infrastructure."""
from training.shared.spec import using
from training.shared.train import main

if __name__ == "__main__":
    with using("python"): main()
