from typing import List, Tuple, Dict
from pinaht.knowledge.precondition import Precondition, MetaPrecondition
from pinaht.knowledge.types.knowledge import Knowledge
from itertools import product
from pinaht.knowledge.observer_pattern import Observer, Event


class Dependency(Observer):
    def __init__(self, precondition_dnf: Dict[str, Tuple[Dict[str, Precondition], MetaPrecondition]]):
        """
        the constructor of the Dependency class. the precondition must be in D+NF.

        :param precondition_dnf: a precondition D+NF, that is a disjunction of Precondition conjunctions +
                                 a metaprecondition
        """
        super(Dependency, self).__init__()
        self.precondition_dnf = precondition_dnf
        self.fullfilled_knowledge = {
            key: [] for meta_key, (disjunct, meta) in self.precondition_dnf.items() for key in disjunct
        }
        self.preconditions = {
            key: disjunct[key] for meta_key, (disjunct, meta) in self.precondition_dnf.items() for key in disjunct
        }

        self.executed = {}
        self.updated = False

    def update(self, knowledge: Knowledge, only_update: bool = False):
        for key in self.preconditions:
            certainty = self.preconditions[key].holds(knowledge)
            if certainty > 0.0:
                if not only_update:
                    self.fullfilled_knowledge[key].append((certainty, knowledge))
                self.updated = True

    def resolve(self) -> List[Tuple[str, float, Dict[str, Tuple[float, Knowledge]]]]:
        """
        resolve is a methode, that checks with knowledge groupings satisfy the hole precondition D+NF

        :return: returns a List of groupings, that satisfy any conjunction in the D+NF, thus allows a module to be
                 executed. The grouping is the metakey, a certainty of the metaprecondition and the dict of
                 (certainty, knowledge) pairs for each precondition (key).
        """

        # maps for each metaprecondition the set of keys, corresponding to the precondition, that must satisfy the
        # metaprecondition
        meta_precondition_key_list = {
            meta_key: (meta, [key for key in disjunct])
            for meta_key, (disjunct, meta) in self.precondition_dnf.items()
        }

        satisfies_conjunct = []
        for meta_key, (meta, key_list) in meta_precondition_key_list.items():
            # calc the cross-product of the fullfilling knowledges for the given metaprecondition
            # extract the knowledge
            knowledge_and_certainty_group_list = product(*map(lambda key: self.fullfilled_knowledge[key], key_list))

            # for every grouping (aka world) check the certainty of fulfillment of the metaprecondition
            for grouping in knowledge_and_certainty_group_list:
                # zips each grouping with its keys
                knowledge_list = list(zip(key_list, map(lambda group: group[1], grouping)))
                # restructure to key, knowledge pairs
                keyed_knowledge = {key: knowledge for key, knowledge in knowledge_list}

                # checks if the pair has already been executed in a previous run
                has_been_executed = False
                if meta_key in self.executed:
                    for executed_keyed_knowledge in self.executed[meta_key]:
                        assert len(executed_keyed_knowledge) == len(keyed_knowledge)
                        # executed_keyed_knowledge == keyed_knowledge?
                        equals = True
                        for key in key_list:
                            if not id(keyed_knowledge[key]) == id(executed_keyed_knowledge[key]):
                                equals = False
                                break
                        if equals:
                            has_been_executed = True
                            break

                if not has_been_executed:
                    # call metaprecondition holds with the arguments
                    certainty = meta.holds(**keyed_knowledge)
                else:
                    certainty = 0.0
                # only the groupings, that have a certainty > 0.0 are candidates
                if certainty > 0.0:
                    # regrouping {key: (certainty, knowledge)}
                    key_grouping = {key: certainty_knowledge for key, certainty_knowledge in zip(key_list, grouping)}
                    grouping_result = (meta_key, certainty, key_grouping)
                    satisfies_conjunct.append(grouping_result)

        return satisfies_conjunct

    def notify(self, observable, event: Event):
        if isinstance(event.knowledge, Knowledge):
            self.update(event.knowledge, event.only_update)

    def add_executed(self, meta_key: str, keyed_knowledge: Dict[str, Knowledge]):
        if meta_key not in self.executed:
            self.executed[meta_key] = [keyed_knowledge]
        else:
            self.executed[meta_key].append(keyed_knowledge)
        self.updated = True
