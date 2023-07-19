from typing import Tuple, Dict

from pinaht.modules.module import Module
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.shell import Shell
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.name import Name
from pinaht.knowledge.types.version import Version
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.reporting.report_util import str_to_latex


class ReconLocalService(Module):
    """
    Searches for installed services on a target system.
    Services are looked up in directory "/etc/init.d/".
    For each found service, dpkg is asked to provide the version number.

    This Module will find local services, as well as services which are visible to a nmap-scan.
    Services, which are added to the Knowledge-Tree, may be duplicates.
    """

    def __init__(self, manager, **kwargs):
        super(ReconLocalService, self).__init__(manager, **kwargs)

        self.estimated_time = 30  # dpkg-querys take some time.
        self.success_chance = 1.0

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        1. make sure, dpkg is installed
        2. execute command
        3. write each service and version number into buffered_module_manager.
        """

        if meta_key == "has_shell":  # Key from Meta-Precondition
            self._logger.info("Executing recon_local-service Module.")
            shell = keyed_knowledge["shell"]
            target = keyed_knowledge["target"]

            # 1. Check, if dpkg is installed
            if not len(shell.execute("which dpkg")) > 0:
                self._logger.error("dpkg is not installed on target system. Aborting.")
                return

            # 2.  execute command
            command_full = (
                "for pkg in $("
                "for file in /etc/init.d/* ; do "
                "dpkg -S $file | awk -F: '{ print $1 }' ; "
                "done | sort | uniq) ; do "
                "echo \"$pkg `dpkg-query -W -f='${Version}' $pkg`\" ; "
                "done"
            )

            buffered_module_manager.report("Executing command to find local services.")
            shout = shell.execute(  # this can take some time, depending on number of services
                command_full, timeout=100
            )
            buffered_module_manager.report(str(len(shout)) + " Services were found: (Name, Version)")

            # 3. write each service and version number into buffered_module_manager.
            for i in range(0, len(shout)):
                name, version = shout[i].replace("\r", "").replace("\n", "").split()

                version = Version(Version.parse_version(version))

                service = Service()
                buffered_module_manager.add_knowledge(target, "services", service, 1.0)
                buffered_module_manager.add_knowledge(service, "service_name", Name(name), 1.0)
                buffered_module_manager.add_knowledge(service, "service_version", version, 1.0)

                buffered_module_manager.report(
                    f"   {i + 1}: \\code{{{str_to_latex(name)}}}, \\code{{{str_to_latex(version)}}}"
                )

        else:
            self._logger.error("Wrong meta Key. recon_local-service Module not implemented properly.")

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Needs a shell to execute it's command.
        Needs a Target, to which the services belong. (A point to hang in a new service in Knowledge-Tree)
        Shell must be a child of the target, to make sure new services belong to correct target.
        """
        pre_shell = check_type(Shell)
        pre_target = check_type(Target)

        return {"has_shell": ({"shell": pre_shell, "target": pre_target}, is_parent("target", ["shell"]))}
