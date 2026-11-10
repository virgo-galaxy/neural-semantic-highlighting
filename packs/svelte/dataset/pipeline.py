from training.shared.spec import using
from training.shared.pipeline import main

if __name__ == "__main__":
    with using("svelte"):
        main()
