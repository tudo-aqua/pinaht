from pinaht.application import Application
from pinaht.strategies.fast_strategy import FastStrategy
from pinaht.knowledge.types.generate import call_generation
from pinaht.flags.create_flag import CreateFlag
from pinaht.modules.module_list import modules
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.localhost import LocalHost
from pinaht.knowledge.types.network import Network
from pinaht.knowledge.types.netmask import NetMask
import argparse
import logging
import os


def main():
    # setup logging
    logger = logging.getLogger("__init__")
    logger.info("Starting")

    # parse command line arguments
    logger.info("Parsing command line arguments")
    parser = argparse.ArgumentParser()
    parser.add_argument("target", type=str, help="the ip address of the target")
    parser.add_argument(
        "-v",
        "--verbosity",
        help="the verbosity of the programm (0 = None, 1 = Info, 2 = Debug)",
        type=int,
        choices=[0, 1, 2],
        default=1,
    )
    parser.add_argument(
        "-g",
        "--generate",
        help="if uses generates the types instead of calling the main.py",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()

    # verbosity
    if args.verbosity == 0:
        logging.basicConfig(level=logging.CRITICAL)
    elif args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)

    # make reporting directory in working directory
    cwd = os.getcwd()
    report_dir = os.path.join(cwd, "reports")
    if (not os.path.exists(report_dir)) or (not os.path.isdir(report_dir)):
        os.mkdir(report_dir)

    # generate
    if args.generate:
        call_generation()
        exit()

    # start application
    if "/" in args.target:
        ip, mask = args.target.split("/")
        network = Network()
        mask = NetMask(mask)
        network_ip = IPAddress(IPAddress.str_to_ip(ip))
        local_host = LocalHost()

        # Man kann an dieser Stelle keinen User hinzufügen, da die targets noch nicht bekannt sind.
        # Testfälle mit präparierten Modulen (z.b. user=idiot, pw="") sind also nicht möglich/sehr schwierig

        start_knowledge = [
            (None, "network", network),
            (network, "net_mask", mask),
            (network, "address", network_ip),
            (network, "local_host", local_host),
        ]
    else:

        # An dieder Stelle können Daten hinzugefügt werden, da das target bereits bekannt ist.

        network = Network()  # keine Ntzwermaske und Netzwerk-IP, weil unbekannt.
        target = Target()
        local_host = LocalHost()
        ip = IPAddress(IPAddress.str_to_ip(args.target))

        start_knowledge = [
            (None, "network", network),
            (network, "targets", target),
            (target, "address", ip),
            (network, "local_host", local_host),
        ]

    flags = [CreateFlag]
    App = Application(FastStrategy, start_knowledge, modules, flags)  # noqa F841

    App.start()
    logger.info("Exiting")
