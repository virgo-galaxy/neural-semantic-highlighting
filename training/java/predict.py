"""Java command backed by the established shared pipeline."""
from training.shared.spec import using
from training.shared.predict import main

if __name__ == "__main__":
    with using("java"):
        main()
