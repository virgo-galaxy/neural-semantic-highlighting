"""Protocol Buffers command backed by the shared immutable pipeline."""
from training.shared.spec import using
from training.shared.challenge import main

if __name__ == "__main__":
    with using("protobuf"):
        main()
