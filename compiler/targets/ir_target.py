from compiler.data_structures import program as prog
from compiler.data_structures.ir import IRInstruction as iri
from compiler.data_structures.ir import InstructionSet
from compiler.data_structures.writable import Writable, WritableType
from compiler.targets.base_target import BaseTarget


class IRTarget(BaseTarget):

    def __init__(self, program: prog.Program, name="IRTarget"):
        super().__init__(program, name)
        self.compiled = ""
        self.tab = ""
        self.tab_count = 0

    def increment_tab(self):
        self.tab_count += 1
        self.tab += "\t"

    def decrement_tab(self):
        self.tab_count -= 1
        if self.tab_count < 0:
            self.tab_count = 0
        self.tab = "".join("\t" for x in range(self.tab_count))

    def transform(self):
        for root in self.program.functions:
            for nid, block in self.program.functions[root]['blocks'].items():
                self.compiled += block.label.label + ":\n"
                self.increment_tab()
                for iid, instruction in enumerate(block.instructions):
                    self.compiled += self.tab
                    if instruction.op == iri.SPLIT:
                        self.compiled += "{}[{}] = {}({}".format(instruction.defs['name'], instruction.split_size,
                                                             instruction.op.name.lower(), instruction.uses[0]['name'])
                        if instruction.uses[0]['offset'] != -1:
                            self.compiled += "[{}]".format(instruction.uses[0]['offset'])
                        self.compiled += ", {})".format(instruction.split_size)
                    elif instruction.op == iri.DISPOSE or instruction.op == iri.STORE:
                        self.compiled += "{}({}[{}])".format(instruction.op.name.lower(), instruction.uses[0]['name'],
                                                             instruction.uses[0]['offset'])
                    elif instruction.op == iri.CONSTANT:
                        self.compiled += "{}[{}] = {}".format(instruction.defs['name'],
                                                              instruction.defs['offset'], instruction.value)
                    elif instruction.op == iri.PHI:
                        self.compiled += f"PHI {instruction.defs['name']} = {{"
                        self.compiled += ",".join(instruction.uses)
                        self.compiled += "}"
                    elif instruction.op == iri.MATH:
                        self.compiled += "{}[{}] = ".format(instruction.defs['name'], instruction.defs['offset'])
                        use_1 = self.program.symbol_table.get_symbol(instruction.uses[0]['name'], root)
                        use_2 = self.program.symbol_table.get_symbol(instruction.uses[1]['name'], root)
                        if "CONST_" in use_1.name:
                            self.compiled += "{}".format(use_1.value.value[instruction.uses[0]['offset']])
                        else:
                            self.compiled += "{}[{}]".format(use_1.name, instruction.uses[0]['offset'])
                        self.compiled += " {} ".format(instruction.operand.get_string())
                        if "CONST_" in use_2.name:
                            self.compiled += "{}".format(use_2.value.value[instruction.uses[1]['offset']])
                        else:
                            self.compiled += "{}[{}]".format(use_2.name, instruction.uses[1]['offset'])
                    elif instruction.op in InstructionSet.assignment and instruction.op != iri.CALL:
                        # There is only one def.
                        self.compiled += "{}[{}] = {}(".format(instruction.defs['name'],
                                                               instruction.defs['offset'], instruction.op.name.lower())
                        # Grab the uses.
                        for use in instruction.uses:
                            if self.program.symbol_table.is_global(use['name']):
                                self.compiled += use['name'] + ", "
                            else:
                                self.compiled += "{}[{}], ".format(use['name'], use['offset'])
                        # Get rid of trailing characters
                        self.compiled = self.compiled[:-2]
                        self.compiled += ")"
                    elif instruction.op == iri.CONDITIONAL:
                        use_1 = self.program.symbol_table.get_symbol(instruction.uses[0]['name'], root)
                        use_2 = self.program.symbol_table.get_symbol(instruction.uses[1]['name'], root)
                        self.compiled += "if "
                        if "CONST_" in use_1.name:
                            self.compiled += "{}".format(use_1.value.value[instruction.left['offset']])
                        else:
                            self.compiled += "{}[{}]".format(use_1.name, instruction.left['offset'])
                        self.compiled += " {} ".format(instruction.relop.get_readable())
                        if "CONST_" in use_2.name:
                            self.compiled += "{}".format(use_2.value.value[instruction.right['offset']])
                        else:
                            self.compiled += "{}[{}]".format(use_2.name, instruction.right['offset'])
                        self.compiled += "{}|{}true: jump {}{}|{}false: jump {}".format(self.tab, self.tab,
                                                                                        instruction.true_branch.label,
                                                                                        self.tab,
                                                                                        self.tab,
                                                                                        instruction.false_branch.label)
                    elif instruction.op == iri.HEAT:
                        self.compiled += "{}({}[{}])".format(instruction.op.name.lower(), instruction.uses[0]['name'],
                                                             instruction.uses[0]['offset'])
                    elif instruction.op == iri.CALL:
                        uses = ""
                        if instruction.uses:
                            for use in instruction.uses:
                                uses += use['name']
                                if use['offset'] >= 0:
                                    uses += "[{}], ".format(use['offset'])
                            uses = uses[:-2]
                        else:
                            uses = ""
                        self.compiled += "_{}_ {}".format(instruction.op.name.lower(), instruction.defs['name'])
                        if instruction.defs['offset'] != -1:
                            self.compiled += "[{}]".format(instruction.defs['offset'])
                        self.compiled += " = {}({})".format(instruction.function.name, uses)
                    elif instruction.op == iri.RETURN:
                        self.compiled += "^{}^ {}".format(instruction.op.name.lower(), instruction.defs['name'])
                        if instruction.defs['offset'] != -1:
                            self.compiled += "[{}]".format(instruction.defs['offset'])
                    elif instruction.op == iri.NOP:
                        self.compiled += "NOP"
                    # Add any meta operations.
                    if instruction.meta:
                        for meta in instruction.meta:
                            if meta.name == "USEIN":
                                self.compiled += " usein {}{}".format(meta.quantity, meta.unit.name)
                            else:
                                self.compiled += " @ {}{}".format(meta.quantity, meta.unit.name)

                    self.compiled += "\n"
                if block.jumps:
                    for jump in block.jumps:
                        if jump:
                            self.compiled += self.tab + "jump: " + jump.label + "\n"
                self.decrement_tab()

            if self.config.write_cfg:
                self.program.write['cfg'] = Writable(self.program.name,
                                                     f"{self.config.output}/{self.program.name}_{root}_dag.dot",
                                                     self.program.bb_graph, WritableType.GRAPH)

        self.program.write[self.program.name] = Writable(self.program.name,
                                                         "{}/{}.ir".format(self.config.output, self.program.name),
                                                         self.compiled)

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
