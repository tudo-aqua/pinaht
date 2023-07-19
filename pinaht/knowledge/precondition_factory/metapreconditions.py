from typing import Iterable, Callable, List
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.precondition import MetaPrecondition
import numpy as np


def id_aggregation_function(knowledge: Iterable[Knowledge]) -> float:
    knowledge = list(knowledge)
    if all(map(lambda x: id(x) == id(knowledge[0]), knowledge)):
        return 1.0
    return 0.0


def static(precondition_keys: Iterable[str], value: float = 1.0) -> MetaPrecondition:
    precondition_keys = set(precondition_keys)

    class CheckMetaPrecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(CheckMetaPrecondition, self).__init__(**kwargs)

        def holds(self, **kwargs) -> float:
            return value

    return CheckMetaPrecondition()


def identical_parents(
    precondition_keys: Iterable[str],
    depth: int = 1,
    aggregation_function: Callable[[Iterable[Knowledge]], float] = id_aggregation_function,
) -> MetaPrecondition:
    precondition_keys = set(precondition_keys)

    class CheckMetaPrecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(CheckMetaPrecondition, self).__init__(**kwargs)

        def holds(self, **kwargs) -> float:
            knowledge = list(map(lambda key: kwargs[key], precondition_keys))

            for i in range(depth):
                for j in range(len(knowledge)):
                    if knowledge[j].parent is None:
                        return 0.0
                    else:
                        knowledge[j] = knowledge[j].parent

            return aggregation_function(knowledge)

    return CheckMetaPrecondition()


def identical_knowledge(
    precondition_keys: Iterable[str],
    aggregation_function: Callable[[Iterable[Knowledge]], float] = id_aggregation_function,
) -> MetaPrecondition:
    return identical_parents(precondition_keys, 0, aggregation_function)


def identical_ancestors(precondition_keys: Iterable[str]):
    precondition_keys = set(precondition_keys)

    class CheckMetaPrecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(CheckMetaPrecondition, self).__init__(**kwargs)

        def holds(self, **kwargs) -> float:
            knowledge = list(map(lambda key: kwargs[key], precondition_keys))

            minimum = np.inf
            maximum = 0
            for i in range(len(knowledge)):
                current_knowledge = knowledge[i]
                knowledge_list = [current_knowledge]
                while current_knowledge.parent is not None:
                    current_knowledge = current_knowledge.parent
                    knowledge_list.append(current_knowledge)
                knowledge[i] = list(map(lambda x: id(x), knowledge_list))
                knowledge[i].reverse()
                minimum = min(minimum, len(knowledge[i]))
                maximum = max(maximum, len(knowledge[i]))

            matrix = np.zeros((len(knowledge), maximum)) + np.inf
            for i in range(len(knowledge)):
                for j in range(len(knowledge[i])):
                    matrix[i, j] = knowledge[i][j]

            matrix = np.transpose(matrix)
            n, d = matrix.shape
            depth = 0
            for i in range(n):
                if all(matrix[i, :] == np.array([matrix[i, 0]] * d)):
                    depth = i
                else:
                    break

            temp = (minimum - depth - 1) + (maximum - depth - 1)
            temp /= 2 * (n - 1)
            temp = 1.0 - temp

            return temp

    return CheckMetaPrecondition()


def merge(metapreconditions: List[MetaPrecondition], f: Callable[[Iterable[float]], float] = min) -> MetaPrecondition:
    assert len(metapreconditions) > 0

    class MergeMetaPrecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(MergeMetaPrecondition, self).__init__(**kwargs)

        def holds(self, **kwargs):
            return f(map(lambda meta: meta.holds(**kwargs), metapreconditions))

    return MergeMetaPrecondition()


def invert(metaprecondition: MetaPrecondition) -> MetaPrecondition:
    class InverseMetaPrecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(InverseMetaPrecondition, self).__init__(**kwargs)

        def holds(self, **kwargs):
            return 1 - metaprecondition.holds(**kwargs)

    return InverseMetaPrecondition()


def is_parent(parent_key: str, children_keys: Iterable[str], max_depth=1) -> MetaPrecondition:
    children_keys = set(children_keys)

    class ParentMetaPrecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(ParentMetaPrecondition, self).__init__(**kwargs)

        def holds(self, **kwargs):
            knowledge = list(map(lambda key: kwargs[key], children_keys))
            parent = kwargs[parent_key]

            for i in range(len(knowledge)):
                ancestors = [knowledge[i]]
                for j in range(max_depth):
                    current = ancestors[-1]
                    if current.parent is not None:
                        ancestors.append(current.parent)
                if not any([id(a) == id(parent) for a in ancestors]):
                    return 0.0

            return 1.0

    return ParentMetaPrecondition()


def check_empty_child(parent_key: str, children_key: str) -> MetaPrecondition:
    class CheckPrecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(CheckPrecondition, self).__init__(**kwargs)

        def holds(self, **kwargs) -> float:
            knowledge = kwargs[parent_key]

            if children_key in knowledge.lookup:
                return 0.0 if len(knowledge.lookup[children_key]) > 0 else 1.0
            return 0.0

    return CheckPrecondition()
