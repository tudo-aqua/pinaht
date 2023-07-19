from typing import List, Tuple
from pinaht.knowledge import knowledge_graph as kg
from pinaht.knowledge import execution_graph as eg
from pinaht.file_manager import FileManager
from pinaht.knowledge.manager import Manager, BufferedModuleManager
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.duality_edge import DualityEdgeType
from pinaht.modules.module import Module, ModuleError
from pinaht.flags.flag import Flag
from pinaht.strategies.strategy import NoPriorityError
from pinaht.reporting.execution_graph_visualization import generate_execution_graph_visualization

from pinaht.reporting.report import generate_report
import logging
import time
import pinaht.util as util
from graphviz import Source
import os
import ipaddress


class Application:
    """
    Main class managing the program flow
    """

    def __init__(
        self,
        strategy_class,
        start_knowledge: List[Tuple[Knowledge, str, Knowledge]],
        modules: List[Module],
        flags: List[Flag],
    ):
        """
        the entry point of the application.

        :param strategy: the Strategy, which the programme follows
        :param start_knowledge: a list of knowledge pairs (parent, knowledge), that is initially known
        """
        self._logger = logging.getLogger("Application")
        self._logger.info("init pinaht main...")

        self.execution_graph = eg.ExecutionGraph()
        self.knowledge_graph = kg.KnowledgeGraph()
        self.manager = Manager(self.knowledge_graph, self.execution_graph)
        self.file_manager = FileManager(int(ipaddress.IPv4Address("255.255.255.0")))
        self.file_manager.start_server()
        self.start_time = None
        self.end_time = None

        # init all the modules
        kwargs = {"manager": self.manager, "file_manager": self.file_manager}
        self.modules = {module.__name__: module(**kwargs) for module in modules}  # a dict of all modules
        self.flags = {flag.__name__: flag(**kwargs) for flag in flags}  # a dict of all flags

        self.strategy = strategy_class(self.modules, self.flags, self.knowledge_graph, self.execution_graph)

        for parent, key, knowledge in start_knowledge:
            self.manager.add_knowledge(parent, key, knowledge)
            self.manager.notify(knowledge)

            self.manager.draw_duality_edge(knowledge, self.execution_graph.root, 0.99, DualityEdgeType.ADD)
            if parent is not None:
                self.manager.draw_duality_edge(parent, self.execution_graph.root, 0.99, DualityEdgeType.ADD)

                if knowledge.type == "BRANCH":
                    self.execution_graph.root.module_doc.append(f"{parent!s} has a {knowledge!s}.")
                else:
                    self.execution_graph.root.module_doc.append(
                        f"{parent!s} has a {knowledge.__class__.__name__} with value: {knowledge!s}."
                    )
            else:
                if knowledge.type == "BRANCH":
                    self.execution_graph.root.module_doc.append(f"we know that {knowledge!s} exists.")
                else:
                    self.execution_graph.root.module_doc.append(
                        f"we find {knowledge.__class__.__name__} with value: {knowledge!s}."
                    )

    def start(self):
        """
        starts the app loop
        """

        self.start_time = time.time()
        self._logger.info(
            f"start with execution at {util.formated_time(self.start_time)} "
            + f"on {util.formated_date(self.start_time)} local time:"
        )

        while not self.strategy.finished():
            try:
                self._logger.info("strategy starts evaluating next module...")
                module_name, module, priority, meta_key, keyed_knowledge, justification = self.strategy.next()
                self._logger.debug(list(map(lambda e: (e.name, e.priority), self.strategy.strategy_elements)))
                self._logger.info(f"next module is {module_name}, with priority {priority}")

                buffered_module_manager = BufferedModuleManager(module_name, time.time())
                module.execute(buffered_module_manager, meta_key, keyed_knowledge)
                buffered_module_manager.add_timestamp_end(time.time())
                self.manager.add_module(buffered_module_manager, justification)

            except ModuleError:
                self._logger.info("an error occurred in the module, ignoring")
                self.strategy.update_all()

            except NoPriorityError:
                self._logger.info("no more modules that can be executed!")
                self._logger.info("stop execution")
                self._logger.debug(list(map(lambda e: (e.name, e.priority), self.strategy.strategy_elements)))
                break

        self.end_time = time.time()
        self._logger.info(
            f"ended with execution at {util.formated_time(self.end_time)} "
            + f"on {util.formated_date(self.end_time)} local time:"
        )

        self.file_manager.shutdown_server()

        # visualization
        generate_execution_graph_visualization(self.execution_graph, self.strategy.flags)
        visualization_str = self.manager.gen_visualization()
        dot = Source(visualization_str)
        cwd = os.getcwd()
        dot.render(os.path.join(cwd, "reports", "knowledge_graph.gv"))

        generate_report(self.knowledge_graph, self.execution_graph, self.strategy.flags, f"{os.getcwd()}/reports")

        duration = self.end_time - self.start_time
        self._logger.info(f"the execution took {util.formated_duration(duration)}")
