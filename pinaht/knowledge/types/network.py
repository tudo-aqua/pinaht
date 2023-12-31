###############################################################################
# Generated By: generate.py
# User: -
# Date: -
###############################################################################

from pinaht.knowledge.types.knowledge import Knowledge  # noqa F401


from pinaht.knowledge.types.target import Target

from pinaht.knowledge.types.localhost import LocalHost

from pinaht.knowledge.types.netmask import NetMask

from pinaht.knowledge.types.ipaddress import IPAddress


class Network(Knowledge):
    """
    Describes an Object of the Type Network. A network contains several targets to attack.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor of the class Network.
        """

        super().__init__()
        self.init_network(*args)

        self.targets = []

        self.local_host = []

        self.net_mask = []

        self.address = []

        self.type = "BRANCH"
        self.lookup = {
            "targets": self.targets,
            "local_host": self.local_host,
            "net_mask": self.net_mask,
            "address": self.address,
        }

        for key, item in kwargs.items():
            if isinstance(item, list):
                for element in item:
                    self.add_child(key, element)
            else:
                self.add_child(key, item)

    def __str__(self):
        return self.__class__.__name__

    def fuzzy_eq(self, other) -> float:
        # TODO
        if id(self) == id(other):
            return 1.0
        if not type(self) == type(other):
            return 0.0
        return 0.5

    def add_child(self, key, child):
        if key not in self.lookup:
            raise ValueError(
                f"Type 'Network' has no child/attribute with name {key}. "
                "Check types.yaml or the generated PDF for correct identifiers."
            )

        if key == "targets" and isinstance(child, Target):
            self.targets.append(child)
            child.parent = self

        elif key == "local_host" and isinstance(child, LocalHost):
            self.local_host.append(child)
            child.parent = self

        elif key == "net_mask" and isinstance(child, NetMask):
            self.net_mask.append(child)
            child.parent = self

        elif key == "address" and isinstance(child, IPAddress):
            self.address.append(child)
            child.parent = self

        else:
            raise TypeError(f"Child for attribute {key} is not of the right type")

    def init_network(self, *args):  # noqa F811
        pass

    ### USER DEFINED METHODS ### # noqa: E266
