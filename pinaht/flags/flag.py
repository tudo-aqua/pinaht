from abc import abstractmethod
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from typing import Tuple, Dict
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.modules.module import Module
from pinaht.knowledge.types.knowledge import Knowledge


class Flag(Module):
    """
    Base class for all the Flags
    """

    def __init__(self, manager, **kwargs):
        super(Flag, self).__init__(manager, **kwargs)

        self.estimated_time = 0.1 ** 10
        self.success_chance = 1

    def precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        if self.precondition_dnf_cache is None:
            self.precondition_dnf_cache = self._generate_precondition_dnf()

        return self.precondition_dnf_cache

    @abstractmethod
    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        raise NotImplementedError()

    @abstractmethod
    def check(self, meta_key: str, keyed_knowledge: Dict[str, Knowledge]) -> bool:
        """
        checks for the flag
        """
        raise NotImplementedError()

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """
        self.check(meta_key, keyed_knowledge)

    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError()
