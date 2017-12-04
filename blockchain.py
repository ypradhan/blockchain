#!/usr/bin/python3

import datetime


class Block:

    def __init__(self, previous_hash=None, transactions=()):
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.this_hash = self.generate_hash()
        self.timestamp = datetime.datetime.now()
    

    def generate_hash(self):
        return hash((self.previous_hash,) + self.transactions)
   

    def __repr__(self):
        return "transactions: %s, timestamp: %s" % (str(self.transactions), str(self.timestamp))


class Chain:
    
    def __init__(self):
        genesis_block = Block()
        self.chain = [genesis_block]


    def register_block(self, transactions):
        self.chain.append(Block(self.chain[-1].this_hash, transactions))
    
    
    def __repr__(self):
        out = ""
        for block in self.chain:
            out += "%s\n" % str(block)
        return out
    

    def isvalid(self):
        for i, block in enumerate(self.chain):
            if not i: continue
            if block.previous_hash != self.chain[i-1].generate_hash():
                return False

        return True


if __name__ == "__main__":
    chain = Chain()
    chain.register_block((1, 2, 3,))
    chain.register_block((1, 2, 3, 4,))
    
    print(chain)
    print(chain.isvalid())
    
    l = list(chain.chain[1].transactions)
    l[1] = 11
    chain.chain[1].transactions = tuple(l)
    print(chain)
    print(chain.isvalid())
