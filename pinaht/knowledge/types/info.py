###############################################################################
# Generated By: generate.py
# User: -
# Date: -
###############################################################################

from pinaht.knowledge.types.knowledge import Knowledge  # noqa F401


from pinaht.knowledge.types.extrainfo import ExtraInfo


class Info(ExtraInfo, str):
    """
    Additional infos about the service.
    """

    def __new__(cls, *args, **kwargs):
        return super(Info, cls).__new__(cls, args[0])

    def __init__(self, *args, **kwargs):
        """
        Constructor of the class Info.
        """

        super().__init__()
        self.init_info(*args)

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
                f"Type 'Info' has no child/attribute with name {key}. "
                "Check types.yaml or the generated PDF for correct identifiers."
            )

        else:
            raise TypeError(f"Child for attribute {key} is not of the right type")

    def init_info(self, *args):  # noqa F811
        pass

    ### USER DEFINED METHODS ### # noqa: E266
