from abc import ABC, abstractmethod
import logging
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from typing import Tuple, Dict
from pinaht.knowledge.dependency import Dependency
from pinaht.knowledge.manager import BufferedModuleManager
from pinaht.knowledge.types.knowledge import Knowledge


class ModuleError(Exception):
    pass


class Module(ABC):
    """
    Base class for all the modules
    """

    def __init__(self, manager, **kwargs):
        super(Module, self).__init__()
        self.estimated_time = None
        self.success_chance = None

        self.precondition_dnf_cache = None
        self.dependency = Dependency(self.precondition_dnf())

        manager.register(self.dependency)

        self._logger = logging.getLogger(self.__class__.__name__)

    def precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        if self.precondition_dnf_cache is None:
            self.precondition_dnf_cache = self._generate_precondition_dnf()

        return self.precondition_dnf_cache

    @abstractmethod
    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        raise NotImplementedError()

    @abstractmethod
    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """
        raise NotImplementedError()
