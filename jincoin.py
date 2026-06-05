import hashlib
import json
import time


class Block:
    def __init__(self, index, transactions, previous_hash):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }

        block_string = json.dumps(block_data, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        target = "0" * difficulty

        print(f"⛏️ NOVA 채굴 시작... 난이도: {difficulty}")

        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()

        print("✅ NOVA 채굴 성공!")
        print("블록 해시:", self.hash)


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 4
        self.mining_reward = 50

    def create_genesis_block(self):
        return Block(0, ["NOVA Genesis Block"], "0")

    def get_latest_block(self):
        return self.chain[-1]

    def create_transaction(self, sender, receiver, amount):

        tx_data = f"{sender}{receiver}{amount}{time.time()}"

        tx_id = hashlib.sha256(tx_data.encode()).hexdigest()

        transaction = {
            "tx_id": tx_id,
            "from": sender,
            "to": receiver,
            "amount": amount
        }

        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self, miner_address):
        reward_transaction = {
            "from": "network",
            "to": miner_address,
            "amount": self.mining_reward
        }

        self.pending_transactions.append(reward_transaction)

        new_block = Block(
            len(self.chain),
            self.pending_transactions,
            self.get_latest_block().hash
        )

        new_block.mine_block(self.difficulty)

        self.chain.append(new_block)
        self.pending_transactions = []

    def get_balance(self, address):
        balance = 0

        for block in self.chain:
            for transaction in block.transactions:
                if isinstance(transaction, dict):
                    if transaction["from"] == address:
                        balance -= transaction["amount"]

                    if transaction["to"] == address:
                        balance += transaction["amount"]

        return balance

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def show_chain(self):
        for block in self.chain:
            print("\n==========================")
            print("블록 번호:", block.index)
            print("시간:", block.timestamp)
            print("거래:", block.transactions)
            print("이전 해시:", block.previous_hash)
            print("현재 해시:", block.hash)
            print("Nonce:", block.nonce)


jincoin = Blockchain()
jincoin.create_transaction("network","JINKYO SUH",1000000)
jincoin.create_transaction("JINKYO SUH", "ARIM KIM", 10)
jincoin.create_transaction("ARIM KIM", "Charlie", 5)

jincoin.mine_pending_transactions("NOVA_WALLET")

jincoin.show_chain()

print("\n블록체인 정상 여부:", jincoin.is_chain_valid())

print("\nJINKYO SUH 잔액:", jincoin.get_balance("JINKYO SUH"), "NOVA")
print("ARIM KIM 잔액:", jincoin.get_balance("ARIM KIM"), "NOVA")
print("Charlie 잔액:", jincoin.get_balance("Charlie"), "NOVA")
print("NOVA_WALLET 잔액:", jincoin.get_balance("NOVA_WALLET"), "NOVA")