class History:
    def __init__(self,id='',username='',blockID='',hash='',methods='',timestamp='',fromusr='',value='',to=''):
        self.id = id
        self.username = username
        self.blockID = blockID
        self.hash = hash
        self.methods = methods
        self.timestamp = timestamp
        self.fromusr = fromusr
        self.value = value
        self.to = to
    def visible(self):
        return{
            "ID": self.id,
            "BlockID": self.blockID,
            "Timestamp": self.timestamp,
            "Username": self.username,
            "Hash": self.hash,
            "Methods": self.methods,
            "From User": self.fromusr,
            "To User": self.to,
            "value": self.value
        }