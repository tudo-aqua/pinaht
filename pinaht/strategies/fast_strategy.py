from pinaht.strategies.strategy import Strategy, NoPriorityError
from typing import Dict, List, Tuple
from pinaht.knowledge import knowledge_graph as kg
from pinaht.knowledge import execution_graph as eg
from pinaht.modules.module import Module
from pinaht.flags.flag import Flag
from pinaht.knowledge.types.knowledge import Knowledge
from functools import reduce
import numpy as np


class FastStrategy(Strategy):
    def __init__(
        self,
        modules: Dict[str, Module],
        flags: Dict[str, Flag],
        knowledge_graph: kg.KnowledgeGraph,
        execution_graph: eg.ExecutionGraph,
        **kwargs,
    ):
        super(FastStrategy, self).__init__(modules, flags, knowledge_graph, execution_graph, **kwargs)

    def calc_priority(
        self, satisfying_knowledge: List[Tuple[str, float, Dict[str, Tuple[float, Knowledge]]]]
    ) -> Tuple[str, Dict[str, Tuple[Knowledge, eg.Node]], float]:
        """
        calc_priority calculates the priority of a given module

        :return: a tuple of the meta_key, fulfilling knowledge (with keys and the actual node) and the priority
        """

        priorities = [
            meta_certainty * reduce(lambda x, y: x * y, map(lambda key: key_grouping[key][0], key_grouping))
            for meta_key, meta_certainty, key_grouping in satisfying_knowledge
        ]
        if len(priorities) > 0:
            index = np.argmax(priorities)

            meta_key, certainty, key_grouping = satisfying_knowledge[index]
            keyed_knowledge = {key: knowledge for key, (certainty, knowledge) in key_grouping.items()}

            concrete_keyed_knowledge = {}
            for key, knowledge in keyed_knowledge.items():
                concrete_keyed_knowledge[key] = (knowledge, knowledge.duality_edges[-1].node)

            return meta_key, concrete_keyed_knowledge, priorities[index]
        else:
            raise NoPriorityError()
