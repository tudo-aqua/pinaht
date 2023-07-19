from typing import List, Dict, Tuple, Callable, Iterable
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.types.knowledge import Knowledge
import time


class Node:
    """
    A node represants an execution of a module and the knowledge gained by it.
    """

    def __init__(self, module_name: str, module_doc: [str], timestamp_start: float, timestamp_end: float):
        self.timestamp_end = timestamp_end
        self.timestamp_start = timestamp_start
        self.module_name = module_name
        self.module_doc = module_doc
        self.metaprecondition = None
        self.metaprecondition_key = None
        self.next = []  # type: List[Edge]
        self.previous = []  # type: List[Edge]
        self.color = "w"  # necessary for some graph algorithms
        self.duality_edges = []

    def add_duality_edge(self, edge):
        self.duality_edges.append(edge)

    def set_metaprecondition(self, metaprecondition: MetaPrecondition, metaprecondition_key: str):
        self.metaprecondition = metaprecondition
        self.metaprecondition_key = metaprecondition_key

    def metaprecondition_is_set(self):
        if self.metaprecondition is None or self.metaprecondition_key is None:
            return False
        return True

    def __str__(self):
        return f"({self.module_name}, {self.metaprecondition_key}, {self.timestamp_start})"


class Edge:
    """
    An edge is the directed connection between nodes.
    It contains the preconditions (knowledge) from the source that the were necessary to execute the target.
    """

    def __init__(self, source: Node, target: Node, preconditions: Dict[str, Tuple[Precondition, Knowledge]]):
        self.source = source
        self.target = target
        self.preconditions = preconditions

    def __str__(self):
        return f"[{self.source} -> {self.target}]"


class ExecutionGraph:
    """
    Contains execution Nodes. The Graph is directed an acyclic.
    """

    def __init__(self):
        """
        constructor of the graph
        """

        self.root = Node("init", [], time.time(), time.time())

    def draw_edge(
        self, source: Node, target: Node, preconditions_knowledge: Dict[str, Tuple[Precondition, Knowledge]]
    ):
        """ """
        edge = Edge(source, target, preconditions_knowledge)
        source.next.append(edge)
        target.previous.append(edge)

    def bfs(
        self, start: Node, next: Callable[[Node], Iterable[Node]] = lambda u: [e.target for e in u.next]
    ) -> List[Node]:
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

        return L

    def topological_sorting(self, start: Node, next: Callable[[Node], Iterable[Node]]) -> List[Node]:
        L = []  # noqa N806

        def visit(node: Node, i: int):
            if node.color == "b":
                return i
            if node.color == "g":
                raise TypeError("EG is not acyclic")
            node.color = "g"
            i += 1
            start = i
            for v in next(node):
                i = visit(v, i)
            node.color = "b"
            i += 1
            L.append([node, start, i])
            return i

        visit(start, 0)

        for n in L:
            n[0].color = "w"

        return L

    def time_sort(self):
        """
        sort the graph, by time a module was executed.
        """

        bfs_list = self.bfs(self.root)

        return sorted(bfs_list, key=lambda n: n.timestamp_end)
