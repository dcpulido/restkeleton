class Instance:

    def __init__(self,
                 dic={}):
        if dic != {}:
            self.set_by_dic(dic)

    def to_dict(self):
        toret = {}
        for k in self.__dict__.keys():
            if k != "__name__":
                toret[k] = self.__dict__[k]
        return toret

    def get_id(self):
        tt = {}
        for att in self._spec[self.__class__.__name__]:
            try:
                tt[att.keys()[0]] = self.to_dict[att]
            except:
                tt[att.keys()[0]] = ""
        return tt

    def set_by_dic(self,
                   arr):
        if len(self.to_dict().keys()) == 0:
            for k in arr.keys():
                aux = ""
                if type(arr[k]).__name__ == "datetime":
                    aux = str(arr[k])
                    setattr(self, k, aux)
                else: 
                    setattr(self, k, arr[k])
        for k in self.to_dict().keys():
            if k in arr.keys():
                if type(arr[k]).__name__ == "datetime":
                    aux = str(arr[k])
                    setattr(self, k, aux)
                else: 
                    setattr(self, k, arr[k])

