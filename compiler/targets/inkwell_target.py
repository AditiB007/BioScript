import json
from collections import deque

import networkx as nx
from jsonschema import exceptions
from jsonschema import validate

from compiler.data_structures import Program
from compiler.data_structures.ir import *
from compiler.data_structures.writable import Writable, WritableType
from compiler.targets.base_target import BaseTarget
from shared.components import FlowType
from shared.components import get_component_api


class InkwellTarget(BaseTarget):

    def __init__(self, program: Program):
        super().__init__(program, "InkwellTarget")
        self.api = get_component_api(self.config)
        self.inputs = dict()
        # All components required for executing this program.
        self.components = dict()
        # All the connections between components.
        self.connections = dict()
        # The DAG node to component entity mapping.
        self.node_to_component = dict()

    def build_dags(self):
        """
        This is a modified DAG construction algorithm.
        The primary difference is that all vertices
        have an output var and consume something.
        :return:
        """

        for root in self.program.functions:
            self.dags[root] = dict()
            # This maps an output variable (key) to a node in the graph.
            instruction_uses = dict()
            # use_defs = defaultdict(lambda: {'uses': set(), 'defs': set()})
            no_defs = {IRInstruction.NOP, IRInstruction.CONDITIONAL}
            for nid, block in self.program.functions[root]['blocks'].items():
                graph = nx.MultiDiGraph()
                for instruction in block.instructions:
                    data = {'iid': instruction.iid, 'op': instruction.op, 'var': None, 'offset': -1}
                    all_uses = set()
                    all_defs = set()
                    if instruction.op not in no_defs:
                        '''
                        Add the defs to the graph.
                        '''
                        deff = self.program.symbol_table.get_symbol(instruction.defs['name'], root)
                        data['var'] = deff.name
                        if instruction.defs['offset'] >= 0:
                            name = "{}_{}".format(deff.name, instruction.defs['offset'])
                            data['offset'] = instruction.defs['offset']
                            graph.add_node(name, data=data)
                            all_defs.add(name)
                        else:
                            for x in range(deff.value.size):
                                name = "{}_{}".format(deff.name, x)
                                data['offset'] = x
                                graph.add_node(name, data=data)
                                all_defs.add(name)
                        '''
                        Add the uses to graph.
                        '''
                        for use in instruction.uses:
                            uze = self.program.symbol_table.get_symbol(use['name'], root)
                            data['var'] = uze.name
                            if use['offset'] >= 0:
                                name = "{}_{}".format(uze.name, use['offset'])
                                data['offset'] = use['offset']
                                graph.add_node(name, data=data)
                                all_uses.add(name)
                            else:
                                for x in range(uze.value.size):
                                    name = "{}_{}".format(uze.name, x)
                                    data['offset'] = x
                                    graph.add_node(name, data=data)
                                    all_uses.add(name)
                    '''
                    Build the edges between uses and defs.
                    '''
                    for u in all_uses:
                        for d in all_defs:
                            graph.add_edge(u, d, op=instruction.op, iid=instruction.iid, label=instruction.iid)

                if self.config.write_cfg:
                    self.program.write['cfg'] = Writable(self.program.name,
                                                         "{}/{}_{}_{}_dag.dot".format(self.config.output,
                                                                                      self.program.name, root, nid),
                                                         graph, WritableType.GRAPH)

                self.program.functions[root]['blocks'][nid].dag = graph
                self.dags[root][nid] = graph

    def transform(self):
        output = {'name': self.program.name.replace('/', '_').replace('.', '_'),
                  'layers': [{"id": "flow", "name": "flow"}],
                  'components': [], 'connections': []}
        if self.program.config.flow_type == FlowType.ACTIVE:
            output['layers'].append({'id': 'control', 'name': 'control'})
        sequences = dict()
        netlist = dict()
        for root in self.program.functions:
            sequences[root] = dict()
            for bid, block in self.program.functions[root]['blocks'].items():
                queue = deque()
                seen = set()
                connections = set()
                sequences[root][bid] = {"on": {}, "off": {}}

                # A dictionary of the nodes and their associated data.
                graph = dict(block.dag.nodes('data'))

                # This gets all the nodes with no incoming edges
                # These are the source nodes of a graph.
                # This is an initialization step.
                for node in block.dag.nodes:
                    if len(block.dag.in_edges(node)) == 0:
                        queue.append(node)

                # BFS!
                while queue:
                    current = queue.pop()
                    # The operation which uses the variable.
                    # Basically an outgoing edge.
                    operation = graph[current]['op']
                    # self.log.info("{} is a use of {}".format(current, operation.name))

                    # We need the variable that is used in this operation.
                    use = self.program.symbol_table.get_symbol(graph[current]['var'], root)
                    if not use:
                        self.log.fatal("{} not found in symbol table".format(current))
                        break

                    component_name = f"{current}_{operation.name}"
                    if component_name not in self.components:
                        # This particular node is a dispense node.
                        # self.log.info(component_name)
                        destination = self.build_component(component_name, 'flow', operation)
                        output['components'].append(destination)
                        self.components[component_name] = destination
                    else:
                        destination = self.components[component_name]

                    # self.log.debug(destination)

                    for out in block.dag.edges(current):
                        for index in block.dag[out[0]][out[1]]:
                            if out[0] == out[1]:
                                edge_op = block.dag[out[0]][out[1]][index]['op']
                                edge_component_name = f"{current}_{edge_op.name}"
                                if edge_component_name not in self.components:
                                    self.components[edge_component_name] = self.build_component(edge_component_name,
                                                                                                "flow", edge_op)

                    # Build the edges between the current node and incoming edges.
                    for ancestor in block.dag.in_edges(current):
                        # Keep the variable around, to make things a bit easier.
                        incoming = self.program.symbol_table.get_symbol(graph[ancestor[0]]['var'], root)
                        # Build the edge name.
                        edge = f"{ancestor[0]}_{graph[ancestor[0]]['op'].name}"
                        # self.log.error(edge)

                        # Verify that the component has been created.
                        if edge not in self.components:
                            self.components[edge] = self.build_component(edge, "flow", graph[ancestor[0]]['op'])
                        source = self.components[edge]
                        if f"{source['name']}|{destination['name']}" in {"b_1_mix|c_0_SPLIT", "a_1_MIX|c_0_SPLIT"}:
                            x = 1
                        # Build the connection between source and destination.
                        if ancestor[0] != current and f"{ancestor[0]}->{current}" not in connections:
                            connections.add(f"{ancestor[0]}->{current}")
                            connection = self.build_connection(source, destination, edge,
                                                               output['layers'][0]['id'],
                                                               incoming.scope == self.program.symbol_table.global_scope)
                            if connection['id'] in {"b_1_mix|c_0_SPLIT", "a_1_MIX|c_0_SPLIT"}:
                                x = 1
                            output['connections'].append(connection)
                        else:
                            self.log.info(f"Ignoring: {ancestor[0]}\t{current}")
                        if connection['id'] == 'b_1_MIX|c_0_SPLIT':
                            self.log.info(connection)
                        # if connection['id'] not in connections and ancestor[0] != current:

                    # output['components'].append(destination)
                    # self.components[use.name] = destination
                    # component_set[operation].add(destination['id'])
                    # Because there are loops, this must come before
                    # we add the out edges of a given node.
                    seen.add(current)
                    # Gather all the edges that leave this node and
                    # Add them to the queue if we haven't seen them.
                    # for out in block.dag.out_edges(var.name):
                    for out in block.dag.out_edges(current):
                        if out[1] not in seen:
                            queue.appendleft(out[1])

            self.log.info(self.components.keys())
            self.log.info(self.connections.keys())

            verified = self.verify_json(output, self.program.config.validate_schema)
            if verified:
                netlist[root] = output
            """
            The check happens here because this is a shared function.
            It has no access to the config object.
            """
            if self.config.debug and self.config.write_out:
                json_dag_name = "{}_{}_dag_from_json".format(self.program.name, root)
                self.program.write["json_graph"] = Writable(json_dag_name,
                                                            "{}/{}.dot".format(self.config.output, json_dag_name),
                                                            self.json_to_graph(output, root), WritableType.GRAPH)
        if self.config.flow_type == FlowType.ACTIVE:
            self.program.write['activations'] = Writable("{}_activations".format(self.program.name),
                                                         "{}/{}_activations.json".format(self.config.output,
                                                                                         self.program.name),
                                                         sequences, WritableType.JSON)
        for root in netlist:
            netlist_name = "{}_netlist_{}".format(self.program.name, root)
            self.program.write['{}_netlist_{}'] = Writable(netlist_name,
                                                           "{}/{}.json".format(self.config.output, netlist_name),
                                                           netlist[root], WritableType.JSON)

    def json_to_graph(self, spec, function_name):
        graph = nx.DiGraph()
        for component in spec['components']:
            graph.add_node(component['id'])
        for connection in spec['connections']:
            for sink in connection['sinks']:
                if 'source' in connection:
                    graph.add_edge(connection['source']['component'], sink['component'], label=connection['name'])
        return graph

    def verify_json(self, output: dict, verify: bool = False) -> bool:
        if verify:
            try:
                with open(self.program.config.schema) as f:
                    schema = json.load(f)
                validate(instance=output, schema=schema)
                self.log.debug("JSON validation successful")
                return True
            except exceptions.ValidationError as e:
                self.log.warning(str(e))
                return False

    def generate_activations(self, components: dict, component_set, dag, sinks) -> list:
        """
        :param components: inkwell json.
        :param component_set: Set of components available for selection.
        :param dag: multidigraph.MultiDiGraph.
        :param sinks:
        :return: List of timesteps and their activations.
        """

        def find_start(e, dispense_dict, mix_defs_dict):
            if e in dispense_dict:
                return dispense_dict[e]
            else:
                return mix_defs_dict[e]

        def find_end(sinks, paths):
            for s in sinks:
                if s in paths:
                    return s

        complete = set(range(1, len(dag.nodes)))
        mapping_names_to_graph = {}
        mapping_graph_to_names = {}
        print(dag.nodes, dag.edges)
        for i, data in dag.nodes('data'):
            op = data['op']
            if op == 'DISPOSE':
                mapping_names_to_graph[data['defs']] = i
                mapping_graph_to_names[i] = data['defs']
            elif op == 'MIX':
                mapping_names_to_graph[data['defs']] = i
                mapping_graph_to_names[i] = data['defs']
            elif op == 'SPLIT':
                pass
            elif op == 'HEAT':
                pass
            elif op == 'DISPENSE':
                key = None
                for s in data['uses']:
                    key = s
                    break
                mapping_graph_to_names[i] = key
                mapping_names_to_graph[key] = i
            else:
                print('hello',data)
                pass
        print('hey')
        print(dag.nodes, dag.edges)
        sink_names = set(map(lambda s: s[7:], sinks))
        sink_nums  = set(map(lambda s : mapping_names_to_graph[s], sink_names))
        timing = list()
        paths = {}

        # where start originates from...
        dispense_dict = {}
        mix_defs_dict = {}

        for block in self.program.functions['main']['blocks'].values():
            for instr in block.instructions:
                if type(instr) == Dispose:
                    t = {}
                    name = instr.uses[0].name
                    assert(name in mapping_names_to_graph)
                    node_num = mapping_names_to_graph[name]
                    for path in paths.values():
                        for pp in path.values():
                            if node_num in pp:
                                t['on'] = pp
                                t['off'] = complete - pp
                                break
                    assert(len(t['on']) != 0)
                    timing.append(t)
                elif type(instr) == Mix:
                    # schedule the 1st element to be mixed.
                    e = instr.uses[0].name
                    start = find_start(e, dispense_dict, mix_defs_dict)
                    end = find_end(sink_nums, paths[start])
                    t1 = {'on': paths[start][end], 'off': (complete - paths[start][end])}

                    # schedule closing of valves
                    t2 = {'on': set(), 'off': complete}

                    # schedule the 2nd element to be mixed.
                    e = instr.uses[1].name
                    start = find_start(e, dispense_dict, mix_defs_dict)
                    t3 = {'on': paths[start][end], 'off': (complete - paths[start][end])}

                    # append timings
                    timing.append(t1)
                    timing.append(t2)
                    timing.append(t3)

                    # picked an arbitary start node
                    mix_defs_dict[instr.defs.name] = start
                elif type(instr) == Split:
                    pass
                elif type(instr) == Heat:
                    pass
                elif type(instr) == Detect:
                    pass
                elif type(instr) == Dispense:
                    node_name = instr.uses[0].name
                    dispense_dict[instr.defs.name] = node_name
                    start = mapping_names_to_graph[node_name]
                    paths[node_name] = {}
                    for n, path in nx.single_source_shortest_path(dag, start).items():
                        if n not in sink_nums:
                            continue
                        paths[node_name][n] = set(path)
                else:
                    self.log.warning('Unhandled instruction')

        self.log.info("Generating activation sequences")
        for i, t in enumerate(timing):
            t['on'] = set(map(lambda x: mapping_graph_to_names[x], t['on']))
            t['on'] = list(t['on'])
            t['off'] = set(map(lambda x: mapping_graph_to_names[x], t['off']))
            t['off'] = list(t['off'])
            # self.log.info('t{}:   {}'.format(i, t))
        return timing

    def build_schedule(self, dag: nx.DiGraph, with_dispense: bool = False):
        schedule = list(nx.algorithms.dag.topological_sort(dag))
        graph = dict(dag.nodes("data"))
        # Filter out the dispenses if necessary.
        if not with_dispense:
            temp = list()
            for node in schedule:
                if not graph[node]['op'].lower() == 'dispense':
                    temp.append(node)
            schedule = temp
        return schedule

    def build_component(self, name, layer: str, op: IRInstruction = IRInstruction.MIX, splits: int = 1):
        """
        This builds the attributes required for defining
        a component on a continuous flow device.
        :param name: Unique identifier of the component to be found,
            note: this is a composite of function name, basic block name,
            op name, and emitting variable name.
        :param layer: Which layer does this operation occur on.
        :param op: What is the operation.
        :param splits: If it's a split, how many?
        :return: The created component.
        """
        if op.name == 'DISPENSE':
            out = self.api.build_component({'taxonomy': 'input', 'uuid': layer, 'name': name, 'splits': splits,
                                            'flow': self.program.config.flow_type})
            self.inputs[name] = out
        else:
            out = self.api.build_component({'taxonomy': op.name, 'uuid': layer, 'name': name, 'splits': splits,
                                            'flow': self.program.config.flow_type})
        # Each port must have it's own connections, so we list all the ports here.
        self.log.debug(f"Building ports for {name}")
        self.connections[name] = set(n['label'] for n in out['ports'])
        return out

    def build_connection(self, source: dict, destination: dict, name: str, layer: str,
                         source_global: bool = False) -> dict:
        """
        Builds a connection between two components.
        :param source: Source component ID.
        :param destination: Destination component ID.
        :param name: Name of connection.
        :param layer: What layer does this belong on?
        :param source_global: Is the source a global variable?
        :return: A dictionary forming the connection.
        """
        connection = dict()
        connection['id'] = f"{source['name']}|{destination['name']}"
        if connection['id'] == 'a_1_MIX|c_0_SPLIT':
            x = 1
        connection['layer'] = layer
        connection['name'] = name
        connection['sinks'] = list()
        label = None
        for p in source['ports']:
            if 'output' in p['label'] and p['label'] in self.connections[source['name']]:
                label = p['label']
                if not source_global:
                    self.connections[source['name']].remove(label)
                break
        connection['source'] = {'component': source['id'], 'port': label if label is not None else "none"}
        label = None
        for p in destination['ports']:
            if 'input' in p['label'] and p['label'] in self.connections[destination['name']]:
                label = p['label']
                self.connections[destination['name']].remove(label)
                break
        connection['sinks'].append({'component': destination['id'], 'port': label if label is not None else "none"})

        return connection

    def get_machine_code(self):
        return {}

    def write_mix(self) -> str:
        return "oh, you know!"

    def write_dispense(self) -> str:
        return "something"

    def write_split(self) -> str:
        pass

    def write_detect(self) -> str:
        pass

    def write_dispose(self) -> str:
        pass

    def write_expression(self) -> str:
        pass

    def write_branch(self) -> str:
        pass
