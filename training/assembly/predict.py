"""Assembly command using the established standalone training workflow."""
from training.shared.spec import using
from training.shared.predict import main

if __name__ == "__main__":
    with using("assembly"):
        main()
