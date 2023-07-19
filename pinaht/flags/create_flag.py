from pinaht.flags.flag import Flag
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.operatingsystemtype import OperatingSystemType
from pinaht.knowledge.types.os import OS
from pinaht.knowledge.types.shell import Shell, ShellTimeoutError
from pinaht.knowledge.types.privilege import Privilege
import pinaht.knowledge.precondition_factory.preconditions as pc
import pinaht.knowledge.precondition_factory.metapreconditions as mc
from typing import Tuple, Dict


class CreateFlag(Flag):
    """
    # TODO
    """

    def __init__(self, manager, **kwargs):
        super().__init__(manager, **kwargs)

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Generates the preconditions
        """

        privilege_precond = pc.check_value(Privilege.ROOT)
        os_precond = pc.check_type(OS)
        os_type_precond = pc.check_value(OperatingSystemType.LINUX)
        shell_precond = pc.check_type(Shell)

        parents_metaprecond = mc.merge(
            [
                mc.is_parent("shell", ["privilege"]),
                mc.is_parent("os", ["ostype"]),
                mc.identical_parents(["os", "shell"]),
            ]
        )

        return {
            "create-flag-meta": (
                {"privilege": privilege_precond, "ostype": os_type_precond, "shell": shell_precond, "os": os_precond},
                parents_metaprecond,
            )
        }

    def check(self, meta_key: str, keyed_knowledge: Dict[str, Knowledge]) -> bool:
        """
        Echoes to /root/flag.txt
        """
        shell = keyed_knowledge["shell"]

        try:
            shell.execute("echo 'HACKED!' > /root/flag.txt")
        except (ShellTimeoutError):
            self._logger.error("cannot echo to file... shell timeout error")
        return True

    def description(self) -> str:
        return "This Flag creats a 'flag.txt' file in the root directory on the target."
