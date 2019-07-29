import compiler.data_structures.symbol_table as st
from compiler.data_structures.ir import *
from compiler.data_structures.scope import Scope
from grammar.parsers.python.BSParser import BSParser
from grammar.parsers.python.BSParserVisitor import BSParserVisitor
from shared.bs_exceptions import *


class BSBaseVisitor(BSParserVisitor):

    def __init__(self, symbol_table: st.SymbolTable, name="BaseVisitor"):
        super().__init__()
        self.log = colorlog.getLogger(self.__class__.__name__)
        self.visitor_name = name
        # Name of global scope
        self.global_scope = "global"
        # The current symbol table
        self.symbol_table = symbol_table
        self.nl = "\n"
        # Manages the scopes that we are in.
        self.scope_stack = list()
        # Determines if renaming should happen.
        self.rename = False

    def visitTimeIdentifier(self, ctx: BSParser.TimeIdentifierContext) -> dict:
        quantity = 10.0
        units = BSTime.SECOND
        if ctx:
            x = self.split_number_from_unit(ctx.TIME_NUMBER().__str__())
            units = BSTime.get_from_string(x['units'])
            quantity = units.normalize(x['quantity'])
        return {'quantity': quantity, 'units': BSTime.SECOND, 'preserved_units': units}

    def visitTemperatureIdentifier(self, ctx: BSParser.TemperatureIdentifierContext) -> dict:
        x = self.split_number_from_unit(ctx.TEMP_NUMBER().__str__())
        units = BSTemperature.get_from_string(x['units'])
        quantity = units.normalize(x['quantity'])
        return {'quantity': quantity, 'units': BSTemperature.CELSIUS, 'preserved_units': units}

    def visitVariableDefinition(self, ctx: BSParser.VariableDefinitionContext):
        return self.visitVariable(ctx.variable())

    def visitVariable(self, ctx: BSParser.VariableContext):
        """
        Gets the variable to which the statement will be assigned.
        If it's -1, the statement uses the whole array.  Which means
        there must be a check to see if the size of the input arrays
        are equal.
        :param ctx: context of the visitor.
        :return: Dictionary that holds the index and the name of the variable to be assigned.
        """
        # If it's -1, it means there wasn't anything given,
        # so use all the elements of the variable available.
        index = -1 if not ctx.INTEGER_LITERAL() else int(ctx.INTEGER_LITERAL().__str__())
        # Array_ref is context specific, something visitVariable cannot infer.
        # Either it is the size of the element or the index.
        # In something like a dispense, it's a size; if it's a mix, it's an index.
        return {"name": ctx.IDENTIFIER().__str__(), "index": index}

    def visitPrimary(self, ctx: BSParser.PrimaryContext):
        if ctx.IDENTIFIER():
            if not self.symbol_table.get_variable(ctx.IDENTIFIER().__str__(), self.scope_stack[-1]):
                raise UndefinedException("Undeclared variable: {}".format(ctx.IDENTIFIER().__str__()))
            return ctx.IDENTIFIER().__str__()
        elif ctx.literal():
            return self.visitLiteral(ctx.literal())
        else:
            return self.visitExpression(ctx.expression())

    def visitLiteral(self, ctx: BSParser.LiteralContext):
        if ctx.INTEGER_LITERAL():
            return ctx.INTEGER_LITERAL().__str__()
        elif ctx.BOOL_LITERAL():
            return ctx.BOOL_LITERAL().__str__()
        elif ctx.FLOAT_LITERAL():
            return ctx.FLOAT_LITERAL().__str__()
        else:
            return ctx.STRING_LITERAL().__str__()

    # def visitExpression(self, ctx: BSParser.ExpressionContext):
    #     if ctx.primary():
    #         return self.visitPrimary(ctx.primary())
    #     else:
    #         exp1 = self.visitExpression(ctx.expression(0))
    #         exp2 = self.visitExpression(ctx.expression(1))
    #         if ctx.MULTIPLY():
    #             op = BinaryOps.MULTIPLE
    #         elif ctx.DIVIDE():
    #             op = BinaryOps.DIVIDE
    #         elif ctx.ADDITION():
    #             op = BinaryOps.ADD
    #         elif ctx.SUBTRACT():
    #             op = BinaryOps.SUBTRACT
    #         elif ctx.AND():
    #             op = BinaryOps.AND
    #         elif ctx.EQUALITY():
    #             op = RelationalOps.EQUALITY
    #         elif ctx.GT():
    #             op = RelationalOps.GT
    #         elif ctx.GTE():
    #             op = RelationalOps.GTE
    #         elif ctx.LT():
    #             op = RelationalOps.LT
    #         elif ctx.LTE():
    #             op = RelationalOps.LTE
    #         elif ctx.NOTEQUAL():
    #             op = RelationalOps.NE
    #         elif ctx.OR():
    #             op = BinaryOps.OR
    #         else:
    #             op = RelationalOps.EQUALITY
    #
    #         if ctx.LBRACKET():
    #             """
    #             In this context, exp1 will *always* hold the variable name.
    #             So we can check to make sure that exp1 is the appropriate size,
    #             Given exp2 as the index.
    #             """
    #             variable = self.symbol_table.get_variable(exp1)
    #             if int(exp2) > variable.size - 1 and int(exp2) >= 0:
    #                 raise InvalidOperation("Out of bounds index: {}[{}], where {} is of size: {}".format(
    #                     exp1, exp2, exp1, variable.size))
    #             output = "{}[{}]".format(exp1, exp2)
    #         else:
    #             if not self.is_number(exp1):
    #                 exp1 = self.symbol_table.get_local(exp1, self.scope_stack[-1])
    #             if not self.is_number(exp2):
    #                 exp2 = self.symbol_table.get_local(exp2, self.scope_stack[-1])
    #             output = {"exp1": exp1, "exp2": exp2, "op": op}
    #
    #         return output

    def split_number_from_unit(self, text) -> dict:
        """
        Splits the number and units: 10mL => (10, "mL").
        :param text: Input text for splitting.
        :return: Dictionary of necessary output.
        """
        temp_float = ""
        temp_unit = ""
        for x in text[0:]:
            if str.isdigit(x):
                temp_float += x
            elif x == ".":
                temp_float += x
            elif x == ",":
                continue
            else:
                temp_unit += x
        return {'quantity': float(temp_float), 'units': temp_unit}

    def get_scope(self, name) -> Scope:
        """
        Get the scope.
        :param name: name of scope.
        :return: Scope object associated with the name.
        """
        if name not in self.symbol_table.scope_map:
            scope = Scope(name)
            self.symbol_table.scope_map[name] = scope
            return scope
        else:
            return self.symbol_table.scope_map[name]

    def check_bounds(self, var: Variable, index: int) -> bool:
        """
        Check to see if we have a valid offset for a variable.
        :param var: Variable to bound check.
        :param index: int offset.
        :return: bool: key is in the object.
        :raises:
            KeyError: if the key doesn't exist in the object,
                this will throw an error.
        """
        if index >= 0:
            return var.value[index]

    @staticmethod
    def is_number(num):
        """
        Simple check to determine if input is a number.
        :param num: Input string.
        :return: Boolean determining if a string is a number.
        """
        try:
            if isinstance(num, Number):
                return False
            float(num)
            return True
        except ValueError:
            return False
