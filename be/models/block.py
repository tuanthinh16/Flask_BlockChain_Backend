from base64 import decode
from datetime import datetime
import json
import hashlib

class Block:
    indexx= 0
    def __init__(self,blockID,timestamp, data,pre_hash=""):
        self.blockID = blockID
        self.timestamp = timestamp
        self.data = data
        self.pre_hash = pre_hash
        self.hash = self.caculate_hash()

    def caculate_hash(self):
        data = str(self.blockID) + str(self.timestamp) + str(self.pre_hash) +str(self.data)+ str(self.indexx)
        decode = data.encode('utf-8')
        rs = hashlib.sha256(decode).hexdigest()
        return rs
    #proof of work for caculate_hash
    def mine_block(self,difficulty):
        value = self.caculate_hash()
        tmp = ""
        for x in range(0,difficulty):
            tmp += "0"
        while value[0:difficulty] != tmp:
            self.indexx += 1
            value = self.caculate_hash()
        print("Need: "+str(self.indexx)+" times to find block. \n")
        self.hash = value
        return value