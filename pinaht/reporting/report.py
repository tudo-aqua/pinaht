from typing import List
import pinaht.knowledge.execution_graph as eg
import pinaht.knowledge.knowledge_graph as kg
from pinaht.strategies.strategy import FlagElement
from pinaht.reporting.report_util import (
    backtrace_flag,
    parse_knowledge,
    get_time_sorted_execution_graph,
    str_to_latex,
)
from pinaht.reporting.execution_graph_visualization import generate_execution_path_visualization
import pinaht.util as util
import time
from jinja2 import Environment
from collections import namedtuple
from latex import build_pdf
from enum import Enum
import os
from pinaht.knowledge.types.ipaddress import IPAddress
from pinaht.knowledge.types.network import Network
from pinaht.knowledge.precondition_factory.preconditions import check_type
from pinaht.knowledge.precondition_factory.metapreconditions import is_parent

latex_jinja_env = Environment(variable_start_string="\VAR[", variable_end_string="]")  # noqa W605


class PaperSize(Enum):
    A4 = "a4paper"
    LETTER = "letterpaper"


Config = namedtuple("Config", ["fontsize", "paper_size"])
Module = namedtuple("Module", ["name", "execution", "duration", "requirements", "metaprecondition_key"])
Requirement = namedtuple("Requirement", ["name", "knowledge", "source", "doc"])
Flag = namedtuple("Flag", ["name", "description", "success", "path", "modules"])
Info = namedtuple("Info", ["duration", "date", "network"])


def generate_report(
    knowledge_graph: kg.KnowledgeGraph,
    execution_graph: eg.ExecutionGraph,
    flags: List[FlagElement],
    path: str,
    paper_size: PaperSize = PaperSize.A4,
):
    config = Config(fontsize="10pt", paper_size=paper_size.value)
    # info
    sorted_nodes = get_time_sorted_execution_graph(execution_graph)
    start_time = sorted_nodes[0].timestamp_start
    end_time = sorted_nodes[-1].timestamp_end

    duration = util.formated_duration(end_time - start_time)

    date = util.formated_date(time.time())

    query_result = knowledge_graph.query(
        ({"Network": check_type(Network), "IP": check_type(IPAddress)}, is_parent("Network", ["IP"]))
    )

    if not query_result:
        network = None
    else:
        network = str(query_result["IP"])

    info = Info(duration=duration, date=date, network=network)

    # flags
    structured_flags = []
    for flag in flags:
        order = backtrace_flag(flag, execution_graph)
        if order:
            modules = []
            for node in order:
                requirements = []
                for edge in node.previous:
                    for name, (pre, knowledge) in edge.preconditions.items():
                        requirement = Requirement(
                            name=str_to_latex(name),
                            knowledge=str_to_latex(parse_knowledge(knowledge)),
                            source=str_to_latex(edge.source.module_name),
                            doc=str_to_latex(pre.doc(knowledge)),
                        )
                        requirements.append(requirement)
                module = Module(
                    name=str_to_latex(node.module_name),
                    execution=node.module_doc,
                    duration=str_to_latex(util.formated_duration(node.timestamp_end - node.timestamp_start)),
                    requirements=str_to_latex(requirements),
                    metaprecondition_key=str_to_latex(node.metaprecondition_key),
                )
                modules.append(module)

            path = generate_execution_path_visualization(execution_graph, flag)

            structured_flag = Flag(
                name=str_to_latex(flag.name),
                description=str_to_latex(flag.flag.description()),
                success=True,
                path=path,
                modules=modules,
            )
        else:
            structured_flag = Flag(
                name=str_to_latex(flag.name), description=flag.flag.description(), success=False, path="", modules=[]
            )
        structured_flags.append(structured_flag)

    current_python_file_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(current_python_file_path, "templates", "report.jinja"), "r") as file:
        template = latex_jinja_env.from_string(file.read())
    file.close()
    pdf = build_pdf(template.render(config=config, info=info, structured_flags=structured_flags))
    pdf.save_to(os.path.join(os.getcwd(), "reports", "report.pdf"))
