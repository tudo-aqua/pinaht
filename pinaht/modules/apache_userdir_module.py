from pinaht.file_manager import FileManager
from pinaht.modules.module import Module
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type, check_str
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent, merge
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.port import Port
from pinaht.knowledge.types.credentials import Credentials
from pinaht.knowledge.types.name import Name
from typing import Tuple, Dict
import requests
from pinaht.reporting.report_util import str_to_latex

NAMES_LIST = "unix_users.txt"


class ApacheUserdirModule(Module):
    """
    Extracts usernames from an apache server with the userdir module enabled.
    """

    def __init__(self, manager, file_manager: FileManager, **kwargs):
        super().__init__(manager, **kwargs)

        self._file_manager = file_manager

        usernames_file = self._file_manager.get_file("ApacheUserdirModule", NAMES_LIST)
        read_data = usernames_file.read()
        usernames_file.close()
        self.user_names_list = read_data.split("\n")

        self.estimated_time = float(len(self.user_names_list)) * 0.05
        self.success_chance = 0.1

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Generates the preconditions
        """
        target_precondition = check_type(Target)
        ip_address_precondition = check_type(IPAddress)
        service_precondition = check_type(Service)
        port_precondition = check_type(Port)
        service_name_precondition = check_str(lambda k: 1.0 if "apache" in str.lower(k) else 0.0)

        return {
            "apache": (
                {
                    "target": target_precondition,
                    "ip_address": ip_address_precondition,
                    "service": service_precondition,
                    "port": port_precondition,
                    "service_name": service_name_precondition,
                },
                merge(
                    [is_parent("target", ["ip_address", "service"]), is_parent("service", ["service_name", "port"])]
                ),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        Searches for usernames
        """
        target = keyed_knowledge["target"]
        ip_address = keyed_knowledge["ip_address"]

        buffered_module_manager.report(
            f"""Testing usernames with ApacheUserdir module. Awaiting HTTP Statuscode 200
            on paths \\code{{http://{ip_address}/\\textasciitilde{{}}<username>}}. This module is using the
            wordlist \\code{{{str_to_latex(NAMES_LIST)}}} in the module directory."""
        )

        found_usernames = []
        for potential_user in self.user_names_list:
            request_string = "http://" + str(ip_address) + "/~" + potential_user + "/"
            response = requests.get(request_string)
            if response.status_code == 200:
                found_usernames.append(potential_user)

        if len(target.lookup["credentials"]) == 0:
            cred = Credentials()
            buffered_module_manager.add_knowledge(target, "credentials", cred, 1.0)
            for name in found_usernames:
                buffered_module_manager.add_knowledge(cred, "users", Name(name), 1.0)
                buffered_module_manager.report(f"Found username \\code{{{str_to_latex(name)}}}.")
        else:
            for name in found_usernames:
                buffered_module_manager.add_knowledge(target.lookup["credentials"][0], "users", Name(name), 1.0)
                buffered_module_manager.report(f"Found username \\code{{{str_to_latex(name)}}}.")
