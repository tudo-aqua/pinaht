from typing import Tuple, Dict
from pinaht.modules.module import Module
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser
from libnmap.objects.host import NmapHost
from libnmap.objects.service import NmapService
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.name import Name
from pinaht.knowledge.types.status import Status
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.port import Port
from pinaht.knowledge.types.version import Version
from pinaht.knowledge.types.protocol import Protocol
from pinaht.knowledge.types.transport import Transport
from pinaht.knowledge.types.network import Network
from pinaht.knowledge.types.netmask import NetMask
from pinaht.knowledge.types.operatingsystemtype import OperatingSystemType
from pinaht.knowledge.types.os import OS
from pinaht.knowledge.types.info import Info
from pinaht.knowledge.types.script import Script
from pinaht.knowledge.types.scriptelement import ScriptElement
from pinaht.knowledge.types.text import Text
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.manager import BufferedModuleManager
from functools import reduce
from pinaht.util import list_str
from pinaht.reporting.report_util import str_to_latex


class NmapModule(Module):
    def __init__(self, manager, **kwargs):
        super(NmapModule, self).__init__(manager, **kwargs)

        self.estimated_time = 0.01
        self.success_chance = 1.0

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """
        if meta_key == "nmap_target_with_ip":
            self.execute_target_scan(buffered_module_manager, **keyed_knowledge)
        if meta_key == "nmap_network":
            self.execute_network_scan(buffered_module_manager, **keyed_knowledge)

    def execute_network_scan(self, buffered_module_manager, network, mask, ip):
        buffered_module_manager.report(
            f"""Starting nmap networkscan on \\code{{{ip!s}/{mask!s}}} with command:
            \\code{{sudo nmap -sn {ip!s}/{mask!s}}}"""
        )
        scanner = NmapProcess(f"{ip!s}/{mask!s}", options="-sn")
        scanner.sudo_run()

        if scanner.has_failed():
            stderr = str.split(scanner.stderr, sep="\n")[0]
            buffered_module_manager.report(f"Nmap scan failed due to {str_to_latex(str(stderr))}.")
            self._logger.info(f"Nmap failed to run. The reason is: {stderr!s} Trying again.")
            buffered_module_manager.report(f"Retrying nmap networkscan with sudo option: \\code{{nmap -sn {ip!s}}}")
            scanner = NmapProcess(str(ip), options="-sn")
            scanner.run()

        if scanner.is_successful():
            report = NmapParser.parse(scanner.stdout)
            targets = list(
                map(lambda h: IPAddress(IPAddress.str_to_ip(h.address)), filter(lambda h: h.is_up(), report.hosts))
            )
            known_target = list(
                reduce(lambda A, B: A + B, map(lambda t: t.address, filter(lambda t: t.address, network.targets)), [])
            )
            local_host_ip = list(
                reduce(
                    lambda A, B: A + B, map(lambda h: h.address, filter(lambda h: h.address, network.local_host)), []
                )
            )

            for ip in known_target:
                if ip in targets:
                    targets.remove(ip)
            for ip in local_host_ip:
                if ip in targets:
                    targets.remove(ip)

            for ip in targets:
                buffered_module_manager.report(f"Target \\code{{{ip!s}}} has been found.")
                target = Target(address=ip)
                buffered_module_manager.add_knowledge(network, "targets", target, 1.0, True)

        else:
            stderr = str.split(scanner.stderr, sep="\n")[0]
            buffered_module_manager.report(
                f"Nmap failed to run. The reason is: \\code{{{str_to_latex(str(stderr))}}}."
            )
            self._logger.info(f"Nmap failed to run. The reason is: {stderr!s} Exiting")

    def execute_target_scan(self, buffered_module_manager: BufferedModuleManager, target, ip):
        buffered_module_manager.report(
            f"Starting nmap portscan with call: \\code{{sudo nmap --version-all -sC -A -sS -O -T4 {ip!s}}}."
        )
        scanner = NmapProcess(str(ip), options="--version-all -sC -A -sS -O -T4")
        scanner.sudo_run()

        if scanner.has_failed():
            stderr = str.split(scanner.stderr, sep="\n")[0]
            buffered_module_manager.report(f"Nmap scan failed due to \\code{{{str_to_latex(str(stderr))}}}.")
            self._logger.info(f"Nmap failed to run. The reason is: {stderr!s} Trying again.")
            scanner = NmapProcess(str(ip), options="-A")
            buffered_module_manager.report(f"Retrying nmap portscan with less option: \\code{{nmap -A {ip!s}}}")
            scanner.run()

        if scanner.is_successful():
            buffered_module_manager.report("Nmap scan successful executed.")
            report = NmapParser.parse(scanner.stdout)
            for host in report.hosts:
                host_ip = IPAddress(IPAddress.str_to_ip(host.ipv4))
                if ip == host_ip:
                    self.scan_host(buffered_module_manager, target, ip, host)

        else:
            stderr = str.split(scanner.stderr, sep="\n")[0]
            buffered_module_manager.report(f"Nmap scan failed due to \\code{{{str_to_latex(str(stderr))}}}.")
            self._logger.info(f"Nmap failed to run. The reason is: {stderr!s} Exiting")

    def scan_host(self, buffered_module_manager: BufferedModuleManager, target, ip, host: NmapHost):
        hostnames = host.hostnames
        if len(hostnames) == 0:
            buffered_module_manager.report("Nmap scan detected new host without name.")
        elif len(hostnames) == 1:
            buffered_module_manager.report(
                f"Nmap scan detected new host with name \\code{{{str_to_latex(str(hostnames[0]))}}}."
            )
        else:
            buffered_module_manager.report(
                f"Nmap scan detected new host with names \\code{{{str_to_latex(', '.join(str(hostnames)))}}}."
            )

        for hostname in hostnames:
            buffered_module_manager.add_knowledge(target, "hostname", Name(hostname), 1.0)

        if host.status == "up":
            buffered_module_manager.report("Host status is UP.")
            buffered_module_manager.add_knowledge(target, "status", Status.UP, 1.0)
        elif host.status == "down":
            buffered_module_manager.report("Host status is DOWN.")
            buffered_module_manager.add_knowledge(target, "status", Status.DOWN, 1.0)
        else:
            buffered_module_manager.report("Host status is unknown.")
            buffered_module_manager.add_knowledge(target, "status", Status.UNKNOWN, 0.8)

        for os_class in host.os_class_probabilities():
            os_version = Version(Version.parse_version(os_class.osgen))
            os = OS(expected_version=os_version)
            if "windows" in str.lower(os_class.osfamily):
                buffered_module_manager.report(
                    f"""Host runs on windows version \\code{{{os_version}}}
                    with accuracy \\code{{{os_class.accuracy / 100}}}."""
                )
                os.add_child("os_type", OperatingSystemType.WINDOWS)
            elif "linux" in str.lower(os_class.osfamily):
                buffered_module_manager.report(
                    f"""Host runs on linux version \\code{{{os_version}}}
                    with accuracy \\code{{{os_class.accuracy / 100}}}."""
                )
                os.add_child("os_type", OperatingSystemType.LINUX)
            elif "bsd" in str.lower(os_class.osfamily):
                buffered_module_manager.report(
                    f"""Host runs on BSD version \\code{{{os_version}}}
                    with accuracy \\code{{{os_class.accuracy / 100}}}."""
                )
                os.add_child("os_type", OperatingSystemType.BSD)
            elif "os" in str.lower(os_class.osfamily) and "2" in str.lower(os_class.osfamily):
                buffered_module_manager.report(
                    f"""Host runs on OS2 version \\code{{{os_version}}}
                    with accuracy \\code{{{os_class.accuracy / 100}}}."""
                )
                os.add_child("os_type", OperatingSystemType.OS_2)

            buffered_module_manager.add_knowledge(target, "os", os, os_class.accuracy / 100, True)

        for service in host.services:
            buffered_module_manager.add_knowledge(
                target, "services", self.service_scan(buffered_module_manager, service), 0.99, True
            )

    def service_scan(self, buffered_module_manager: BufferedModuleManager, nmap_service: NmapService):
        service = Service()

        if nmap_service.port is not -1:
            service.add_child("port", Port(nmap_service.port))

        if "name" in nmap_service.service_dict:
            service.add_child("protocol", Protocol(name=Name(nmap_service.service_dict["name"])))

        if "product" in nmap_service.service_dict:
            service.add_child("service_name", Name(nmap_service.service_dict["product"]))

        if "extrainfo" in nmap_service.service_dict:
            service.add_child("extrainfo", Info(nmap_service.service_dict["extrainfo"]))

        if "udp" in str.lower(nmap_service.protocol):
            service.add_child("transport", Transport.UDP)
        elif "tcp" in str.lower(nmap_service.protocol):
            service.add_child("transport", Transport.TCP)
        elif "dtls" in str.lower(nmap_service.protocol):
            service.add_child("transport", Transport.DTLS)
        elif "sctp" in str.lower(nmap_service.protocol):
            service.add_child("transport", Transport.SCTP)
        elif "tls" in str.lower(nmap_service.protocol):
            service.add_child("transport", Transport.TLS)

        for cpe in nmap_service.cpelist:
            if cpe is not None:
                version = Version(Version.parse_version(cpe.get_version()))
                service.add_child("service_version", version)

        if "open" in str.lower(nmap_service.state):
            service.add_child("status", Status.OPEN)
        elif "close" in str.lower(nmap_service.state):
            service.add_child("status", Status.CLOSED)
        else:
            service.add_child("status", Status.UNKNOWN)

        for script in nmap_service.scripts_results:
            service.add_child("extrainfo", self.script_parser(**script))

        buffered_module_manager.report(
            f"""New service \\code{{{str_to_latex(list_str(service.service_name))}}} on Host
            in version \\code{{{str_to_latex(list_str(service.service_version))}}} on Port
            \\code{{{str_to_latex(list_str(service.port))}}} detected."""
        )
        return service

    def script_parser(self, id, output, elements):
        script = Script(id=Name(id), output=Text(output))
        for key, value in elements.items():
            script.add_child("elements", ScriptElement(id=Name(key), output=Text(value)))

        return script

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        return {
            "nmap_target_with_ip": (
                {"target": check_type(Target), "ip": check_type(IPAddress)},
                is_parent("target", ["ip"]),
            ),
            "nmap_network": (
                {"network": check_type(Network), "mask": check_type(NetMask), "ip": check_type(IPAddress)},
                is_parent("network", ["mask", "ip"]),
            ),
        }
