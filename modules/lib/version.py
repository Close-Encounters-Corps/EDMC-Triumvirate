
class Version:
    def __init__(self, value: str):
        self.raw_value = value
        self.values = [int(x) for x in value.split(".")]

    def __eq__(self, other):
        if not isinstance(other, Version):
            return False
        return self.values == other.values

    def __lt__(self, other):
        if not isinstance(other, Version):
            raise TypeError("Version can be compared only with other version.")
        if len(self.values) > len(other.values):
            return False
        for i, val in enumerate(self.values):
            if val < other.values[i]:
                # другая версия больше текущей
                return True
        return False
        

    def __repr__(self):
        return "{}({!r})".format(self.__class__.__name__, self.raw_value)