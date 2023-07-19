from typing import Tuple, Dict
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge import knowledge_graph as kg
from pinaht.knowledge import execution_graph as eg
from pinaht.knowledge.duality_edge import DualityEdge, DualityEdgeType
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.observer_pattern import Observable, Event
import numpy as np
import functools as ft
import jinja2 as ji2
import string
import logging
from pinaht.knowledge.types.generate import get_types_obj, check_model_consistency
import os


class BufferedModuleManager:
    def __init__(self, module_name: str, timestamp_start: float):
        self.node = eg.Node(module_name, ["Module not finished"], timestamp_start, np.inf)
        self.add_knowledge_buffer = []
        self.update_knowledge_buffer = []
        self.log_list = []
        self._logger = logging.getLogger(f"{self.__class__.__name__!s}_{module_name!s}")

    def report(self, input: str):
        self._logger.debug(f"{input}")
        self.log_list.append(input)

    def add_timestamp_end(self, timestamp: float):
        self.node.timestamp_end = timestamp

    def add_knowledge(
        self, parent: Knowledge, key: str, knowledge: Knowledge, certainty: float, recursive: bool = False
    ):
        if certainty < 0.0 or certainty > 1.0:
            raise ValueError("certainty must be in interval [0,1]")

        self.add_knowledge_buffer.append((parent, key, knowledge, certainty, recursive))

    def update_knowledge(self, knowledge: Knowledge, certainty: float):
        if certainty < 0.0 or certainty > 1.0:
            raise ValueError("certainty must be in interval [0,1]")

        self.update_knowledge_buffer.append((knowledge, certainty))


