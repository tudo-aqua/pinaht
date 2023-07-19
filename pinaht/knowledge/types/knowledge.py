from abc import ABC, abstractmethod, ABCMeta
from enum import EnumMeta
import logging


class KnowledgeEnumMeta(ABCMeta, EnumMeta):
    pass


class Knowledge(ABC):
    """
    The Knowledge interface. It structures the behavior of knowledge.
    """

    def __init__(self, *args, **kwargs):
        super(Knowledge, self).__init__()

        self.color = "w"
        self.parent = None
        self.type = ""
        self.duality_edges = []
        self.lookup = {}
        self._logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def fuzzy_eq(self, other) -> float:
        """ """
        raise NotImplementedError()

    @abstractmethod
    def add_child(self, key, child):
        raise NotImplementedError()

    def add_duality_edge(self, edge):
        self.duality_edges.append(edge)


class RootKnowledge(Knowledge):
    def __init__(self, **kwargs):
        super(RootKnowledge, self).__init__(**kwargs)

        self.parent = None
        self.lookup = {}

    def fuzzy_eq(self, other) -> float:
        return 0.0

    def add_child(self, key, child):
        if key in self.lookup:
            self.lookup[key].append(child)
        else:
            self.lookup[key] = [child]
