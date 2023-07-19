from typing import List, Tuple
import pinaht.knowledge.execution_graph as eg
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.strategies.strategy import FlagElement
import time
from collections import namedtuple


Config = namedtuple("Config", ["graph", "node", "edge"])


def backtrace_flag(flag: FlagElement, execution_graph: eg.ExecutionGraph) -> List[eg.Node]:
    if flag.priority <= 0.0 or (flag.priority > 0.0 and not flag.check()):
        return []
    node, edges = flag_to_node(flag)
    node.previous = edges

    sorting = execution_graph.topological_sorting(node, lambda node: map(lambda edge: edge.source, node.previous))
    sorting = sorted(sorting, key=lambda T: T[2])

    return list(map(lambda T: T[0], sorting))


def flag_to_node(flag: FlagElement) -> Tuple[eg.Node, List[eg.Edge]]:
    meta_key, meta_precondition, fulfilling_preconditions = flag.justification
    node = eg.Node(flag.name, [], time.time(), time.time())
    node.set_metaprecondition(meta_precondition, meta_key)

    source_dict = {
        id(source_node): {} for key, (precondition, source_node, knowledge) in fulfilling_preconditions.items()
    }
    source_lookup = {
        id(source_node): source_node
        for key, (precondition, source_node, knowledge) in fulfilling_preconditions.items()
    }
    for key, (precondition, source_node, knowledge) in fulfilling_preconditions.items():
        source_dict[id(source_node)][key] = (precondition, knowledge)

    edges = []
    for source_node_id, keyed_preconditions_knowledge in source_dict.items():
        edges.append(eg.Edge(source_lookup[source_node_id], node, keyed_preconditions_knowledge))

    return node, edges


def parse_knowledge(knowledge: Knowledge) -> str:
    if knowledge.type == "BRANCH":
        return f"{knowledge!s}"
    return f"{knowledge.__class__.__name__}"


def get_time_sorted_execution_graph(execution_graph: eg.ExecutionGraph) -> List[eg.Node]:
    return execution_graph.time_sort()


def str_to_latex(value):
    if isinstance(value, list):
        for i in range(len(value)):
            value[i] = str_to_latex(value[i])
    elif isinstance(value, str):
        replace = {
            "\\": "\\textbackslash{}",
            "_": "\\_",
            "|": "\\textbar{}",
            "$": "\\textdollar{}",
            "~": "\\textasciitilde{}",
        }
        for old, new in replace.items():
            value = value.replace(old, new)
    return value
