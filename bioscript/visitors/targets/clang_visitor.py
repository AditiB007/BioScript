from bioscript.visitors.targets.target_visitor import TargetVisitor
from grammar.parsers.python.BSParser import BSParser
from shared.bs_exceptions import UndefinedException
from shared.enums.chemtypes import ChemTypes


class ClangVisitor(TargetVisitor):

    def __init__(self, symbol_table):
        super().__init__(symbol_table, "ClangVisitor")
        self.compiled = "// BSProgram!" + self.nl
        self.compiled += "#include <unistd.h>" + self.nl + "#include <random>" + self.nl
        self.compiled += "{}{}{}".format(self.build_structs(), self.nl, self.build_functions())

    def visitProgram(self, ctx: BSParser.ProgramContext):
        self.scope_stack.append("main")
        self.visitModuleDeclaration(ctx.moduleDeclaration())
        self.visitManifestDeclaration(ctx.manifestDeclaration())
        self.visitStationaryDeclaration(ctx.stationaryDeclaration())

        for func in ctx.functionDeclaration():
            self.visitFunctionDeclaration(func)

        self.add("int main() {")

        for statement in ctx.statements():
            self.add(self.visitStatements(statement))

        self.add("} // main")

    def visitModuleDeclaration(self, ctx: BSParser.ModuleDeclarationContext):
        for name in ctx.IDENTIFIER():
            self.add("module {};".format(self.check_identifier(name.__str__())))

    def visitManifestDeclaration(self, ctx: BSParser.ManifestDeclarationContext):
        for name in ctx.IDENTIFIER():
            self.add("mat {};".format(self.check_identifier(name.__str__())))

    def visitStationaryDeclaration(self, ctx: BSParser.StationaryDeclarationContext):
        for name in ctx.IDENTIFIER():
            self.add("mat {};".format(self.check_identifier(name.__str__())))
        pass

    def visitFunctionDeclaration(self, ctx: BSParser.FunctionDeclarationContext):
        name = ctx.IDENTIFIER().__str__()
        func = self.symbol_table.functions[name]

        self.scope_stack.append(name)
        if ChemTypes.MAT in func.types:
            output = "mat "
        else:
            output = "double "

        output += "{} (".format(name)
        if func.args:
            for arg in func.args:
                output += "{} {}, ".format(
                    self.get_types(self.symbol_table.get_variable(arg.name, self.scope_stack[-1]).types), arg.name)
            output = output[:-2]
        output += ") {{{}".format(self.nl)

        for statement in ctx.statements():
            output += "{} {}".format(self.visitStatements(statement), self.nl)

        output += "return {};{}".format(self.visitReturnStatement(ctx.returnStatement()), self.nl)
        output += "}} // end {} {}".format(name, self.nl)

        self.add(output)
        self.scope_stack.pop()

    def visitFormalParameters(self, ctx: BSParser.FormalParametersContext):
        return super().visitFormalParameters(ctx)

    def visitFormalParameterList(self, ctx: BSParser.FormalParameterListContext):
        return super().visitFormalParameterList(ctx)

    def visitFormalParameter(self, ctx: BSParser.FormalParameterContext):
        return super().visitFormalParameter(ctx)

    def visitFunctionTyping(self, ctx: BSParser.FunctionTypingContext):
        return super().visitFunctionTyping(ctx)

    def visitReturnStatement(self, ctx: BSParser.ReturnStatementContext):
        return ctx.IDENTIFIER().__str__()

    def visitBlockStatement(self, ctx: BSParser.BlockStatementContext):
        output = ""
        for statement in ctx.statements():
            output += "{}{}".format(self.visitStatements(statement), self.nl)
        return output

    def visitAssignmentOperations(self, ctx: BSParser.AssignmentOperationsContext):
        if ctx.mix():
            return self.visitMix(ctx.mix())
        elif ctx.detect():
            return self.visitDetect(ctx.detect())
        elif ctx.expression():
            return self.visitExpression(ctx.expression())
        elif ctx.split():
            return self.visitSplit(ctx.split())
        elif ctx.methodCall():
            return self.visitMethodCall(ctx.methodCall())
        else:
            self.log.fatal("No operation: {}".format(ctx.getText()))
            return ""

    def visitStatements(self, ctx: BSParser.StatementsContext):
        if ctx.dispose():
            return self.visitDispose(ctx.dispose())
        elif ctx.heat():
            return self.visitHeat(ctx.heat())
        elif ctx.ifStatement():
            return self.visitIfStatement(ctx.ifStatement())
        elif ctx.localVariableDeclaration():
            return self.visitLocalVariableDeclaration(ctx.localVariableDeclaration())
        elif ctx.whileStatement():
            return self.visitWhileStatement(ctx.whileStatement())
        elif ctx.repeat():
            return self.visitRepeat(ctx.repeat())
        else:
            self.log.fatal("No operation: {}".format(ctx.getText()))
            return ""

    def visitIfStatement(self, ctx: BSParser.IfStatementContext):
        output = "if {} {{{}{}".format(self.visitParExpression(ctx.parExpression()), self.nl,
                                       self.visitBlockStatement(ctx.blockStatement(0)))
        output += self.nl
        output += "}"

        if ctx.ELSE():
            output += "ELSE {{ {}".format(self.nl)
            output += "{} {} }}".format(self.visitBlockStatement(ctx.blockStatement(1)), self.nl)

        return output

    def visitWhileStatement(self, ctx: BSParser.WhileStatementContext):
        return super().visitWhileStatement(ctx)

    def visitRepeat(self, ctx: BSParser.RepeatContext):
        return super().visitRepeat(ctx)

    def visitMix(self, ctx: BSParser.MixContext):
        output = "mix("
        for v in ctx.volumeIdentifier():
            var = self.visit(v)
            output += "{}, {}, ".format(self.check_identifier(var['variable'].name), var['quantity'])
        if ctx.timeIdentifier():
            time = self.visitTimeIdentifier(ctx.timeIdentifier())
            output += time['quantity']
        else:
            output += "10.0"
        output += ")"
        return output

    def visitDetect(self, ctx: BSParser.DetectContext):
        output = "detect("
        module = self.check_identifier(ctx.IDENTIFIER(0).__str__())
        material = self.check_identifier(ctx.IDENTIFIER(1).__str__())
        output += "{}, {}, ".format(module, material)
        if ctx.timeIdentifier():
            time = self.visitTimeIdentifier(ctx.timeIdentifier())
            output += "{}".format(time['quantity'])
        else:
            output += "10.0"

        output += ")"
        return output

    def visitHeat(self, ctx: BSParser.HeatContext):
        name = ctx.IDENTIFIER()
        temp = self.visitTemperatureIdentifier(ctx.temperatureIdentifier())
        time = self.visitTimeIdentifier(ctx.timeIdentifier())
        return "{} = heat({}, {}, {});".format(name, name, temp['quantity'], time['quantity'])

    def visitSplit(self, ctx: BSParser.SplitContext):
        return "split({}, {})".format(self.check_identifier(ctx.IDENTIFIER().__str__()),
                                      ctx.INTEGER_LITERAL().__str__())

    def visitDispense(self, ctx: BSParser.DispenseContext):
        return "dispense({})".format("INSERT_NAME")

    def visitDispose(self, ctx: BSParser.DisposeContext):
        name = self.check_identifier(ctx.IDENTIFIER().__str__())
        return "drain({});".format(name)

    def visitExpression(self, ctx: BSParser.ExpressionContext):
        if ctx.primary():
            return self.visitPrimary(ctx.primary())
        else:
            exp1 = self.visitExpression(ctx.expression(0))
            exp2 = self.visitExpression(ctx.expression(1))
            if ctx.MULTIPLY():
                op = "*"
            elif ctx.DIVIDE():
                op = "/"
            elif ctx.ADDITION():
                op = "+"
            elif ctx.SUBTRACT():
                op = "-"
            elif ctx.AND():
                op = "&&"
            elif ctx.EQUALITY():
                op = "=="
            elif ctx.GT():
                op = ">"
            elif ctx.GTE:
                op = ">="
            elif ctx.LT():
                op = "<"
            elif ctx.LTE():
                op = "<="
            elif ctx.NOTEQUAL():
                op = "!="
            elif ctx.OR():
                op = "||"
            else:
                op = "=="

            if ctx.LBRACKET():
                output = "{}[{}]".format(exp1, exp2)
            else:
                output = "{}{}{}".format(exp1, op, exp2)

            return output

    def visitParExpression(self, ctx: BSParser.ParExpressionContext):
        return "({})".format(self.visitExpression(ctx.expression()))

    def visitMethodCall(self, ctx: BSParser.MethodCallContext):
        output = "{}(".format(ctx.IDENTIFIER().__str__())
        if ctx.expressionList():
            output += "{}".format(self.visitExpressionList(ctx.expressionList()))
        output += ")"
        return output

    def visitExpressionList(self, ctx: BSParser.ExpressionListContext):
        output = ""
        for expr in ctx.expression():
            output += "{}, ".format(self.visitExpression(expr))
        output = output[:-2]
        return output

    def visitTypeType(self, ctx: BSParser.TypeTypeContext):
        return super().visitTypeType(ctx)

    def visitUnionType(self, ctx: BSParser.UnionTypeContext):
        return super().visitUnionType(ctx)

    def visitTypesList(self, ctx: BSParser.TypesListContext):
        return super().visitTypesList(ctx)

    def visitArrayInitializer(self, ctx: BSParser.ArrayInitializerContext):
        return ctx.INTEGER_LITERAL()

    def visitLocalVariableDeclaration(self, ctx: BSParser.LocalVariableDeclarationContext):
        name = ctx.IDENTIFIER().__str__()
        variable = self.symbol_table.get_variable(name, self.scope_stack[-1])
        type_def = ""
        if not variable.is_declared:
            type_def = self.get_types(variable.types)
            variable.is_declared = True
        return "{} {} = {};".format(type_def, self.check_identifier(name), self.visit(ctx.assignmentOperations()))

    def visitPrimary(self, ctx: BSParser.PrimaryContext):
        if ctx.IDENTIFIER():
            if not self.symbol_table.get_variable(ctx.IDENTIFIER().__str__()):
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

    def visitPrimitiveType(self, ctx: BSParser.PrimitiveTypeContext):
        return super().visitPrimitiveType(ctx)

    def get_types(self, types):
        if ChemTypes.MAT in types:
            return "mat"
        else:
            return "double"

    def build_structs(self):
        output = "struct mat {double quantity;};" + self.nl
        output += "struct splitMat{mat values[100];};" + self.nl
        output += "struct module{int x, y;};" + self.nl

        return output

    def build_functions(self):
        output = "mat mix(mat input1, double input1_quantity, mat input2, " \
                 "double input2_quantity, double quantity) {" + self.nl
        output += "mat output;" + self.nl
        output += "output.quantity = input1.quantity + input2.quantity;" + self.nl
        output += "input1.quantity -= input1_quantity;" + self.nl
        output += "input2.quantity -= input2_quantity;" + self.nl
        output += "sleep(quantity);" + self.nl
        output += "return output;" + self.nl
        output += "}}{}{}".format(self.nl, self.nl)

        output += "mat split(mat input, int quantity) {" + self.nl
        output += "splitMat output;" + self.nl
        output += "for (int x =0; x < quantity; x++) {" + self.nl
        output += "output.values[x] = input;" + self.nl
        output += "output.values[x].quantity = input.quantity/(float)quantity;" + self.nl
        output += "}" + self.nl
        output += "return output.values[0];" + self.nl
        output += "}}{}{}".format(self.nl, self.nl)

        output += "mat heat(mat input, double temp, double time) {" + self.nl
        output += "sleep(time);" + self.nl
        output += "return input;" + self.nl
        output += "}}{}{}".format(self.nl, self.nl)

        output += "double detect(module detect, mat input, double quantity) {" + self.nl
        output += "sleep(quantity);" + self.nl
        output += "return -1.0;" + self.nl
        output += "}}{}{}".format(self.nl, self.nl)

        output += "mat dispense(mat input, double quantity) {" + self.nl
        output += "mat output = input;" + self.nl
        output += "output.quantity = quantity;" + self.nl
        output += "return input;" + self.nl
        output += "}}{}{}".format(self.nl, self.nl)

        output += "void drain(mat input) {" + self.nl
        output += "}}{}{}".format(self.nl, self.nl)

        return output
