from abc import ABCMeta, abstractmethod
from enum import IntEnum
from typing import List, Set

from chemicals.chemtypes import ChemTypes, ChemTypeResolver
from chemicals.epa_manager import EpaManager


class CombineMethod(IntEnum):
    NAIVE = 1
    SIMULATE = 2

    def get_combiner(self, epa_defs: str, abs_int: str):
        if self.value == CombineMethod.SIMULATE:
            return SimulateCombiner(epa_defs, abs_int)
        else:
            return NaiveCombiner()


class Combiner(metaclass=ABCMeta):
    """
    This class deals with combining chemicals.
    However, there is a difficult dependency to untie here.
    Functions typecheck, union, and naive could be split into
    their own class (TypeChecker) but for simplicity, right now,
    it is just combined here.
    """

    def __init__(self):
        pass

    def combine(self, one, two):
        result = set()
        if one in ChemTypeResolver.materials and two in ChemTypeResolver.materials:
            result.add(ChemTypes.MAT)
        elif one in ChemTypeResolver.numbers and two in ChemTypeResolver.numbers:
            result.union(ChemTypeResolver.numbers)
        elif (one in ChemTypeResolver.numbers and two in ChemTypeResolver.materials) or \
                (one in ChemTypeResolver.materials and two in ChemTypeResolver.numbers):
            result.add(ChemTypes.REAL)
            result.add(ChemTypes.MAT)
        else:
            result.add(ChemTypes.UNKNOWN)
        return result

    @abstractmethod
    def combine(self, *args: List) -> Set:
        """
        Takes a list of sets and returns a union of them.
        :param args: List of sets containing ChemTypes types.
        :return: Set of union-ed ChemTypes types.
        """
        pass

    @abstractmethod
    def combine_sets(self, set1: Set, set2: Set) -> Set:
        pass

    @abstractmethod
    def combine_types(self, t1: ChemTypes, t2: ChemTypes) -> Set:
        pass


class NaiveCombiner(Combiner):

    def __init__(self):
        super().__init__()

    def combine(self, *args: List) -> Set:
        types = set()
        for arg in args:
            types.union(arg)
        return types

    def combine_sets(self, set1: Set, set2: Set) -> Set:
        result = set()
        for one in set1:
            for two in set2:
                if one in ChemTypeResolver.materials and two in ChemTypeResolver.materials:
                    result.add(ChemTypes.MAT)
                elif one in ChemTypeResolver.numbers and two in ChemTypeResolver.numbers:
                    result.union(ChemTypeResolver.numbers)
                elif (one in ChemTypeResolver.numbers and two in ChemTypeResolver.materials) or \
                        (one in ChemTypeResolver.materials and two in ChemTypeResolver.numbers):
                    result.add(ChemTypes.REAL)
                    result.add(ChemTypes.MAT)
                else:
                    result.add(ChemTypes.UNKNOWN)
        return result

    def combine_types(self, t1: ChemTypes, t2: ChemTypes) -> Set:
        return {t1, t2}


class SimulateCombiner(Combiner):

    def __init__(self, epa_manager: str = "/resources/epa_defs.json",
                 abs_int: str = '/resources/abstract-interaction.txt'):
        super().__init__()
        self.epa_manager = EpaManager(epa_manager, abs_int)

    def combine(self, *args: List) -> Set:
        types = set()
        for x in range(0, len(args)):
            if x + 1 < len(args):
                types.add(self.combine_sets(args[x], args[x + 1]))
        return types

    def combine_sets(self, t1: Set, t2: Set) -> Set:
        types = set()
        for one, two in t1, t2:
            types.add(self.combine_types(one, two))
        return types

    def combine_types(self, t1: ChemTypes, t2: ChemTypes) -> Set:
        return self.epa_manager.get_interaction_result(t1, t2)
