from typing import Dict, List, Tuple
from enum import Enum
from abc import ABC, abstractmethod
from pinaht.knowledge import knowledge_graph as kg
from pinaht.knowledge import execution_graph as eg
from pinaht.modules.module import Module
from pinaht.flags.flag import Flag
from pinaht.knowledge.types.knowledge import Knowledge
import logging


class State(Enum):
    SUCCESSFUL = 0
    INTERRUPTED = 1
    UNSOLVED = 2
    RUNNING = 3


class NoPriorityError(Exception):
    pass


class StrategyElement:
    def __init__(self, name: str, module: Module):
        self.name = name
        self.module = module
        self.priority = 0.0
        self.meta_key = ""
        self.keyed_knowledge = {}
        self.justification = ()


class FlagElement(StrategyElement):
    def __init__(self, name: str, flag: Flag):
        super().__init__(name, flag)
        self.flag = flag

    def check(self) -> bool:
        return self.flag.check(self.meta_key, self.keyed_knowledge)


class Strategy(ABC):
    """
    The abstract Strategy class defines the general behavior of a strategy
    """

    def __init__(
        self,
        modules: Dict[str, Module],
        flags: Dict[str, Flag],
        knowledge_graph: kg.KnowledgeGraph,
        execution_graph: eg.ExecutionGraph,
        **kwargs,
    ):
        super(Strategy, self).__init__(**kwargs)
        self._logger = logging.getLogger(self.__class__.__name__)
        self.knowledge_graph = knowledge_graph
        self.execution_graph = execution_graph
        self.strategy_elements = [StrategyElement(name, module) for name, module in modules.items()]
        self.flags = [FlagElement(name, flag) for name, flag in flags.items()]
        self.iter = 0
        self.state = State.RUNNING

    def next(self):
        self.update(self.strategy_elements)

        # normalizing and max
        s = sum(map(lambda strategy_element: strategy_element.priority, self.strategy_elements))
        s = 1 if s == 0 else s

        max_strategy_element = self.strategy_elements[0]
        for strategy_element in self.strategy_elements:
            strategy_element.priority /= s
            if strategy_element.priority > max_strategy_element.priority:
                max_strategy_element = strategy_element

        if max_strategy_element.priority == 0.0:
            self.state = State.UNSOLVED
            raise NoPriorityError()

        # notifies the dependency which keyed_knowledge has already been used
        max_strategy_element.module.dependency.add_executed(
            max_strategy_element.meta_key, max_strategy_element.keyed_knowledge
        )
        return (
            max_strategy_element.name,
            max_strategy_element.module,
            max_strategy_element.priority,
            max_strategy_element.meta_key,
            max_strategy_element.keyed_knowledge,
            max_strategy_element.justification,
        )

    def update_all(self):
        self.update(self.strategy_elements)
        self.update(self.flags)

    def update(self, element_list: List[StrategyElement]):
        for strategy_element in element_list:
            if strategy_element.module.dependency.updated:
                satisfying_knowledge = strategy_element.module.dependency.resolve()
                try:
                    meta_key, keyed_knowledge_node, priority = self.calc_priority(satisfying_knowledge)

                    # extract keyed_knowledge and justification
                    keyed_knowledge = {}
                    fulfilling_preconditions = {}
                    for key, (knowledge, node) in keyed_knowledge_node.items():
                        keyed_knowledge[key] = knowledge
                        fulfilling_preconditions[key] = (
                            strategy_element.module.dependency.preconditions[key],
                            node,
                            keyed_knowledge[key],
                        )

                    strategy_element.priority = priority
                    strategy_element.meta_key = meta_key
                    strategy_element.keyed_knowledge = keyed_knowledge
                    strategy_element.justification = (
                        meta_key,
                        strategy_element.module.dependency.precondition_dnf[meta_key][1],
                        fulfilling_preconditions,
                    )
                    strategy_element.module.dependency.updated = False

                except NoPriorityError:
                    strategy_element.priority = 0.0
                    strategy_element.meta_key = ""
                    strategy_element.module.dependency.updated = False

    def finished(self, max_iter: int = 10 ** 5) -> bool:
        if self.iter > max_iter:
            self._logger.info(f"Strategy finished because the max iterations of {max_iter} have been reached.")
            self.state = State.INTERRUPTED
            return True
        self.iter += 1
        self.update(self.flags)
        if all(map(lambda flag: flag.priority > 0.0, self.flags)):
            if all([flag_element.check() for flag_element in self.flags]):
                self._logger.info("Strategy finished because all Flags have been found.")
                self.state = State.SUCCESSFUL
                return True
        return False

    @abstractmethod
    def calc_priority(
        self, satisfying_knowledge: List[Tuple[str, float, Dict[str, Tuple[float, Knowledge]]]]
    ) -> Tuple[str, Dict[str, Tuple[Knowledge, eg.Node]], float]:
        """
        calc_priority calculates the priority of a given module

        :return: a tuple of the meta_key, fulfilling knowledge (with keys and the actual node) and the priority
        """

        raise NotImplementedError()
