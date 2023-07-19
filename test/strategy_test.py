from typing import Tuple, Dict
import logging
from pinaht.application import Application
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.modules.module import Module
from pinaht.knowledge.precondition import (
    Precondition,
    MetaPrecondition,
    gen_empty_metaprecondition,
    gen_type_check_precondition,
)
from pinaht.strategies.fast_strategy import FastStrategy
from pinaht.knowledge.manager import BufferedModuleManager


class Integer(Knowledge, int):
    def __new__(cls, *args, **kwargs):
        return super(Integer, cls).__new__(cls, args[0])

    def __init__(self, *args, **kwargs):
        super(Integer, self).__init__(**kwargs)
        self.lookup = {}
        self.duality_edges = []

    def fuzzy_eq(self, other):
        if isinstance(other, Integer):
            return self == other
        return 0.0

    def add_child(self, key, child):
        raise ValueError()


class A(Knowledge):
    def __init__(self, **kwargs):
        super(A, self).__init__(**kwargs)

        self.parent = None
        self.B = []
        self.C = []
        self.lookup = {"B": self.B, "C": self.C}
        self.duality_edges = []

    def fuzzy_eq(self, other) -> float:
        if isinstance(other, A):
            b_eq = min([max([self_b.fuzzy_eq(other_b) for other_b in other.B] + [0]) for self_b in self.B] + [0])
            c_eq = min([max([self_c.fuzzy_eq(other_c) for other_c in other.C] + [0]) for self_c in self.C] + [0])
            return b_eq * c_eq
        return 0.0

    def add_child(self, key, child):
        if key in self.lookup:
            self.lookup[key].append(child)
        else:
            raise ValueError()


class B(Knowledge):
    def __init__(self, b: Integer, **kwargs):
        super(B, self).__init__(**kwargs)

        self.parent = None
        self.D = []
        self.b = [b]
        self.lookup = {"D": self.D, "b": self.b}
        self.duality_edges = []

    def fuzzy_eq(self, other) -> float:
        if isinstance(other, B):
            d_eq = min([max([self_d.fuzzy_eq(other_d) for other_d in other.D] + [0]) for self_d in self.D] + [0])
            b_eq = min([max([self_b.fuzzy_eq(other_b) for other_b in other.b] + [0]) for self_b in self.b] + [0])

            return d_eq * b_eq
        return 0.0

    def add_child(self, key, child):
        if key in self.lookup:
            self.lookup[key].append(child)
        else:
            raise ValueError()


class C(Knowledge):
    def __init__(self, c_1: Integer, c_2: Integer, **kwargs):
        super(C, self).__init__(**kwargs)

        self.parent = None
        self.D = []
        self.c_1 = [c_1]
        self.c_2 = [c_2]
        self.lookup = {"D": self.D, "c_1": self.c_1, "c_2": self.c_2}
        self.duality_edges = []

    def fuzzy_eq(self, other) -> float:
        if isinstance(other, C):
            d_eq = min([max([self_d.fuzzy_eq(other_d) for other_d in other.D] + [0]) for self_d in self.D] + [0])
            c_1_eq = min(
                [max([self_c.fuzzy_eq(other_c) for other_c in other.c_1] + [0]) for self_c in self.c_1] + [0]
            )
            c_2_eq = min(
                [max([self_c.fuzzy_eq(other_c) for other_c in other.c_2] + [0]) for self_c in self.c_2] + [0]
            )
            return d_eq * c_1_eq * c_2_eq
        return 0.0

    def add_child(self, key, child):
        if key in self.lookup:
            self.lookup[key].append(child)
        else:
            raise ValueError()


class D(Knowledge):
    def __init__(self, d: Integer, **kwargs):
        super(D, self).__init__(**kwargs)

        self.parent = None
        self.d = [d]
        self.duality_edges = []

    def fuzzy_eq(self, other) -> float:
        if isinstance(other, C):
            d_eq = min([max([self_d.fuzzy_eq(other_d) for other_d in other.d] + [0]) for self_d in self.d] + [0])
            return d_eq
        return 0.0

    def add_child(self, key, child):
        if key in self.lookup:
            self.lookup[key].append(child)
        else:
            raise ValueError()


