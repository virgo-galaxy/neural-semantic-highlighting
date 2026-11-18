"""Pure neural GraphQL inference; no parser or server."""
from training.shared.spec import using
from training.shared.runtime import LocalPack as SharedPack, main

class GraphqlPack(SharedPack):
    def __init__(self, **kwargs):
        super().__init__(pack_id="graphql", **kwargs)

if __name__ == "__main__":
    with using("graphql"):
        main()
