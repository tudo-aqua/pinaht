from typing import Tuple, Dict

from pinaht.knowledge.types.port import Port
from pinaht.modules.module import Module
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type, check_str
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent, merge
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.loginuser import LoginUser
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.user import User
from pinaht.knowledge.types.name import Name
from pinaht.knowledge.types.password import Password
from pinaht.knowledge.types.credentials import Credentials
from pinaht.knowledge.types.privilege import Privilege
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.types.secureshell import SecureShell
from paramiko import AuthenticationException, SSHException
import ipaddress
import socket


class SSHToShell(Module):
    def __init__(self, manager, **kwargs):
        super(SSHToShell, self).__init__(manager, **kwargs)

        self.estimated_time = 5
        self.success_chance = 0.01

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """

        target = keyed_knowledge["target"]
        ip = str(ipaddress.IPv4Address(keyed_knowledge["ip"]))
        user_name = str(keyed_knowledge["name"])
        port = int(keyed_knowledge["port"])

        if meta_key == "no_pw_ssh":  # Key from Meta-Precondition
            password = ""
            self._logger.info("Excecuting SSH on user " + user_name + " with NO Password.")
        elif meta_key == "pw_ssh":
            password = keyed_knowledge["password"]
            self._logger.info("Excecuting SSH with Password.")
        elif meta_key == "credentials_ssh":
            password = keyed_knowledge["password"]
            self._logger.info("Excecuting SSH on user " + user_name + " with password '" + str(password) + "'.")
        else:
            self._logger.error("Wrong meta Key. recon_local-service Module not implemented properly.")
            return

        try:
            shell = SecureShell(user_name, password, ip, port)
        except (AuthenticationException, SSHException, socket.error):
            self._logger.debug("Failed to invoke a SSH-Shell, aborting Module!")
            return

        buffered_module_manager.add_knowledge(target, "shells", shell, 1.0)
        buffered_module_manager.add_knowledge(shell, "privilege", Privilege.OTHER, 1.0)
        buffered_module_manager.add_knowledge(shell, "shelluser", User(user_name), 1.0)

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        pre_ip = check_type(IPAddress)
        pre_port = check_type(Port)
        pre_target = check_type(Target)
        pre_service = check_type(Service)
        pre_service_name = check_str(lambda value: "openssh" in str.lower(value))
        pre_user = check_type(LoginUser)
        pre_user_name = check_type(Name)
        pre_password = check_type(Password)
        pre_credentials = check_type(Credentials)

        return {
            "pw_ssh": (
                {
                    "target": pre_target,
                    "ip": pre_ip,
                    "port": pre_port,
                    "service": pre_service,
                    "user": pre_user,
                    "name": pre_user_name,
                    "service_name": pre_service_name,
                    "password": pre_password,
                },
                merge(
                    [
                        is_parent("target", ["ip", "service", "user"]),
                        is_parent("user", ["name", "password"]),
                        is_parent("service", ["service_name", "port"]),
                    ]
                ),
            ),
            "credentials_ssh": (
                {
                    "target": pre_target,
                    "ip": pre_ip,
                    "port": pre_port,
                    "service": pre_service,
                    "credentials": pre_credentials,
                    "name": pre_user_name,
                    "service_name": pre_service_name,
                    "password": pre_password,
                },
                merge(
                    [
                        is_parent("target", ["ip", "service", "credentials"]),
                        is_parent("credentials", ["name", "password"]),
                        is_parent("service", ["service_name", "port"]),
                    ]
                ),
            ),
        }
