from typing import List
import pinaht.knowledge.execution_graph as eg
from pinaht.strategies.strategy import FlagElement
from pinaht.reporting.report_util import flag_to_node, backtrace_flag
from jinja2 import Template
from graphviz import Source
from collections import namedtuple
import os


Config = namedtuple("Config", ["graph", "node", "edge"])


def generate_execution_graph_visualization(execution_graph: eg.ExecutionGraph, flags: List[FlagElement]):
    nodes = execution_graph.bfs(execution_graph.root)

    generate_execution_sub_graph_visualization(nodes, flags).render(
        os.path.join(os.getcwd(), "reports", "execution_graph.gv")
    )


def generate_execution_path_visualization(execution_graph: eg.ExecutionGraph, flag: FlagElement):
    if flag.priority > 0.0 and flag.check():
        nodes = backtrace_flag(flag, execution_graph)[:-1]
        path = generate_execution_sub_graph_visualization(nodes, [flag]).render(
            os.path.join(os.getcwd(), "reports", f"{flag.name}_flag_execution_path.gv")
        )

        return path
    return None


def generate_execution_sub_graph_visualization(nodes: List[eg.Node], flags: List[FlagElement]):

    config = Config(
        graph={"nodesep": 1, "ranksep": 1},
        node={"fontname": "LiberationSans", "fontcolor": "black", "fontsize": 15},
        edge={"fontname": "LiberationSans", "fontcolor": "dimgray", "fontsize": 11},
    )

    edges = [
        (
            id(edge.source),
            id(edge.target),
            ",\n".join([f"{key} = {know!s}" for key, (pre, know) in edge.preconditions.items()]),
        )
        for node in nodes
        for edge in node.previous
    ]

    nodes = [
        (id(node), node.module_name, node.metaprecondition_key if node.metaprecondition_key else "None", "MODULE")
        for node in nodes
    ]

    # flag
    for flag_element in flags:
        if flag_element.priority > 0.0 and flag_element.check():
            node, node_edges = flag_to_node(flag_element)

            nodes.append(
                (
                    id(node),
                    node.module_name,
                    node.metaprecondition_key if node.metaprecondition_key else "None",
                    "FLAG",
                )
            )
            for edge in node_edges:
                edges.append(
                    (
                        id(edge.source),
                        id(edge.target),
                        ",\n".join([f"{key} = {know!s}" for key, (pre, know) in edge.preconditions.items()]),
                    )
                )

    config = {
        config._fields[i]: ",".join([f'{key}="{value!s}"' for key, value in config[i].items()])
        for i in range(len(config))
    }

    current_python_file_path = os.path.dirname(os.path.realpath(__file__))
    file = open(os.path.join(current_python_file_path, "templates", "eg_visualization.jinja"), "r")
    template = Template(file.read())
    file.close()
    return Source(template.render(config=config, edges=edges, nodes=nodes))
