from typing import Tuple, Dict
import ipaddress
import shutil
from pinaht.modules.module import Module
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent
from pinaht.knowledge.types.localhost import LocalHost
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.executable import Executable
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.file_manager import FileManager
from assets.SelfScanModule.executable_list import search_executables


class SelfScanModule(Module):
    def __init__(self, manager, file_manager: FileManager, **kwargs):
        super(SelfScanModule, self).__init__(manager, **kwargs)

        self.filemanager = file_manager
        self.search_executables = search_executables

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """
        self._logger.info("Executing SelfScan")
        local_host = keyed_knowledge["local_host"]
        target_ips = keyed_knowledge["address"]
        ips = self.filemanager.get_local_ips()
        netmask = self.filemanager.netmask
        self._logger.info("Found ips: " + str(ips))
        ips = [IPAddress(int(ipaddress.IPv4Address(ip))) for ip in ips]
        for ip in ips:
            for target_ip in [target_ips]:
                if ip & netmask == target_ip & netmask:
                    buffered_module_manager.add_knowledge(local_host, "address", ip, 1.0)

        for executable in self.search_executables:
            if shutil.which(executable) is not None:
                buffered_module_manager.add_knowledge(local_host, "executable", Executable(executable), 1.0)

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        condition_1 = check_type(LocalHost)
        condition_2 = check_type(Target)
        condition_3 = check_type(IPAddress)
        meta = is_parent("target", ["address"])
        return {
            "get_ip_of_local_computer": (
                {"local_host": condition_1, "target": condition_2, "address": condition_3},
                meta,
            )
        }
