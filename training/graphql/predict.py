"""GraphQL command backed by the shared immutable pipeline."""
from training.shared.spec import using
from training.shared.predict import main

if __name__ == "__main__":
    with using("graphql"):
        main()
