from pinaht.knowledge.types.knowledge import Knowledge, RootKnowledge
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from typing import Tuple, Dict, Callable, Iterable, List
import pinaht.util as util
from itertools import product
import numpy as np


class KnowledgeGraph:
    def __init__(self):
        self.root = RootKnowledge()
        self.changed = True
        self.bfs_catch = None

    def add_knowledge(self, parent: Knowledge, key: str, knowledge: Knowledge):
        if parent is None:
            knowledge.parent = self.root
            self.root.add_child(key, knowledge)
        else:
            knowledge.parent = parent
            parent.add_child(key, knowledge)
        self.changed = True

    def query(
        self,
        q: Tuple[Dict[str, Precondition], MetaPrecondition],
        evaluation: Callable[[float, dict], float] = lambda T: T[0] * min([value for name, value in T[1].items()]),
        choose_function: Callable[[Iterable], int] = lambda I: np.argmax(I),  # noqa: E741
    ):

        bfs_flatted_knowledge = self.bfs(
            self.root, lambda u: util.list_flatt([entry for name, entry in u.lookup.items()])
        )
        preconditions, meterprecondition = q
        precondition_catch = {name: [] for name in preconditions}
        precondition_names = [name for name in preconditions]

        for k in bfs_flatted_knowledge:
            for name, prec in preconditions.items():
                if prec.holds(k) > 0:
                    precondition_catch[name].append(k)

        list_of_kwargs = list(
            map(
                lambda T: {precondition_names[i]: T[i] for i in range(len(T))},
                product(*map(lambda p: precondition_catch[p], precondition_catch)),
            )
        )

        position = choose_function(
            map(
                evaluation,
                zip(
                    [meterprecondition.holds(**kwargs) for kwargs in list_of_kwargs],
                    [
                        {name: preconditions[name].holds(value) for name, value in kwargs.items()}
                        for kwargs in list_of_kwargs
                    ],
                ),
            )
        )

        return list_of_kwargs[position]

    def bfs(self, start: Knowledge, next: Callable[[Knowledge], Iterable[Knowledge]]) -> List[Knowledge]:
        if not self.changed:
            return self.bfs_catch

        Q = []  # noqa N806
        L = []  # noqa N806
        start.color = "g"
        Q.append(start)

        while Q:
            u = Q.pop(0)
            L.append(u)
            u.color = "b"
            for v in next(u):
                if v.color == "w":
                    v.color = "g"
                    Q.append(v)

        for v in L:
            v.color = "w"

        self.bfs_catch = L
        return L
