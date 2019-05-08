import copy
import json
import uuid
from collections import deque

import networkx as nx
from jsonschema import exceptions
from jsonschema import validate

from compiler.data_structures import Program
from compiler.targets.base_target import BaseTarget
from shared.bs_exceptions import UnsupportedOperation
from shared.bs_junk_drawer import write_graph
from shared.components import FlowType
from shared.components import get_component_api

from compiler.data_structures.ir import *


class InkwellTarget(BaseTarget):

    def __init__(self, config: 'Config', program: Program):
        super().__init__(config, program, "InkwellTarget")
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
            var_defs = dict()
            var_uses = dict()
            instruction_defs = dict()
            instruction_uses = dict()
            used_defs = set()
            nodes = set()

            for nid, block in self.program.functions[root]['blocks'].items():
                graph = nx.MultiDiGraph()
                # Op nodes are defined as {output var, op}
                # Var nodes are defined as {var}
                for instruction in block.instructions:
                    instruction_defs[instruction.iid] = set()
                    instruction_uses[instruction.iid] = set()

                    if instruction.defs:
                        instruction_defs[instruction.iid].add(instruction.defs.name)
                        var_defs[instruction.defs.name] = instruction.iid
                    else:
                        raise UnsupportedOperation("Inkwell target does not support arithmetic math.")

                    for uses in instruction.uses:
                        if uses.name not in var_uses:
                            var_uses[uses.name] = list()
                        instruction_uses[instruction.iid].add(uses.name)
                        var_uses[uses.name].append(instruction.iid)

                    data = {'op': instruction.op.name, 'defs': instruction.defs.name,
                            'uses': instruction_uses[instruction.iid]}
                    graph.add_node(instruction.iid, data=data)

                    for use in instruction_uses[instruction.iid]:
                        if not self.program.symbol_table.is_global(use):
                            # graph.add_node(use)
                            if use not in used_defs:
                                used_defs.add(use)
                                if use not in var_defs:
                                    raise UnsupportedOperation("Inkwell target does not support arithmetic math.")
                                else:
                                    node = var_defs[use]
                            else:
                                node = var_uses[use][-2]
                            graph.add_edge(node, instruction.iid)
                        # else:
                        #     graph.add_edge(use, var_defs[instruction.defs.name])

                if self.config.write_cfg:
                    write_graph(graph, "{}_{}_dag.dot".format(root, nid))

                self.program.functions[root]['blocks'][nid].dag = graph
                self.dags[root][nid] = graph

    def transform(self, verify: bool = False):
        """
        Transform the IR into something Inkwell can understand.
        :param verify:
        :return:
        """
        uid = uuid.uuid5(uuid.NAMESPACE_OID, self.program.name)
        output = {'name': self.program.name.replace('/', '_').replace('.', '_'),
                  'layers': [{"id": str(uid), "name": "flow"}, {"id": "x", "name": "control"}],
                  'components': [], 'connections': []}
        sequences = dict()
        component_set = dict()
        for root in self.program.functions:
            sequences[root] = dict()
            for bid, block in self.program.functions[root]['blocks'].items():
                queue = deque()
                seen = set()
                connections = set()
                globalz = dict()
                sequences[root][bid] = {"on": {}, "off": {}}
                sinks = set()

                # This gets all the nodes with no incoming edges
                # These are the source nodes of a graph.
                # This is an initialization step.
                for node in block.dag.nodes:
                    if len(block.dag.in_edges(node)) == 0:
                        queue.append(node)

                # A dictionary of the nodes and their associated data.
                graph = dict(block.dag.nodes('data'))

                # BFS!
                while queue:
                    current = queue.pop()
                    operation = graph[current]['op']
                    if operation not in component_set:
                        component_set[operation] = set()
                    # We use the def iff the def is not a global.
                    # If it's a global, then we need the dispense
                    # port for this to work correctly.
                    var = self.program.symbol_table.get_variable(graph[current]['defs'], root)
                    # Stop if we couldn't find the variable.
                    if not var:
                        break
                    # destination_op = graph[var.name]
                    if var.name not in self.components:
                        use = self.program.symbol_table.get_local(copy.deepcopy(graph[current]['uses']).pop(), root)
                        # This amounts to a unique identifier for each component generated.
                        # name = self.build_name(root, bid, graph[current]['op'], use.name)
                        if not use:
                            break
                        # The check to see if this is a global use.
                        # If it's not a global, then the original def
                        # Is used for this.
                        if use.is_global:
                            globalz[var.name] = use
                            var = use
                        # If we haven't seen this (global or def) before,
                        # Then we need to create it.  This happens twice
                        # because the global may alter things.
                        if var.name not in self.components:
                            destination = self.build_component(var.name, "flow", graph[current]['op'], splits=var.size)
                            destination_name = "{}_{}".format(destination['entity'], var.name)
                            if graph[current]['op'] in {'DISPOSE', 'OUTPUT'}:
                                sinks.add(destination_name)
                            output['components'].append(destination)
                            self.components[var.name] = destination
                            component_set[operation].add(destination['id'])
                    else:
                        destination = self.components[var.name]
                        destination_name = "{}_{}".format(destination['entity'], var.name)

                    # All the edges that are coming into this
                    # node requires connections; build them.
                    # We should have seen *all* incoming edges,
                    # by now, which means we don't have to create.
                    # for ancestor in block.dag.in_edges(var.name):
                    for ancestor in block.dag.in_edges(current):
                        incoming = self.program.symbol_table.get_variable(graph[ancestor[0]]['defs'], root)
                        if self.program.symbol_table.is_global(ancestor[0]):
                            continue
                        # source_op = graph[incoming.name]
                        # incoming_name = self.build_name(root, bid, graph[current]['op'], incoming.name)
                        if incoming.name in globalz:
                            incoming = globalz[incoming.name]
                        if incoming.name not in self.components:
                            source = self.build_component(incoming.name, "flow", op=graph[incoming.name],
                                                          splits=incoming.size)
                            output['components'].append(source)
                            self.components[incoming.name] = source
                            component_set[operation].add(source['id'])
                        else:
                            source = self.components[incoming.name]
                        # This builds the maps of the components.
                        incoming_name = "{}_{}".format(source['entity'], incoming.name)
                        connection_name = "{}_{}".format(incoming.name, var.name)
                        if connection_name not in connections:
                            output['connections'].append(
                                self.build_connection(source, destination, connection_name, "flow", incoming.is_global))
                            connections.add(connection_name)

                    # Gather all the edges that leave this node and
                    # Add them to the queue if we haven't seen them.
                    # for out in block.dag.out_edges(var.name):
                    for out in block.dag.out_edges(current):
                        if out not in seen:
                            queue.appendleft(out[1])
                    # We've now seen this
                    seen.add(current)
                
                if self.config.flow_type == FlowType.ACTIVE:
                    activations = self.generate_activations(output, component_set, block.dag, sinks)
                    sequences[root][bid]['timing'] = activations

            verified = self.verify_json(output, True)
            if verified:
                self.json_to_graph(output)

    def json_to_graph(self, spec):
        graph = nx.DiGraph()
        for component in spec['components']:
            graph.add_node(component['id'])
        for connection in spec['connections']:
            for sink in connection['sinks']:
                graph.add_edge(connection['source']['component'], sink['component'])
        if self.config.write_cfg:
            write_graph(graph, "json.dag")

    def verify_json(self, output: dict, verify: bool = False) -> bool:
        if verify:
            try:
                #self.log.info(json.dumps(output, indent=4, separators=(',', ':')))
                with open('resources/parchmint_schema.json') as f:
                    schema = json.load(f)
                validate(instance=output, schema=schema)
                self.log.debug("JSON validation successful")
                return True
            except exceptions.ValidationError as e:
                self.log.warning(str(e))
                return False

    def generate_activations(self, components: dict, component_set, dag, sinks) -> dict:
        '''
        components=inkwell json.
        component_set=dispose, mix, dispense, etc.
        dag=multidigraph.MultiDiGraph
        sinks=output
        '''
        #TODO: this is hard-coded for mix.bs until a more general solution presents itself
        complete = set(range(1, len(dag.nodes)))
        mapping_names_to_graph = {'aaa':1, 'bbb':2, 'c0':3, 'c1':4}
        mapping_graph_to_names = {1:'aaa', 2:'bbb', 3:'c0', 4:'c1'}
        self.log.info(dag.nodes('data'))
        #TODO: need to handle multiple outputs...
        end_node_name = None
        for s in sinks:
            end_node_name = s[7:] # cut-off "output_"
            break
        end_node_num = mapping_names_to_graph[end_node_name]
        timing = list() 
        paths = {} 

        #where start originates from...
        dispense_dict = {}
        #TODO: dag.nodes('data') is NOT the instructions, its the data associated with the ndoes
        #TODO: could probably associate 
        for i, data in dag.nodes('data'):
            op = data['op']
            if op == 'DISPOSE':
                t = {'on':set(), 'off':set()}

                node_num = None
                name = None 
                for s in data['uses']:
                    name = s
                    break

                assert(name in mapping_names_to_graph)
                node_num = mapping_names_to_graph[name]

                #find an arbitrary path to dispose the chemical
                for path in paths.values():
                    #TODO: hard-coded until better solution
                    a = False 
                    for node in path:
                        if node == node_num:
                            a = True
                            break

                    if a:
                        t['on'] = set(path)
                        t['off'] = set(complete - t['on'])
                        break
                assert(len(t['on']) != 0)
                timing.append(t)

            elif op == 'MIX':
                ##TODO: does the order of the mix matters????? because
                ##obtaining the mix a with b is in an unordered set...

                #schedule the 1st element to be mixed.
                uses = list(data['uses'])
                e = uses[0] 
                start = dispense_dict[e]
                t1 = {'on': set(paths[start]), 'off': (complete - set(paths[start]))}

                #schedule closing of valves
                t2 = {'on': set(), 'off': complete}

                #schedule the 2nd element to be mixed.
                e = uses[1]
                start = dispense_dict[e]
                t3 = {'on': set(paths[start]), 'off': (complete - set(paths[start]))}

                #append timings
                timing.append(t1)
                timing.append(t2)
                timing.append(t3)

            elif op == 'SPLIT':
                pass
            elif op == 'HEAT':
                pass
            elif op == 'DISPENSE':
                node_name = None
                #get first element in set...retriving 1st element is ugly...
                for a in data['uses']:
                    node_name = a
                    break
                dispense_dict[data['defs']] = node_name

                #I assume the start node for the dispense is the beginning of the DAG
                start = mapping_names_to_graph[node_name]  
                paths[node_name] = nx.dijkstra_path(dag, start, end_node_num )
                print(nx.single_source_shortest_path(dag, start))
            else:
                self.log.warning('Unhandled instruction')

        self.log.info("Generating activation sequences")
        for i, t in enumerate(timing):
            t['on'] = set(map(lambda x: mapping_graph_to_names[x], t['on']))
            t['off'] = set(map(lambda x: mapping_graph_to_names[x], t['off']))
            self.log.info('t{}:   {}'.format(i, t))
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

    def build_component(self, name, layer: str, op: str = 'mix', splits: int = 1):
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
        if op == 'DISPENSE':
            out = self.api.build_component({'taxonomy': 'input', 'uuid': layer, 'name': name, 'splits': splits})
            self.inputs[name] = out
        else:
            out = self.api.build_component({'taxonomy': op, 'uuid': layer, 'name': name, 'splits': splits})
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
        connection['id'] = '{}|{}'.format(source['name'], destination['name'])
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
        connection['source'] = {'component': source['id'], 'port': label}
        label = None
        for p in destination['ports']:
            if 'input' in p['label'] and p['label'] in self.connections[destination['name']]:
                label = p['label']
                self.connections[destination['name']].remove(label)
                break
        connection['sinks'].append({'component': destination['id'], 'port': label})

        return connection

    def build_name(self, root: str, nid: int, op: str, variable):
        return "{}_{}_{}_{}".format(root, nid, op, variable)

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
