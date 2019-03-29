# from compiler.data_structures import Program
from compiler.targets.base_target import BaseTarget
from compiler.data_structures.variable import *
from chemicals.chemtypes import ChemTypes

class ClangTarget(BaseTarget):

    def __init__(self, program: 'Program'):
        super().__init__(program, 'ClangTarget')
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

        for t in types:
            if t == ChemTypes.REAL:
                assert(len(types)==1)
                return 'double'
            elif t == ChemTypes.NAT:
                assert(len(types)==1)
                return 'int'
            elif t == ChemTypes.BOOL:
                assert(len(types)==1)
                return 'bool'
            elif t == ChemTypes.CONST:
                #don't know what to do here
                assert(False)
            elif t == ChemTypes.NULL or t == ChemTypes.UNKNOWN:
                assert(False)
            else:
                return 'mat'


    def transform(self):

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
        for name, v in self.program.globals.items():
            if ChemTypes.MAT in v.types:
                self.compiled += '{} {};\n'.format('mat', name)
            elif ChemTypes.MODULE in v.types:
                self.compiled += '{} {};\n'.format('module', name)
        self.compiled += '\n'
        #add functions
        for root, function in self.program.functions.items():
            code = '' 
            if root == 'main':
                code += 'int main(int argc, char const **argv) {\n'
            else:
                function_data = self.program.symbol_table.functions[root]
                print(type(function_data.types))
                print(type(function_data.args))

                ret = ClangTarget.get_type_string(function_data.types)
                
                args = ''

                for arg in function_data.args:
                    val = ClangTarget.get_type_string(arg.types)
                    if args:
                        args += ', {} {}'.format(val, arg.name)
                    else:
                        args = '{} {}'.format(val, arg.name)


                #function header
                self.compiled += '{} {}({});\n\n'.format(ret, root, args) 
                #function body 
                code += '{} {}({})'.format(ret, root, args) + '{\n' 
            #go through each function
            for bid, block in function['blocks'].items():

                #used the 'instructions' from the block directly.
                for instr in block.instructions:
                    if instr.name == 'DISPOSE':
                        code += '  dispose({});\n'.format(instr.uses[0].name)
                    elif instr.name == 'MIX':
                        code += '  mat {} = mix({}, {}, {}, {}, {});\n'.format(
                                            instr.defs.name, 
                                            instr.uses[0].name, 
                                            instr.uses[0].size, 
                                            instr.uses[1].name, 
                                            instr.uses[1].size,
                                            1000)  
                    elif instr.name == 'SPLIT':
                        code += '  mat {} = split({}, {});\n'.format(
                                            instr.defs.name,
                                            instr.uses[0].name,
                                            instr.uses[0].size)
                    elif instr.name == 'DETECT':
                        code += '  double {} = detect({}, {}, {});\n'.format(instr.defs.name, instr.module.name, instr.uses[0].name, instr.module.size)
                    elif instr.name == 'HEAT':
                        #(Daniel) I don't know what to fill in for temp or time...
                        code += '  mat {} = heat({}, {}, {});\n'.format(instr.defs.name, instr.uses[0].name, instr.uses[0].size, instr.uses[0].size) 
                    elif instr.name == 'DISPENSE':
                        code += '  mat {} = dispense({}, {});\n'.format(instr.defs.name, instr.uses[0].name, instr.uses[0].size) 
                    elif instr.name == 'RETURN':

                        if type(instr.return_value) == Chemical:
                            code += '  return {};\n'.format(instr.return_value.name)
                        elif type(instr.return_value) == RenamedVar:
                            code += '  return {};\n'.format(instr.return_value.name)
                        elif type(instr.return_value) == Number: 
                            code += '  return {};\n'.format(instr.return_value.value)
                   
                    elif instr.name == 'STORE':
                        pass
            code += '}\n\n'

            self.function_code.append(code)

        for fn in self.function_code:
            self.compiled += fn 

        with open('stuff.cpp', 'w') as file:
            file.write(self.compiled)
        
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








