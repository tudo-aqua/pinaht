from pinaht.knowledge.execution_graph import ExecutionGraph, Node, Edge
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.target import Target
from pinaht.knowledge.types.service import Service
from pinaht.knowledge.types.version import Version
import logging
import time


def test():
    logger = logging.getLogger("kb test")
    logger.debug("start KG test")

    kg = ExecutionGraph()

    t1 = Target("127.0.0.1")
    n1 = Node(None, "node 1", [t1], time.localtime(), time.localtime())
    e1 = Edge(kg.root, n1, [])
    kg.root.next.append(e1)
    n1.previous.append(e1)

    t2 = Target("127.0.0.2")
    n2 = Node(None, "node 2", [t2], time.localtime(), time.localtime())
    e2 = Edge(kg.root, n2, [])
    kg.root.next.append(e2)
    n2.previous.append(e1)

    s1 = Service(t1, 110, "Apache Software Foundation", "Apache Server", Version(Version.parse_version("3.5")))
    s2 = Service(t1, 220, "WordPress Foundation", "WordPress", Version(Version.parse_version("11.2a")))

    logger.debug("Service: " + str(s1))
    logger.debug("Service: " + str(s2))

    n3 = Node(None, "node 3", [s1, s2], time.localtime(), time.localtime())
    e3 = Edge(n1, n3, [])
    n1.next.append(e3)
    n3.previous.append(e3)

    s3 = Service(t2, 330, "Drupal community", "Drupal", Version(Version.parse_version("8.6.5-b")))

    logger.debug("Service: " + str(s3))

    n4 = Node(None, "node 4", [s3], time.localtime(), time.localtime())
    e4 = Edge(n2, n4, [])
    n2.next.append(e4)
    n4.previous.append(e4)

    n5 = Node(None, "node 5", [s2], time.localtime(), time.localtime())
    e5 = Edge(n3, n5, [])
    n3.next.append(e5)
    n5.previous.append(e5)

    e6 = Edge(n4, n5, [])
    n4.next.append(e6)
    n5.previous.append(e6)

    logger.debug(kg.root.module_doc)
    for n in map(lambda n: n.target, kg.root.next):
        logger.debug("." + n.module_doc)
        for m in map(lambda m: m.target, n.next):
            logger.debug(".." + m.module_doc)
            for x in map(lambda x: x.target, m.next):
                logger.debug("..." + x.module_doc)

    logger.debug(list(map(lambda x: (x[1], x[0].module_doc, x[2]), kg.topological_sort(n5))))
    logger.debug("all knowledge")
    for knowledge in kg.get_all_knowledge():
        logger.debug(knowledge)

    logger.debug(kg.bfs(kg.root))
    for n in kg:
        logger.debug(n.module_doc)

    logger.debug("")
    logger.debug("")

    print(list(map(lambda x: str(x), Knowledge.union([s1, s2], [s3]))))