class Manager(Observable):
    def __init__(self, knowledge_graph: kg.KnowledgeGraph, execution_graph: eg.ExecutionGraph):
        super(Manager, self).__init__()
        self.knowledge_graph = knowledge_graph
        self.execution_graph = execution_graph

    def add_knowledge(self, parent: Knowledge, key: str, knowledge: Knowledge, eq_certainty: float = 1.0):
        self.knowledge_graph.add_knowledge(parent, key, knowledge)

    def add_node(
        self,
        node: eg.Node,
        justification: Tuple[str, MetaPrecondition, Dict[str, Tuple[Precondition, eg.Node, Knowledge]]],
    ):
        metaprecondition_key, metaprecondition, fulfilling_preconditions = justification

        # set MetaPrecondition
        node.set_metaprecondition(metaprecondition, metaprecondition_key)

        # restructure the justification to fit Dict[id(eg.Node), Dict[str, Precondition]]
        source_dict = {
            id(source_node): {} for key, (precondition, source_node, knowledge) in fulfilling_preconditions.items()
        }
        source_lookup = {
            id(source_node): source_node
            for key, (precondition, source_node, knowledge) in fulfilling_preconditions.items()
        }
        for key, (precondition, source_node, knowledge) in fulfilling_preconditions.items():
            source_dict[id(source_node)][key] = (precondition, knowledge)

        # draw edges
        for source_node_id, keyed_preconditions_knowledge in source_dict.items():
            self.execution_graph.draw_edge(source_lookup[source_node_id], node, keyed_preconditions_knowledge)

    def draw_duality_edge(
        self, knowledge: Knowledge, node: eg.Node, certainty: float, duality_edge_type: DualityEdgeType
    ):
        if certainty < 0.0 or certainty > 1.0:
            raise ValueError("certainty must be in interval [0,1]")

        duality_edge = DualityEdge(knowledge, node, certainty, duality_edge_type)
        node.add_duality_edge(duality_edge)
        knowledge.add_duality_edge(duality_edge)

    def add_module(
        self,
        module_manager: BufferedModuleManager,
        justification: Tuple[str, MetaPrecondition, Dict[str, Tuple[Precondition, eg.Node, Knowledge]]],
    ):
        self.add_node(module_manager.node, justification)

        # add doc
        module_manager.node.module_doc = module_manager.log_list

        # add knowledge
        for (parent, key, knowledge, certainty, recursive) in module_manager.add_knowledge_buffer:
            if recursive:

                def recursive_get_children(knowledge):
                    temp_children = [
                        (knowledge, key, children)
                        for key, children_list in knowledge.lookup.items()
                        for children in children_list
                    ]
                    recursive_children = ft.reduce(
                        lambda A, B: A + B,
                        [recursive_get_children(knowledge) for parent, key, knowledge in temp_children],
                        [],
                    )
                    return temp_children + recursive_children

                recursive_knowledge = [(parent, key, knowledge)] + recursive_get_children(knowledge)
                # adds the parent into the tree thus "building the bridge"
                self.add_knowledge(parent, key, knowledge)
                for parent, key, knowledge in recursive_knowledge:
                    # for all new added knowledge the duality edge must be drawn and the modules need to be notified
                    self.draw_duality_edge(knowledge, module_manager.node, certainty, DualityEdgeType.ADD)
                    self.notify(knowledge)

            else:
                self.add_knowledge(parent, key, knowledge)
                self.draw_duality_edge(knowledge, module_manager.node, certainty, DualityEdgeType.ADD)
                self.notify(knowledge)

        # update knowledge
        for (knowledge, certainty) in module_manager.update_knowledge_buffer:
            self.draw_duality_edge(knowledge, module_manager.node, certainty, DualityEdgeType.UPDATE)
            self.notify(knowledge, True)

    def notify(self, knowledge: Knowledge, only_update=False):
        e = Event()
        e.knowledge = knowledge
        e.only_update = only_update
        self.notify_all(e)

    @staticmethod
    def filter_string(raw_string):
        allowed = string.ascii_letters + string.digits + string.punctuation + "\n "
        raw_string = "".join(char for char in raw_string if char in allowed)
        raw_string = raw_string.strip(" \n")
        # Mask HTML special characters
        raw_string = raw_string.replace("<", "&lt;")
        raw_string = raw_string.replace(">", "&gt;")
        raw_string = raw_string.replace("/", "&#47;")
        raw_string = raw_string.replace("\\", "&#92;")
        return raw_string

    @staticmethod
    def format_node_string(prefix, nodestr, maxlength):
        prefix_length = len(prefix)
        if prefix_length == 0:
            column_counter = 1
            formatted_string = ""
        else:
            column_counter = prefix_length + 1
            formatted_string = '<font color="#404040">' + prefix + "</font>"

        for position in range(1, len(nodestr) + 1):
            if nodestr[position - 1] == "\n":
                formatted_string = formatted_string + '<font color="#404040">⏎</font><br/>'
            else:
                formatted_string = formatted_string + nodestr[position - 1]
            if (
                column_counter % maxlength == 0
                and not position == len(nodestr)
                and not nodestr[position - 1] == "\n"
                and nodestr[position - 1] != "&"
                and nodestr[position - 2] != "&"
                and nodestr[position - 3] != "&"
                and nodestr[position - 4] != "&"
                and nodestr[position - 5] != "&"
                and nodestr[position - 6] != "&"
                and nodestr[position - 7] != "&"
            ):
                formatted_string = formatted_string + '<font color="#404040">⏎</font><br/>'
                column_counter = 0
            if nodestr[position - 1] == "\n":
                column_counter = 1
            else:
                column_counter = column_counter + 1
        return formatted_string

    def traverse_kb(self, knowledge, curr_node_counter, edges, nodes, structure, max_line_length):
        curr_classname = knowledge.__class__.__name__
        # Provisionary
        if curr_classname not in structure:
            nodes.append((curr_node_counter, "LEAF_CUSTOM", knowledge.__class__.__name__, "-"))
            return curr_node_counter, edges, nodes, structure
        # Provisionary
        if structure[curr_classname][0] == "BRANCH":
            nodes.append((curr_node_counter, "BRANCH", knowledge.__class__.__name__, ""))
            node_counter = curr_node_counter
            for key, child_knowledge_list in knowledge.lookup.items():
                if len(child_knowledge_list) > 0:
                    curr_node_counter += 1
                    intermediate_counter = curr_node_counter
                    edges.append((node_counter, intermediate_counter, ""))
                    nodes.append((intermediate_counter, "INTER", key, ""))
                    arr_pos = 0
                    for child_knowledge in child_knowledge_list:
                        curr_node_counter += 1
                        edges.append((intermediate_counter, curr_node_counter, "[" + str(arr_pos) + "]"))
                        curr_node_counter, edges, nodes, structure = self.traverse_kb(
                            child_knowledge, curr_node_counter, edges, nodes, structure, max_line_length
                        )
                        arr_pos += 1
            return curr_node_counter, edges, nodes, structure
        elif structure[curr_classname][0] == "LEAF_EXTENDS":

            nodes.append(
                (
                    curr_node_counter,
                    "LEAF_EXTENDS",
                    knowledge.__class__.__name__,
                    self.format_node_string(
                        "(" + structure[curr_classname][1] + ") ", self.filter_string(str(knowledge)), max_line_length
                    ),
                )
            )
            return curr_node_counter, edges, nodes, structure
        elif structure[curr_classname][0] == "LEAF_ENUM":
            nodes.append(
                (
                    curr_node_counter,
                    "LEAF_ENUM",
                    knowledge.__class__.__name__,
                    self.format_node_string("", self.filter_string(str(knowledge)), max_line_length),
                )
            )
            return curr_node_counter, edges, nodes, structure
        elif structure[curr_classname][0] == "LEAF_CUSTOM":
            if str(knowledge) == "":
                nodes.append((curr_node_counter, "LEAF_CUSTOM", knowledge.__class__.__name__, "-"))
            else:
                nodes.append(
                    (
                        curr_node_counter,
                        "LEAF_CUSTOM",
                        knowledge.__class__.__name__,
                        self.format_node_string("", self.filter_string(str(knowledge)), max_line_length),
                    )
                )
            return curr_node_counter, edges, nodes, structure
        else:
            raise TypeError(
                "Cannot generate knowledgebase visualization. Failed to classify object of class "
                + curr_classname
                + ". Possible model incoherence!"
            )

    def gen_visualization(self):
        current_python_file_path = os.path.dirname(os.path.realpath(__file__))
        tobj = get_types_obj(os.path.join(current_python_file_path, "types", "types.yaml"))
        check_model_consistency(tobj)
        structure = {}
        structure["RootKnowledge"] = ("BRANCH", "")
        for typeclass in tobj["types"]:
            kind_is = ""
            if typeclass["kind"] == "LEAF_EXTENDS":
                kind_is = typeclass["is"]
            structure[typeclass["name"]] = (typeclass["kind"], kind_is)
        _, edges, nodes, structure = self.traverse_kb(
            self.knowledge_graph.root, 1, [], [], structure, tobj["visualization"]["node_content_max_line_length"]
        )

        template_file = open(os.path.join(current_python_file_path, "kb_visualization.jinja"), "r")
        class_template = ji2.Template(template_file.read())
        template_file.close()
        viz_str = class_template.render(edges=edges, nodes=nodes, style=tobj["visualization"])
        return viz_str
