###############################################################################
# Generated By: generate.py
# User: -
# Date: -
###############################################################################

from pinaht.knowledge.types.knowledge import Knowledge  # noqa F401


from pinaht.knowledge.types.extrainfo import ExtraInfo

from pinaht.knowledge.types.name import Name

from pinaht.knowledge.types.text import Text

from pinaht.knowledge.types.scriptelement import ScriptElement


class Script(ExtraInfo):
    """
    The result of a nmap script.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor of the class Script.
        """

        super().__init__()
        self.init_script(*args)

        self.id = []

        self.output = []

        self.elements = []

        self.type = "BRANCH"
        self.lookup = {"id": self.id, "output": self.output, "elements": self.elements}

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
                f"Type 'Script' has no child/attribute with name {key}. "
                "Check types.yaml or the generated PDF for correct identifiers."
            )

        if key == "id" and isinstance(child, Name):
            self.id.append(child)
            child.parent = self

        elif key == "output" and isinstance(child, Text):
            self.output.append(child)
            child.parent = self

        elif key == "elements" and isinstance(child, ScriptElement):
            self.elements.append(child)
            child.parent = self

        else:
            raise TypeError(f"Child for attribute {key} is not of the right type")

    def init_script(self, *args):  # noqa F811
        pass

    ### USER DEFINED METHODS ### # noqa: E266
