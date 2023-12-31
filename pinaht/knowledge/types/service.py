###############################################################################
# Generated By: generate.py
# User: -
# Date: -
###############################################################################

from pinaht.knowledge.types.knowledge import Knowledge  # noqa F401


from pinaht.knowledge.types.port import Port

from pinaht.knowledge.types.name import Name

from pinaht.knowledge.types.version import Version

from pinaht.knowledge.types.protocol import Protocol

from pinaht.knowledge.types.transport import Transport

from pinaht.knowledge.types.status import Status

from pinaht.knowledge.types.extrainfo import ExtraInfo


class Service(Knowledge):
    """
    Describes an Object of the Type Service. A service is a program, that is accessible from the outside.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor of the class Service.
        """

        super().__init__()
        self.init_service(*args)

        self.port = []

        self.service_name = []

        self.service_version = []

        self.protocol = []

        self.transport = []

        self.status = []

        self.extrainfo = []

        self.type = "BRANCH"
        self.lookup = {
            "port": self.port,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "protocol": self.protocol,
            "transport": self.transport,
            "status": self.status,
            "extrainfo": self.extrainfo,
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
                f"Type 'Service' has no child/attribute with name {key}. "
                "Check types.yaml or the generated PDF for correct identifiers."
            )

        if key == "port" and isinstance(child, Port):
            self.port.append(child)
            child.parent = self

        elif key == "service_name" and isinstance(child, Name):
            self.service_name.append(child)
            child.parent = self

        elif key == "service_version" and isinstance(child, Version):
            self.service_version.append(child)
            child.parent = self

        elif key == "protocol" and isinstance(child, Protocol):
            self.protocol.append(child)
            child.parent = self

        elif key == "transport" and isinstance(child, Transport):
            self.transport.append(child)
            child.parent = self

        elif key == "status" and isinstance(child, Status):
            self.status.append(child)
            child.parent = self

        elif key == "extrainfo" and isinstance(child, ExtraInfo):
            self.extrainfo.append(child)
            child.parent = self

        else:
            raise TypeError(f"Child for attribute {key} is not of the right type")

    def init_service(self, *args):  # noqa F811
        pass

    ### USER DEFINED METHODS ### # noqa: E266