class SearchModule(Module):
    def __init__(self, manager, **kwargs):
        super(SearchModule, self).__init__(manager, **kwargs)
        self.estimated_time = 1
        self.success_chance = 1

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        pre_1 = gen_type_check_precondition(A)
        meta_1 = gen_empty_metaprecondition()
        return {"search_meta_1": ({"pre_1": pre_1}, meta_1)}

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """
        if meta_key == "search_meta_1":
            b_1 = B(Integer(56))
            c_1 = C(Integer(10), Integer(23))
            d_1 = D(Integer(9))
            d_2 = D(Integer(20))

            b_1.add_child("D", d_1)
            c_1.add_child("D", d_2)

            a_2 = A()
            a_2.add_child("B", b_1)
            a_2.add_child("C", c_1)
            buffered_module_manager.add_knowledge(None, "A", a_2, 0.9, True)


class SoloExploitModule(Module):
    def __init__(self, manager, **kwargs):
        super(SoloExploitModule, self).__init__(manager, **kwargs)
        self.estimated_time = 1
        self.success_chance = 1

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """

        class Pre1(Precondition):
            def __init__(self, **kwargs):
                super(Pre1, self).__init__(**kwargs)

            def holds(self, knowledge: Knowledge) -> float:
                if isinstance(knowledge, B):
                    if knowledge.b == "B":
                        return 1.0
                    else:
                        return 0.5
                else:
                    return 0.0

            def doc(self) -> str:
                return f"checks if the given knowledge is of type {B.__name__}"

        pre_1 = Pre1()

        meta_1 = gen_empty_metaprecondition()

        pre_2 = gen_type_check_precondition(C)
        meta_2 = gen_empty_metaprecondition(0.8)
        return {"solo_meta_1": ({"pre_1": pre_1}, meta_1), "solo_meta_2": ({"pre_2": pre_2}, meta_2)}

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """
        if meta_key == "solo_meta_1":
            buffered_module_manager.log("executed on B:")
            b = keyed_knowledge["pre_1"]
            d = D(0.54)
            buffered_module_manager.log("found a D")
            buffered_module_manager.add_knowledge(b, "D", d, 0.9)
            buffered_module_manager.log("set certainty to 1.0")
            buffered_module_manager.update_knowledge(b, 1.0)
        if meta_key == "solo_meta_2":
            buffered_module_manager.log("executed on C:")
            c = keyed_knowledge["pre_2"]
            d = D(0.10)
            buffered_module_manager.log("found a D")
            buffered_module_manager.add_knowledge(c, "D", d, 0.9)
            buffered_module_manager.log("set certainty to 1.0")
            buffered_module_manager.update_knowledge(c, 1.0)


class MultiExploitModule(Module):
    def __init__(self, manager, **kwargs):
        super(MultiExploitModule, self).__init__(manager, **kwargs)
        self.estimated_time = 1
        self.success_chance = 1

    def _generate_precondition_dnf(self) -> Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]:
        """ """
        pre = gen_type_check_precondition(D)

        class Meta1(MetaPrecondition):
            def __init__(self, **kwargs):
                super(Meta1, self).__init__(**kwargs)

            def holds(self, **kwargs) -> float:
                """
                checks if the meterpreconditions holds
                """
                d_1 = kwargs["pre_1"]
                d_2 = kwargs["pre_2"]
                if d_1.parent.fuzzy_eq(d_2.parent) <= 0.0 and d_1.parent.parent.fuzzy_eq(d_2.parent.parent) >= 1.0:
                    return 1.0
                return 0.2

        return {"multi_meta_1": ({"pre_1": pre, "pre_2": pre}, Meta1())}

    def execute(
        self, buffered_module_manager: BufferedModuleManager, meta_key: str, keyed_knowledge: Dict[str, Knowledge]
    ):
        """
        executes the module
        """
        if meta_key == "multi_meta_1":
            print("ROOT")


def test():
    logger = logging.getLogger("strategy test")
    logger.debug("start Strategy test")

    modules = [MultiExploitModule, SearchModule]
    a = A()
    i_1 = Integer(10)
    print(i_1)
    print(type(i_1))
    print(i_1.lookup)
    app = Application(FastStrategy, [(None, "init", a)], modules)
    app.start()
