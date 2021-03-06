import unittest
import datetime
import requests

from blockchain import Block, Chain, Node


class BlockTests(unittest.TestCase):
    """A block records transactions in a blockchain. Thus a block is like a
    page of a ledger or record book. Each time a block is 'completed', it
    gives way to the next block in the blockchain."""

    def test_genesis_block(self):
        """A genesis block is the first block of a block chain. Modern
        versions of Bitcoin number it as block 0, though very early versions
        counted it as block 1. The genesis block is almost always hardcoded
        into the software of the applications that utilize its block chain."""

        # An empty block is a genesis block.
        genesis_block = Block()
        self.assertTrue(genesis_block)

        # Following are attributes of a block and values for genesis block.
        self.assertEqual(genesis_block.previous_hash, None)
        self.assertEqual(genesis_block.transactions, [])
        self.assertEqual(type(genesis_block.timestamp), datetime.datetime)
        self.assertEqual(type(genesis_block.this_hash), int) # more on this hash calculation later


    def test_transaction_block(self):
        """Every new block uses the hash of the previous one and transactions
        within the block. It is meant to be completely unique and dependent on
        data from previous block.
            this_hash = hash(prev_block_hash, timestamp, transactions))"""
        genesis_block = Block()
        transactions = [1, 2, 3]
        transaction_block = Block(previous_hash=genesis_block.this_hash, transactions=transactions)

        self.assertTrue(transaction_block)
        self.assertEqual(transaction_block.previous_hash, genesis_block.this_hash)
        self.assertEqual(transaction_block.transactions, transactions)
        self.assertEqual(type(transaction_block.timestamp), datetime.datetime)
        self.assertTrue(transaction_block.timestamp > genesis_block.timestamp)


class BlockChainTests(unittest.TestCase):
    """A blockchain is a continuously growing list of blocks linked and secured
    using cryptography. By design, a blockchain is inherently immutable. It is
    "an open, distributed ledger that can record transactions between two
    parties efficiently and in a verifiable and permanent way"."""

    def test_chain(self):
        blockchain = Chain()
        self.assertTrue(blockchain)

        # First block in the chain is always a genesis block.
        self.assertEqual(len(blockchain), 1)
        self.assertEqual(type(blockchain[0]), Block)
        self.assertEqual(blockchain[0].previous_hash, None)
        self.assertEqual(blockchain[0].transactions, [])


    def test_add_block(self):
        blockchain = Chain()

        # A block is appended in the end of the list(chain).
        transactions1 = [1, 2, 3,]
        blockchain.register_block(transactions=transactions1)
        self.assertEqual(len(blockchain), 2)
        self.assertEqual(blockchain[-1].transactions, transactions1)

        transactions2 = [1, 2, 3, 4,]
        blockchain.register_block(transactions=transactions2)
        self.assertEqual(len(blockchain), 3)
        self.assertEqual(blockchain[-1].transactions, transactions2)

        # The hashes are maintained along the chain.
        self.assertEqual(blockchain[0].this_hash, blockchain[1].previous_hash)
        self.assertEqual(blockchain[1].this_hash, blockchain[2].previous_hash)


    def test_chain_validation(self):
        """A blockchain ledger should be immutable. To make sure we validate it
        by traversing through the chain to make sure previous hash of a block
        is indeed the hash of previous block."""
        blockchain = Chain()
        transactions1 = [1, 2, 3,]
        blockchain.register_block(transactions=transactions1)
        transactions2 = [1, 2, 3, 4,]
        blockchain.register_block(transactions=transactions2)
        self.assertTrue(blockchain.isvalid())

        # In case of any mutation the hash condition of the whole chain is invalid.
        blockchain[1].transactions[1] = 11
        self.assertFalse(blockchain.isvalid())


