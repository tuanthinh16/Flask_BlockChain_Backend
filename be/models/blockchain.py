from datetime import datetime

from models.block import Block
from pymongo import MongoClient

client = MongoClient("localhost:27017")
db = client.DATN_data

class Block_Chain:
    dificulty = 2
    def __init__(self):
        self.chain= self.create_root_block()  
    def create_root_block(self):
        time = datetime.now()
        list_block = []
        for item in db.block.find({'_id':0}):
            if item:
                list_block.append(Block(0,item['timestamp'],item['data']))
            else:
                list_block.append(Block(0,time,{'ADMIN create forum'}))
        return list_block

    def get_latest_block(self):
        listID = []
        for item in db.block.find():
            listID.append(item['_id'])
        lastestID = max(listID)
        for item in db.block.find({'_id':lastestID}):
            return item

    def add_block(self, new_block):
        new_block.pre_hash = self.get_latest_block()['hash']
        new_block.hash = new_block.mine_block(Block_Chain.dificulty)
        self.chain.append(new_block)

    def check_valid(self):
        for x in range(1, len(self.chain)):
            if self.chain[x].hash != self.get_latest_block().caculate_hash():
                return False
            if self.chain[x].pre_hash != self.chain[x-1].caculate_hash():
                return False
        return True
    #