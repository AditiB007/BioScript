from compiler.data_structures import Program
from compiler.passes.analyses.bs_analysis import BSAnalysis

import networkx as nx
import json
from collections import defaultdict

# Use-def chain
# https://en.wikipedia.org/wiki/Use-define_chain
# https://github.com/lilott8/ChemCompiler-Deprecated-/blob/master/src/main/java/compilation/datastructures/basicblock/DependencySlicedBasicBlock.java

# RUN COMMAND: python3 main.py -i tests/test_cases/slice/slice1.bs -t ir
# Stick to formats that have libraries between languages : JSON recommend
# NetworkX goes away at this stage
# Be aware of certain flow displays of mfsim
# Goals: Build def-use chain, implicitly building the needed DAGs, Dependency Graph

class Chain(object):

    def __init__(self, block: int, instruction: int):
        self.block = -1
        self.instruction = -1


class Slicer(BSAnalysis):

    def __init__(self):
        super().__init__("Slicer")
        self.def_use_chain = dict()

    def analyze(self, program: Program) -> dict:
        self.build_dependency_graph(program)
        return {'name': self.name, 'result': None}

    def build_dependency_graph(self, program: Program):
        deps = dict()
        defs = dict()
        uses = list()  # list of maps
        def_use_json = dict()

        for root in program.functions:
            for nid, block in program.functions[root]['blocks'].items():
                i_counter = 1
                for instruction in block.instructions:
                    # self.log.info(instruction)

                    # DISPENSE
                    if str(type(instruction)) == "<class 'compiler.data_structures.ir.Dispense'>":
                        ins = str(instruction).split('=')
                        var = ins[0].strip()
                        exp = ins[1:]

                        deps[var] = exp
                        defs[var] = (nid, i_counter)

                    # MIX
                    if str(type(instruction)) == "<class 'compiler.data_structures.ir.Mix'>":
                        ins = str(instruction).split('=')
                        var = ins[0].strip()
                        exp = ins[1:]
                        parts = str(exp)[7:-3].split(',')

                        deps[var] = exp
                        defs[var] = (nid, i_counter)
                        uses.extend([(parts[0].strip(), (nid, i_counter)), (parts[1].strip(), (nid, i_counter))])

                    # Line Counter
                    i_counter += 1

        # This aligns out print statements with the log format info = green, warn = yellow, error = red
        # self.log.info("\nDeps: \n{} \nDefs: \n{} \nUses: \n{}".format(deps, defs, uses))

        used = defaultdict(list)
        multi_use = defaultdict(list)

        # find the possible conflicts
        for u in uses:
            used[u[0]].append(u[1])
        for u in used:
            if len(used[u]) > 1:
                # self.log.warn("{} in block: 0 at line: {} ".format(u, used[u][1:]))
                multi_use[u].append(used[u][1:])
        # output data file
        for u in multi_use:
            def_use_json[u] = "{}".format(multi_use[u])
        with open('data.txt', 'w') as outfile:
            json.dump(def_use_json, outfile)

        return [deps, defs, uses]
