from chemicals.identification.identifier import Identifier


class NaiveIdentifier(Identifier):
    def __init__(self):
        Identifier.__init__(self)

    def identify_compound(self, name):
        return
