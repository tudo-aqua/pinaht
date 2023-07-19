from pinaht.knowledge.dependency import Dependency
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
import logging


class A(Knowledge):
    def __init__(self, **kwargs):
        super(A, self).__init__(**kwargs)
        self.a = "a"
        self.B = []
        self.C = []

    def fuzzy_eq(self, other) -> float:
        if isinstance(other, A) and id(self) == id(other):
            return 1.0
        return 0.0

    def link_to_parent(self, parent):
        pass


class B(Knowledge):
    def __init__(self, **kwargs):
        super(B, self).__init__(**kwargs)
        self.b = "b"

    def fuzzy_eq(self, other) -> float:
        if isinstance(other, B) and self.b == other.b:
            return 1.0
        return 0.0

    def link_to_parent(self, parent):
        if isinstance(parent, A):
            parent.B.append(self)
            self.parent = parent


class C(Knowledge):
    def __init__(self, **kwargs):
        super(C, self).__init__(**kwargs)
        self.c = "c"

    def fuzzy_eq(self, other) -> float:
        if isinstance(other, C) and self.c == other.c:
            return 1.0
        return 0.0

    def link_to_parent(self, parent):
        if isinstance(parent, A):
            parent.C.append(self)
            self.parent = parent


class Pre1(Precondition):
    def __init__(self, **kwargs):
        super(Pre1, self).__init__(**kwargs)

    def holds(self, knowledge: Knowledge) -> float:
        if isinstance(knowledge, B):
            if knowledge.b == "b":
                return 0.9
            return 0.5
        return 0.0

    def doc(self) -> str:
        return "pre_1"


class Pre2(Precondition):
    def __init__(self, **kwargs):
        super(Pre2, self).__init__(**kwargs)

    def holds(self, knowledge: Knowledge) -> float:
        if isinstance(knowledge, C):
            if knowledge.c == "c":
                return 0.9
            if knowledge.c == "C":
                return 0.1
            return 0.5
        return 0.0

    def doc(self) -> str:
        return "pre_2"


class M1(MetaPrecondition):
    def __init__(self, **kwargs):
        super(M1, self).__init__(**kwargs)

    def holds(self, pre_1, pre_2) -> float:
        """
        checks if the meterpreconditions holds
        """
        if isinstance(pre_1, Knowledge) and isinstance(pre_2, Knowledge):
            return pre_1.parent.fuzzy_eq(pre_2.parent)
        return 0.0


def test():
    logger = logging.getLogger("kb test")
    logger.debug("start KG test")
    # gen knowledge

    a_1 = A()
    a_2 = A()

    b_1 = B()
    b_2 = B()
    b_2.b = "B"

    c_1 = C()
    c_2 = C()
    c_2.c = "C"

    b_1.link_to_parent(a_1)
    b_2.link_to_parent(a_1)
    c_1.link_to_parent(a_1)
    c_2.link_to_parent(a_2)

    dnf = {"M1": ({"pre_1": Pre1(), "pre_2": Pre2()}, M1())}
    logger.debug(dnf)

    dependency = Dependency(dnf)
    logger.debug("Dependency Status:")
    logger.debug(dependency.precondition_dnf)
    logger.debug(dependency.fullfilled_knowledge)
    logger.debug(dependency.preconditions)

    dependency.update(a_1)
    logger.debug("Update with a_1")
    logger.debug("Dependency Status:")
    logger.debug(dependency.fullfilled_knowledge)

    dependency.update(a_2)
    logger.debug("Update with a_1")
    logger.debug("Dependency Status:")
    logger.debug(dependency.fullfilled_knowledge)

    dependency.update(b_1)
    logger.debug("Update with b_1")
    logger.debug("Dependency Status:")
    logger.debug(dependency.fullfilled_knowledge)

    dependency.update(c_1)
    logger.debug("Update with c_1")
    logger.debug("Dependency Status:")
    logger.debug(dependency.fullfilled_knowledge)

    dependency.update(b_2)
    logger.debug("Update with b_2")
    logger.debug("Dependency Status:")
    logger.debug(dependency.fullfilled_knowledge)

    dependency.update(c_2)
    logger.debug("Update with c_2")
    logger.debug("Dependency Status:")
    logger.debug(dependency.fullfilled_knowledge)

    logger.debug(dependency.resolve())
