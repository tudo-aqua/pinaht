from enum import Enum
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge import execution_graph as eg


class DualityEdgeType(Enum):
    ADD = 0
    UPDATE = 1


class DualityEdge:
    def __init__(
        self, knowledge: Knowledge, node: eg.Node, certainty: float, duality_edge_type: DualityEdgeType, **kwargs
    ):
        super(DualityEdge, self).__init__(**kwargs)
        self.knowledge = knowledge
        self.node = node
        self.certainty = certainty
        self.duality_edge_type = duality_edge_type

        self.knowledge.add_duality_edge(self)
        self.node.add_duality_edge(self)
