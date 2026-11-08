"""Assembly command using the established standalone training workflow."""
from training.shared.spec import using
from training.shared.export_model import main

if __name__ == "__main__":
    with using("assembly"):
        main()
