from typing import Callable
from pinaht.knowledge.types.knowledge import Knowledge
from pinaht.knowledge.types.version import Version
from pinaht.knowledge.precondition import Precondition


def check_type(target_type: type) -> Precondition:
    class CheckPrecondition(Precondition):
        def __init__(self, **kwargs):
            super(CheckPrecondition, self).__init__(**kwargs)

        def holds(self, knowledge: Knowledge) -> float:
            if isinstance(knowledge, target_type):
                return 1.0
            return 0.0

        def doc(self, knowledge: Knowledge) -> str:
            return f"checks if {knowledge!s} is of type {target_type.__name__}"

    return CheckPrecondition()


def check_value(value: Knowledge) -> Precondition:
    class CheckPrecondition(Precondition):
        def __init__(self, **kwargs):
            super(CheckPrecondition, self).__init__(**kwargs)

        def holds(self, knowledge: Knowledge) -> float:
            return knowledge.fuzzy_eq(value)

        def doc(self, knowledge: Knowledge) -> str:
            return f"checks if {knowledge!s} is fuzzy equals to the value {value}"

    return CheckPrecondition()


def compare_value(
    f: Callable[[Knowledge], float], description: Callable[[Knowledge], str] = lambda x: "no information"
) -> Precondition:
    class ContainsPrecondition(Precondition):
        def __init__(self, **kwargs):
            super(ContainsPrecondition, self).__init__(**kwargs)

        def holds(self, knowledge: Knowledge) -> float:
            return f(knowledge)

        def doc(self, knowledge: Knowledge) -> str:
            return f"checks if {knowledge!s} fulfills the function f: {description(knowledge)}"

    return ContainsPrecondition()


def check_str(
    f: Callable[[str], float], description: Callable[[str], str] = lambda x: "no information"
) -> Precondition:
    class ContainsPrecondition(Precondition):
        def __init__(self, **kwargs):
            super(ContainsPrecondition, self).__init__(**kwargs)

        def holds(self, knowledge: Knowledge) -> float:
            if isinstance(knowledge, str):
                return f(knowledge)
            return 0.0

        def doc(self, knowledge: Knowledge) -> str:
            return f"checks if the string {knowledge!s} fulfills the function f: {description(knowledge)}"

    return ContainsPrecondition()


def check_version(
    compare: Callable[[Version], float], description: Callable[[Version], str] = lambda x: "no information"
) -> Precondition:
    class CheckPrecondition(Precondition):
        def __init__(self, **kwargs):
            super(CheckPrecondition, self).__init__(**kwargs)

        def holds(self, knowledge: Knowledge) -> float:
            if isinstance(knowledge, Version):
                return compare(knowledge)
            return 0.0

        def doc(self, knowledge: Knowledge) -> str:
            return f"checks if the version {knowledge!s} fulfills the function f: {description(knowledge)}"

    return CheckPrecondition()
