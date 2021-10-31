import hashlib
import datetime

class Block:
    def __init__(self, previous_block_hash, data, timestamp):
        self.previous_block_hash = previous_block_hash
        self.data = data
        self.timestamp = timestamp
        self.hash = self.get_hash()
        
    @staticmethod
    def create_genesis_block():
        return Block("0", "0", datetime.datetime.now())
    
    def get_hash(self):
        header_bin = (str(self.previous_block_hash) + str(self.data) + str(self.timestamp)).encode()
        
        inner_hash = hashlib.sha256(header_bin).hexdigest().encode()
        outer_hash = hashlib.sha256(inner_hash).hexdigest()
        return outer_hash