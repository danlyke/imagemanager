class subscriptable :
    def __init__(self):
        self.data = {}
    def has_key(self, k) :
        return self.data.has_key(k)
    def __getitem__(self, k):
        return self.data[k]
    def __setitem__(self, k, v):
        self.data[k] = v
        


class abc :
    def __init__(self):
        print "def abc::__init__(self):"
    def abc(self):
        print "def abc::abc(self):"
    def pdq(self):
        print "def abc::pdq(self):"

class xyz(abc) :
    def __init__(self):
        abc.__init__(self)
        print "def xyz::__init__(self):"
    def pdq(self):
        print "def xyz::pdq(self):"


