from eclypse.remote.bootstrap.options_factory import RayOptionsFactory

# Subclass of RayOptionsFactory for automatic dynamic placement managed by Ray
class DynamicPlacementFactory(RayOptionsFactory):
    def __call__(self, name: str) -> dict:
        options = super().__call__(name)
        node_id = name.split("/")[-1]
        if node_id != "manager":
            options["resources"] = {node_id: 1}
        return options