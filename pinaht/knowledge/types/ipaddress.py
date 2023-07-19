###############################################################################
# Generated By: generate.py
# User: -
# Date: -
###############################################################################

from pinaht.knowledge.types.knowledge import Knowledge  # noqa F401


class IPAddress(Knowledge, int):
    """
    Describes an Object of the Type IPAddress. An IP address is a single network Address.
    """

    def __new__(cls, *args, **kwargs):
        return super(IPAddress, cls).__new__(cls, args[0])

    def __init__(self, *args, **kwargs):
        """
        Constructor of the class IPAddress.
        """

        super().__init__()
        self.init_ipaddress(*args)

        self.type = "LEAF_EXTENDS"
        self.lookup = {}

        for key, item in kwargs.items():
            if isinstance(item, list):
                for element in item:
                    self.add_child(key, element)
            else:
                self.add_child(key, item)

    def fuzzy_eq(self, other) -> float:
        if type(self) == type(other):
            if self == other:
                return 1.0
        return 0.0

    def add_child(self, key, child):
        if key not in self.lookup:
            raise ValueError(
                f"Type 'IPAddress' has no child/attribute with name {key}. "
                "Check types.yaml or the generated PDF for correct identifiers."
            )

        else:
            raise TypeError(f"Child for attribute {key} is not of the right type")

    def init_ipaddress(self, *args):  # noqa F811
        pass

    ### USER DEFINED METHODS ### # noqa: E266

    @staticmethod
    def str_to_ip(ip_address: str):
        ip_address = "".join(map(lambda i: f"{int(i):08b}", ip_address.split(".")))
        return int(ip_address, 2)

    def __str__(self):
        binary = f"{self:32b}".replace(" ", "0")
        ip_address = [binary[0:8], binary[8:16], binary[16:24], binary[24:32]]
        ip_address = list(map(lambda b: str(int(b, 2)), ip_address))
        return ".".join(ip_address)