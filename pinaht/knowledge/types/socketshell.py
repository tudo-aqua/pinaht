###############################################################################
# Generated By: generate.py
# User: -
# Date: -
###############################################################################

from pinaht.knowledge.types.knowledge import Knowledge  # noqa F401


from pinaht.knowledge.types.shell import Shell

from pinaht.knowledge.types.privilege import Privilege

from pinaht.knowledge.types.user import User


class SocketShell(Shell):
    """
    Wraps Python socket shells.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor of the class SocketShell.
        """

        super().__init__()
        self.init_socketshell(*args)

        self.privilege = []

        self.shelluser = []

        self.type = "BRANCH"
        self.lookup = {"privilege": self.privilege, "shelluser": self.shelluser}

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
                f"Type 'SocketShell' has no child/attribute with name {key}. "
                "Check types.yaml or the generated PDF for correct identifiers."
            )

        if key == "privilege" and isinstance(child, Privilege):
            self.privilege.append(child)
            child.parent = self

        elif key == "shelluser" and isinstance(child, User):
            self.shelluser.append(child)
            child.parent = self

        else:
            raise TypeError(f"Child for attribute {key} is not of the right type")

    def init_socketshell(self, *args):  # noqa F811
        pass

    ### USER DEFINED METHODS ### # noqa: E266

    def init_socketshell(self, *args):  # noqa F811
        """
        Creates a wrapper for a Python socket shell.

        :param args[0]: Python socket connection to a shell
        """
        super().__init__()
        self._shell = args[0]

    def execute(self, command, timeout=10, new_shell=False):
        """
        Executes a command in the shell and returns its output.

        :param command: command to execute
        :param timeout: number of seconds after which to raise a ShellTimeoutError exception
        :return: shell output
        """
        self._shell.send(str.encode(command, encoding="utf-8"))
        return str(self._shell.recv(1024), "utf-8")
