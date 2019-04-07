# from compiler.data_structures import Program
from compiler.targets.base_target import BaseTarget
from chemicals.chemtypes import ChemTypes
from compiler.data_structures.variable import *
from compiler.data_structures.ir import *



class ClangTarget(BaseTarget):

    def __init__(self, program: 'Program', inline=False):
        super().__init__(program, "ClangTarget", inline)
        # This *should* be moved into the LLVM target...
        self.keywords = ('alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel', 'atomic_commit',
                         'atomic_noexcept', 'auto', 'bitand', 'bitor', 'bool', 'break', 'case', 'catch', 'char',
                         'char16_t', 'char32_t', 'class', 'compl', 'concept', 'const', 'constexpr', 'const_cast',
                         'continue', 'co_await', 'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do',
                         'double', 'dynamic_cast', 'else', 'enum', 'explicit', 'export', 'extern', 'false', 'float',
                         'for', 'friend', 'goto', 'if', 'import', 'inline', 'int', 'long', 'module', 'mutable',
                         'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq',
                         'private', 'protected', 'public', 'reflexpr', 'register', 'reinterpret_cast', 'requires',
                         'return', 'short', 'signed', 'sizeof', 'static', 'static_assert', 'static_cast', 'struct',
                         'switch', 'synchronized', 'template', 'this', 'thread_local', 'throw', 'true', 'try',
                         'typedef', 'typeid', 'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile',
                         'wchar_t', 'while', 'xor', 'xor_eq')


    def check_identifier(self, name):
        if name in self.keywords:
            return '{}{}'.format(name, name)
        else:
            return name

    @staticmethod
    def get_type_string(types : ChemTypes):
        '''
        Go through all the types in the set of return types,
        and determine the C++ equivalent of those types
        ''' 
        if ChemTypes.REAL in types:
            return 'double'
        elif ChemTypes.NAT in types:
            return 'double'
        elif ChemTypes.BOOL in types:
            return 'bool'
        elif ChemTypes.CONST in types:
            #don't know what to do here
            assert(False)
        elif ChemTypes.NULL in types or ChemTypes.UNKNOWN in types:
            #unknown type
            #
            return 'None'
        else:
            return 'mat'


    def construct_basic_block_code(self, instructions, inline=False):
        code = ''
        for instr in instructions:
            if type(instr) == Dispose:
                code += '  dispose({});\n'.format(instr.uses[0].name)
            elif type(instr) == Mix:
                code += '  mat {} = mix({}, {}, {}, {}, {});\n'.format(
                                            instr.defs.name, 
                                            instr.uses[0].name, 
                                            instr.uses[0].size, 
                                            instr.uses[1].name, 
                                            instr.uses[1].size,
                                            1000)  
            elif type(instr) == Split:
                        code += '  mat {} = split({}, {});\n'.format(
                                            instr.defs.name,
                                            instr.uses[0].name,
                                            instr.uses[0].size)
            elif type(instr) == Detect: 
                        code += '  double {} = detect({}, {}, {});\n'.format(instr.defs.name, instr.module.name, instr.uses[0].name, instr.module.size)
            elif type(instr) == Heat: 
                #(Daniel) I don't know what to fill in for temp or time...
                code += '  mat {} = heat({}, {}, {});\n'.format(instr.defs.name, instr.uses[0].name, instr.uses[0].size, instr.uses[0].size) 
            elif type(instr) == Dispense:
                        code += '  mat {} = dispense({}, {});\n'.format(instr.defs.name, instr.uses[0].name, instr.uses[0].size) 
            elif type(instr) == Return:
            
                if type(instr.return_value) == Chemical:
                    code += '  return {};\n'.format(instr.return_value.name)
                elif type(instr.return_value) == RenamedVar:
                    code += '  return {};\n'.format(instr.return_value.name)
                elif type(instr.return_value) == Number: 
                    code += '  return {};\n'.format(instr.return_value.value)
            elif type(instr) == Store:
                pass 
            elif type(instr) == Call:
                if inline == True:
                    ret = ClangTarget.get_type_string(instr.function.types)
                    code += self.inlined_code_block(instr.name, instr.defs.name)
                else:
                    ret = ClangTarget.get_type_string(instr.function.types)
                    args = ''
                    for arg in instr.args:
                        if args:
                            args += ', '+arg.name
                        else:
                            args = arg.name

                    code += '  {} {} = {}({});\n'.format(ret, instr.defs.name, instr.name, args)
            elif type(instr) == BinaryOps:
                pass
            else:
                pass
        return code


    def inlined_code_block(self, func_name, ret):
        '''
        alpha conversion of variables based on func_name e.g.
        a function fibonacci with a variable named "a" will
        have variable alpha converted to the name "fibonacci_a"
        '''
        func_info = self.program.symbol_table.functions[func_name]
        code = '  {} {};\n'.format(ClangTarget.get_type_string(func_info.types), ret)
        code += '  {\n    //inlined code\n'
        for arg in func_info.args:
            var_type = ClangTarget.get_type_string(arg.types)
            code += '    {} {}_{};//TODO: pass the parameters into the function\n'.format(var_type, func_name, arg.name)

        for block in self.program.functions[func_name]['blocks'].values():
            for instr in block.instructions:
                if type(instr) == Dispose:
                    code += '    dispose({}_{});\n'.format(func_name, instr.uses[0].name)
                elif type(instr) == Mix:
                    code += '    mat {}_{} = mix({}_{}, {}, {}_{}, {}, {});\n'.format(
                                                     func_name, instr.defs.name,
                                                     func_name, instr.uses[0].name,
                                                     instr.uses[0].size,
                                                     func_name, instr.uses[1].name,
                                                     instr.uses[1].size,
                                                     1000)
                elif type(instr) == Split:
                    code += '    mat {}_{} = split({}_{}, {});\n'.format(
                                             func_name, instr.defs.name,
                                             func_name, instr.uses[0].name,
                                             instr.uses[0].size)
                elif type(instr) == Detect:
                    code += '    double {}_{} = detect({}, {}_{}, {});\n'.format(
                                             func_name, instr.defs.name,
                                             instr.module.name,
                                             func_name, instr.uses[0].name,
                                             instr.module.size)
                elif type(instr) == Heat:
                    code += '    mat {}_{} = heat({}_{}, {}, {});\n'.format(
                                             func_name, instr.defs.name,
                                             func_name, instr.uses[0].name,
                                             instr.uses[0].size, instr.uses[0].size) 
                elif type(instr) == Dispense:
                    code += '    mat {}_{} = dispense({}_{}, {});\n'.format(
                                             func_name, instr.defs.name,
                                             func_name, instr.uses[0].name, instr.uses[0].size)
                elif type(instr) == Return:
                    if type(instr.return_value) == Chemical or type(instr.return_value) == RenamedVar:
                        code += '    {} = {}_{};\n'.format(
                                             ret, func_name, instr.return_value.name)
                    elif type(instr.return_value) == Number:
                        code += '    {} = {}_{};\n'.format(
                                             ret, func_name, instr.return_value.name) 
                elif type(instr) == Call:
                    #nested inlined functions currently not supported!!!
                    assert(False)
        code += '  }\n' 
        return code


    def transform(self):
        #TODO: fix when inlining is truly implemented
        INLINE = True 

        #a list of strings that represents all the function code
        self.function_code = []
        self.compiled = \
        '#include <unistd.h>\n' \
        '#include <vector>\n\n' \
        'struct mat {double quantity;};\n' \
        'struct splitMat{mat values[100];};\n' \
        'struct module{int x, y;};\n\n' \
        'mat mix(mat input1, double input1_quantity, mat input2, double input2_quantity, double quantity) {\n' \
        '  mat output;\n' \
        '  output.quantity = input1.quantity + input2.quantity;\n' \
        '  input1.quantity -= input1_quantity;\n' \
        '  input2.quantity -= input2_quantity;\n' \
        '  sleep(quantity);\n' \
        '  return output;\n' \
        '}\n\n' \
        'std::vector<mat> split(mat input, int quantity) {\n' \
        '  std::vector<mat> output;\n' \
        '  for (int x =0; x < quantity; x++) {\n' \
        '    output[x] = input;\n' \
        '    output[x].quantity = input.quantity/(float)quantity;\n' \
        '  }\n' \
        '  return output;\n' \
        '}\n\n' \
        'mat heat(mat input, double temp, double time) {\n' \
        '  sleep(time);\n' \
        '  return input;\n' \
        '}\n\n'\
        'double detect(module detect, mat input, double quantity) {\n' \
        '  sleep(quantity);\n' \
        '  return -1.0;\n' \
        '}\n\n' \
        'mat dispense(mat input, double quantity) {\n' \
        '  mat output = input;\n' \
        '  output.quantity = quantity;\n' \
        '  return input;\n' \
        '}\n\n' \
        'void dispose(mat a) {\n\n'\
        '}\n\n' \
        'void drain(mat input) {\n\n' \
        '}\n\n'

        #go through the globals and add module/manifest code.
        for name, v in self.program.symbol_table.globals.items():
            if ChemTypes.MAT in v.types:
                self.compiled += '{} {};\n'.format('mat', name)
            elif ChemTypes.MODULE in v.types:
                self.compiled += '{} {};\n'.format('module', name)
        self.compiled += '\n'

        if INLINE == True:
            self.compiled += 'int main(int argc, char const **argv) {\n'
            for block in self.program.functions['main']['blocks'].values():
                self.compiled += self.construct_basic_block_code(block.instructions, inline=INLINE)
            self.compiled += '}\n\n'
        else:
            code_func = []
            for func_name, function in self.program.functions.items():
                code = ''
                if func_name == 'main':
                    code = 'int main(int argc, char const **argv) {\n' 
                else:
                    func_info = self.program.symbol_table.functions[func_name]
                    ret = ClangTarget.get_type_string(func_info.types)
                    args = ''

                    for arg in func_info.args:
                        var_name = arg.name
                        var_type = ClangTarget.get_type_string(arg.types)
                        if args:
                            args += ', {} {}'.format(var_type, var_name)
                        else:
                            args = '{} {}'.format(var_type, var_name)

                    self.compiled += '{} {}({});\n\n'.format(ret, func_name, args)
                    code = '{} {}({}) '.format(ret, func_name, args) + '{\n'
                for block in function['blocks'].values(): 
                    code += self.construct_basic_block_code(block.instructions, inline=INLINE)
                code += '}\n\n'
                code_func.append(code)
 
            for c in code_func:
                self.compiled += c


        print(self.compiled)
        return False 

    def write_mix(self) -> str:
        pass

    def write_split(self) -> str:
        pass

    def write_detect(self) -> str:
        pass

    def write_dispose(self) -> str:
        pass

    def write_dispense(self) -> str:
        pass

    def write_expression(self) -> str:
        pass

    def write_branch(self) -> str:
        pass








