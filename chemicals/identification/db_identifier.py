from chemicals.identification.identifier import Identifier
from shared.bs_exceptions import IdentificationException
from shared.enums.bs_properties import *
from shared.enums.config_flags import IdentifyLevel
from shared.variable import *


class DBIdentifier(Identifier):

    def __init__(self, level: IdentifyLevel, db):
        super().__init__(level)
        self.db = db

    def identify(self, search_for: str, types: set = frozenset(), scope: str = "", volume: float = 10.0,
                 units: BSVolume = BSVolume.MICROLITRE) -> Variable:
        self.log.fatal("DB Identifier isn't functioning correctly.")
        var = Chemical(search_for, {ChemTypes.UNKNOWN})
        return var

    # fix(daniel): figure out if there is a way to prevent exceptions from firing...
    def is_name(self, string):
        try:
            cursor = self.db.sql_query('SELECT name FROM chemicals WHERE name = {0};'.format(string))
            cursor.close()
            return True
        except IdentificationException:
            return False

    def is_pub_chem_id(self, string):
        try:
            cursor = self.db.sql_query('SELECT * FROM chemicals WHERE pubchem_id = {0}'.format(string))
            cursor.close()
            return True
        except IdentificationException:
            return False

    def search_by_cas_number(self, string):
        cursor = self.db.sql_query('SELECT * FROM cas_numbers WHERE cas_number_string = {0}'.format(string))
        return cursor.fetchall()

    def search_by_inchi_key(self, string):
        cursor = self.db.sql_query('SELECT * FROM chemicals WHERE inchi_key = {0}'.format(string))
        return cursor.fetchall()

    def search_by_smiles(self, string):
        cursor = self.db.sql_query(
            'SELECT * FROM chemicals WHERE isomeric_smiles = {0} OR canonical_smiles = {0}'.format(string))
        return cursor.fetchall()

    def search_by_pub_chem_id(self, string):
        cursor = self.db.sql_query('SELECT * FROM chemicals WHERE pubchem_id = {0}'.format(string))
        return cursor.fetchall()

    def search_by_aliases(self, string):
        raise NotImplementedError()
