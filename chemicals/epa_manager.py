import json
import sys
import logging
import re
from enums.consequence import Consequence

class EpaManager(object):

    def __init__(self, sparse_matrix_file_name, interpretation_file_name):
        #self.sparse_matrix = self.create_sparse_matrix(sparse_matrix_file_name)
        self.interpretation = self.create_2D_dict(interpretation_file_name)


    def create_2D_dict(self, file_name):
        regex = re.compile(r'[0-9]+')
        value = dict()

        file_read = open(file_name)
        for line in (file_read.readlines()[1:]):
            match = regex.findall(line)
            x = int(match[0])
            y = int(match[1])
            rest = set(map(int, match[2:]))
            if x not in value:
                value[x] = {y:rest}
            else:
                value[x].update({y:rest})
        
        return value


    def create_sparse_matrix(self, file_name):
        json_parsed_struct = []
        sparse_matrix      = {}

        with open(file_name) as file_read:
            json_parsed_struct = json.loads(file_read.read())['chemicalgroups']['group']

        for json_item in json_parsed_struct:
            if 'reactivegroups' in json_item and json_item['reactivegroups'] != None and len(json_item['reactivegroups']) != 0:
                key   = int(json_item['id'])
                value = dict(map(lambda x: (int(x['id']), {'outcome': x['outcome']}), \
                        filter(lambda y: 'id' in y and 'outcome' in y, json_item['reactivegroups']['reaction'])))
                sparse_matrix[key] = value
        return sparse_matrix


    def check_sparse_matrix(self, x, y):
        return x in self.sparse_matrix and y in self.__sparse_matrix[x]


    def for_each_sparse_matrix_item(self, f):
        for x, yy in self.sparse_matrix.items():
            for y, c in yy.items():
                f(x, y, c)


    def get_sparse_matrix_reaction(self, x, y):
        val = self.sparse_matrix[x][y]['outcome']
        if val == 'N':
            return Consequence.INCOMPATIBLE
        elif val == 'C':
            return Consequence.CAUTION
        elif val == 'SR':
            return Consequence.SELF_REACTIVE
        else:
            return Consequence.UNKNOWN


    def get_sparse_matrix_at_index(self, x, y):
        return self.sparse_matrix[x][y]


    def look_up_types(self, types):
        results = set()
        for t1 in types:
            for t2 in types:
                results.update(self.look_up_a_b(t1, t2))

        return results


    def look_up_a_b(self, a, b):
        if a > b:
            a, b = b, a

        if a in self.sparse_matrix and b in self.sparse_matrix[a]:
            return set(map(Consequence.get_type_from_id, self.sparse_matrix[a][b]['outcome']))
        else:
            return {Consequence.get_type_from_id(a), Consequence.get_type_from_id(b)}