class NodeTests(unittest.TestCase):
    """A full node downloads the entire blockchain. Full nodes form the
    backbone of the system and keep the entire network honest. The full nodes
    basically validate the nodes and transactions and relay the information to
    the other nodes"""

    def test_node(self):
        node = Node()
        self.assertTrue(node)

        # Each node holds a copy of blockchain and address of their peers.
        self.assertEqual(type(node.chain), Chain)
        self.assertEqual(node.peers, set())


    def test_proof_of_work(self):
        """A proof-of-work is an economic measure to deter denial of service
        attacks and other service abuses such as spam on a network by requiring
        some work from the service requester, usually meaning processing time
        by a computer. It is done to verify an honest node in a network."""
        node = Node()
        proof_of_work = node.proof_of_work()
        self.assertTrue(proof_of_work>0)


    def test_mining(self):
        """Mining is the process of adding transaction records to the ledger.
        They are done by mining nodes. Transaction data are sent to them. They
        provide the proof of work and add blocks to the network."""
        node = Node()
        self.assertEqual(node.unmined_transactions, [])

        node.add_transaction(1)
        self.assertEqual(node.unmined_transactions, [1])
        node.add_transaction(2)
        self.assertEqual(node.unmined_transactions, [1, 2])
        self.assertEqual(len(node.chain), 1)
        node.mine()
        self.assertEqual(node.unmined_transactions, [])
        self.assertEqual(len(node.chain), 2)
        self.assertEqual(node.chain[1].transactions, [1, 2])

        node.add_transaction(3)
        node.mine()
        self.assertEqual(len(node.chain), 3)


class ConsensusTests(unittest.TestCase):

    def test1_node_chain(self):
        """Multiple decentralized nodes are live that hold and pass on the
        transactions."""
        r = requests.get('http://localhost:5000')
        data = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(data['chain'])
        self.assertEqual(data['chain_length'], 1)


    def test2_add_transaction(self):
        """Users add transactions to different nodes."""
        r = requests.post('http://localhost:5000/add_transaction', data={'transaction': 1})
        r = requests.post('http://localhost:5000/add_transaction', data={'transaction': 2})
        self.assertEqual(r.status_code, 201)

        r = requests.get('http://localhost:5000')
        data = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(data['unmined'])
        self.assertEqual(data['unmined_length'], 2)


    def test3_mine(self):
        """Nodes mine the transactions into blocks."""
        r = requests.get('http://localhost:5000/mine')
        self.assertEqual(r.status_code, 200)

        r = requests.get('http://localhost:5000')
        data = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(data['chain_length'], 2)
        self.assertEqual(data['unmined_length'], 0)


    def test4_consensus(self):
        """The blocks are added into a network when there is a consensus
        between different nodes."""
        r = requests.post('http://localhost:5000/register_peer', data={'peer': 'localhost:4000'})
        self.assertEqual(r.status_code, 201)
        r = requests.post('http://localhost:4000/register_peer', data={'peer': 'localhost:5000'})
        self.assertEqual(r.status_code, 201)

        r = requests.get('http://localhost:5000/consensus')
        self.assertEqual(r.status_code, 200)
        r = requests.get('http://localhost:4000/consensus')
        self.assertEqual(r.status_code, 200)


    def test5_evern_more_consensus(self):
        """The blocks are added into a network when there is a consensus
        between different nodes."""

        # Adding a new node.
        r = requests.post('http://localhost:5000/register_peer', data={'peer': 'localhost:3000'})
        r = requests.post('http://localhost:4000/register_peer', data={'peer': 'localhost:5000'})
        r = requests.post('http://localhost:4000/register_peer', data={'peer': 'localhost:3000'})
        r = requests.post('http://localhost:3000/register_peer', data={'peer': 'localhost:4000'})

        # Maintaining consensus.
        r = requests.get('http://localhost:5000/consensus')
        self.assertEqual(r.status_code, 200)
        r = requests.get('http://localhost:4000/consensus')
        self.assertEqual(r.status_code, 200)
        r = requests.get('http://localhost:3000/consensus')
        self.assertEqual(r.status_code, 200)

        # New transaction mined by node 3000.
        r = requests.post('http://localhost:3000/add_transaction', data={'transaction': 5})
        r = requests.get('http://localhost:3000/mine')

        # And another consensus.
        r = requests.get('http://localhost:5000/consensus')
        self.assertEqual(r.status_code, 200)
        r = requests.get('http://localhost:4000/consensus')
        self.assertEqual(r.status_code, 200)
        r = requests.get('http://localhost:3000/consensus')
        self.assertEqual(r.status_code, 200)


unittest.main(verbosity=2)
