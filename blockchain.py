from block import Block
import datetime

block_chain = [Block.create_genesis_block()]

print("The Genesis Block Has Been Created !")
print("Hash: %s" % block_chain[-1].hash)

num_blocks_to_add = 10

for i in range(1, num_blocks_to_add + 1):
    block_chain.append(Block(block_chain[-1].hash, "DATA !", datetime.datetime.now()))
    
    print("Block #%d Has Been Created." % i)
    print("Block #%d Hash : %s" % (i, block_chain[i].hash))