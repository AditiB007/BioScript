from compiler.data_structures.symbol_table import SymbolTable


class Program(object):
    """
    This class models the input program and
    stores various data about the program.
    """

    def __init__(self, functions: dict = dict, roots: dict = dict, entry_point: int = 1,
                 symbol_table: SymbolTable = None, bb_graph=None, name: str = "program",
                 ssa_form: bool = False, analysis: dict = dict(), globals: dict = dict(), calls: dict = dict()):
        # A dict: id->basic block
        self.functions = functions
        # Set of basic block ids that are roots
        self.roots = roots
        # The main entry point for the program
        self.entry_point = entry_point
        # The symbol table for the program
        self.symbol_table = symbol_table
        # The basic block based control flow graph
        self.bb_graph = bb_graph
        # The name of the graph
        self.name = name
        # Is this program in SSA form?
        self.ssa_form = ssa_form
        # Storing different analysis here (liveness, call graph, etc)
        self.analysis = analysis
        # Keep track of the globals
        self.globals = globals
        # keep the call graph.
        self.calls = calls
        # for source, destinations in calls.items():
        #     for destination in destinations:
        #         self.bb_graph.add_edge(self.functions[source]['entry'], self.functions[destination]['entry'])
