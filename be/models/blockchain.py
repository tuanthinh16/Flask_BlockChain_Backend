from datetime import datetime

from pymongo import MongoClient

import json
from base64 import decode
import hashlib

client = MongoClient("localhost:27017")
db = client.Data


class Block:
    indexx = 0

    def __init__(self, blockID, timestamp, data, pre_hash=""):
        self.blockID = blockID
        self.timestamp = timestamp
        self.data = data
        self.pre_hash = pre_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        data = (
            str(self.blockID)
            + str(self.timestamp)
            + str(self.pre_hash)
            + str(self.data)
            + str(self.indexx)
        )
        print("data at block :" + str(data))
        decode = data.encode("utf-8")
        rs = hashlib.sha256(decode).hexdigest()
        return rs

    # proof of work for caculate_hash
    def mine_block(self, difficulty):
        value = self.calculate_hash()
        tmp = ""
        for x in range(0, difficulty):
            tmp += "0"
        while value[0:difficulty] != tmp:
            self.indexx += 1
            value = self.calculate_hash()
        print("Need: " + str(self.indexx) + " times to find block. \n")
        self.hash = value
        return value


total = 0


class Block_Chain:
    dificulty = 0

    def __init__(self):
        self.chain = self.create_root_block()

    def get_latest_block(self):
        global total
        listID = []
        for item in db.block.find():
            listID.append(item["_id"])
        total = max(listID)
        for item in db.block.find({"_id": total}):
            return item

    def create_root_block(self):
        time = datetime.now()
        list_block = []
        for item in db.block.find({"_id": 0}):
            if item:
                list_block.append(Block(0, item["timestamp"], item["data"]))
            else:
                list_block.append(Block(0, time, {"ADMIN create forum"}))
        return list_block

    def add_block(self, new_block):
        self.chain.append(new_block)

    def calculate(self, block):
        data = (
            str(block.blockID)
            + str(block.timestamp)
            + str(block.pre_hash)
            + str(block.data)
            + str(block.indexx)
        )
        decode = data.encode("utf-8")
        rs = hashlib.sha256(decode).hexdigest()
        return rs

    def checkvaild(self, block):
        if block.pre_hash != self.get_latest_block()["hash"]:
            return False
        return True

    def check_valid(self):
        for x in range(1, len(self.chain)):
            if self.chain[x].hash != self.calculate(self.chain[x]):
                return False
            if self.chain[x].pre_hash != self.get_latest_block()["hash"]:
                return False
        return True

