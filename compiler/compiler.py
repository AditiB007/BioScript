import colorlog
import networkx as nx
from antlr4 import *

from compiler.config.config import Config
from compiler.data_structures.program import Program
from compiler.data_structures.symbol_table import SymbolTable
from compiler.passes.pass_manager import PassManager
from compiler.semantics.global_visitor import GlobalVariableVisitor
from compiler.semantics.ir_visitor import IRVisitor
from compiler.semantics.method_visitor import MethodVisitor
from compiler.semantics.symbol_visitor import SymbolTableVisitor
from compiler.semantics.type_visitor import TypeCheckVisitor
from grammar.parsers.python.BSLexer import BSLexer
from grammar.parsers.python.BSParser import BSParser
from solvers.z3_solver import Z3Solver


class BSCompiler(object):

    def __init__(self, configuration: Config):
        self.config = configuration
        self.log = colorlog.getLogger(self.__class__.__name__)
        self.log.warning(self.config.input)
        # The symbol is built is phases, hence it's globalness.
        self.symbol_table = None
        self.program = None

    def compile(self):
        ir = self.translate(self.config.input)
        ir = self.optimizations(self.program)
        target = self.target(self.program)

    def translate(self, filename: str) -> Program:
        """
        Translates the program from the AST into the corresponding IR.
        :param filename: name of file to parse.
        :return:
        """
        file_stream = FileStream(filename)
        lexer = BSLexer(file_stream)
        stream = CommonTokenStream(lexer)
        parser = BSParser(stream)
        tree = parser.program()

        # This gets run first, gathering all the globals.
        global_visitor = GlobalVariableVisitor(SymbolTable(), self.config.identify.get_identifier())
        global_visitor.visit(tree)

        # Build the functions and their symbols next.
        method_visitor = MethodVisitor(global_visitor.symbol_table)
        method_visitor.visit(tree)

        # Finish building the symbol table.
        symbol_visitor = SymbolTableVisitor(method_visitor.symbol_table, self.config.identify.get_identifier())
        symbol_visitor.visit(tree)

        # Attempt to type check the program
        self.visit_type_check(tree, symbol_visitor.symbol_table)

        # Convert the AST to the IR for further analysis.
        ir_visitor = IRVisitor(symbol_visitor.symbol_table)
        ir_visitor.visit(tree)
        # Always update the symbol table.
        self.program = Program(ir_visitor)
        self.program.name = filename

        if self.config.write_cfg:
            pos = nx.nx_agraph.graphviz_layout(ir_visitor.graph)
            nx.draw(ir_visitor.graph, pos=pos)
            nx.drawing.nx_pydot.write_dot(ir_visitor.graph, 'file.dot')

        return self.program

    def optimizations(self, program: Program):
        """
        Run the various optimizations that can be run.
        :param program:
        :return:
        """
        passes = PassManager(self.program)
        passes.config = self.config
        passes.run_analysis()
        passes.run_transformations()
        # return passes
        return program

    def target(self, program: Program):
        """
        Run the various transforms that can be run.
        :param program:
        :return:
        """
        target = self.config.target.get_target(self.config)
        target.transform(self.program)
        return target

    def visit_type_check(self, tree, symbol_table: SymbolTable):
        """
        Attempts to typecheck a program if enabled.
        :param tree: the AST of a program.
        :param symbol_table: The symbol table of the program.
        :return: None
        """
        if self.config.typecheck:
            combiner = self.config.combine.get_combiner(self.config.epa_defs, self.config.abstract_interaction)
            type_checker = TypeCheckVisitor(symbol_table, combiner, self.config.types_used)
            type_checker.visit(tree)
            z3 = Z3Solver()
            self.log.info(type_checker.smt_string)
            if not z3.solve(type_checker.smt_string):
                raise TypeError("The BioScript program could not be safely type checked.")
        else:
            self.log.debug("Type checking has been disabled.")
