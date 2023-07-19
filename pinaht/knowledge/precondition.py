from abc import ABC, abstractmethod
from pinaht.knowledge.types.knowledge import Knowledge


class Precondition(ABC):
    """
    A precondition Interface
    """

    def __init__(self, **kwargs):
        super(Precondition, self).__init__(**kwargs)

    @abstractmethod
    def holds(self, knowledge: Knowledge) -> float:
        """
        The holds method defines whether the precondition is fulfilled

        :param node_knowledge: a list of knowledge, to check the precondition.
        :return: float, degree of certainty
        """
        raise NotImplementedError()

    @abstractmethod
    def doc(self, knowledge: Knowledge) -> str:
        """
        The doc method documents the precondition.

        :return: a str, that is the documentation of the precondition
        """
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__


class MetaPrecondition(ABC):
    """ """

    def __init__(self, **kwargs):
        super(MetaPrecondition, self).__init__(**kwargs)

    @abstractmethod
    def holds(self, **kwargs) -> float:
        """
        checks if the meterpreconditions holds
        """

        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__


def gen_type_check_precondition(target_type):
    print("method gen_type_check_precondition deprecated")

    class TypeCheckPrecondition(Precondition):
        def __init__(self, **kwargs):
            super(TypeCheckPrecondition, self).__init__(**kwargs)

        def holds(self, knowledge: Knowledge) -> float:
            return 1.0 if isinstance(knowledge, target_type) else 0.0

        def doc(self, knowledge: Knowledge) -> str:
            return f"checks if the given knowledge is of type {target_type.__name__}"

    return TypeCheckPrecondition()


def gen_empty_metaprecondition(certainty: float = 1.0):
    print("method gen_empty_metaprecondition deprecated")

    class EmptyMetaprecondition(MetaPrecondition):
        def __init__(self, **kwargs):
            super(EmptyMetaprecondition, self).__init__(**kwargs)

        def holds(self, **kwargs) -> float:
            return certainty

    return EmptyMetaprecondition()
