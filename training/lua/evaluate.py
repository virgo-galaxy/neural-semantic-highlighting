"""Lua command backed by the shared pipeline."""
from training.shared.spec import using
from training.shared.evaluate import main

if __name__ == "__main__":
    with using("lua"):
        main()
