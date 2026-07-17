from flask import Flask, jsonify, request, session, redirect
import random
import string
import sqlite3
from jincoin import jincoin

app = Flask(__name__)
app.secret_key = "nova_secret_key"

wallets = []


def init_db():
    conn = sqlite3.connect("nova.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            wallet TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_db()


def new_wallet_address():
    random_part = "".join(
        random.choices(string.ascii_uppercase + string.digits, k=16)
    )
    return f"NOVA{random_part}"


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].upper()
        password = request.form["password"]
        wallet_address = new_wallet_address()

        conn = sqlite3.connect("nova.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password, wallet) VALUES (?, ?, ?)",
                (username, password, wallet_address),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return """
            <html>
            <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:100px;">
                <h1 style="color:#ff6b6b;">❌ Username Already Exists</h1>
                <a href="/signup">Try Again</a>
                <br><br>
                <a href="/">← Back Explorer</a>
            </body>
            </html>
            """

        conn.close()

        return f"""
        <html>
        <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:100px;">
            <h1 style="color:#f39c12;">✅ Account Created</h1>
            <h2>{username}</h2>
            <p>Your NOVA Wallet:</p>
            <h2 style="color:#7dffb2;">{wallet_address}</h2>
            <br>
            <a href="/login">🔐 Login</a>
            <br><br>
            <a href="/">← Back Explorer</a>
        </body>
        </html>
        """

    return """
    <html>
    <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:100px;">
        <h1 style="color:#f39c12;">👤 NOVA Sign Up</h1>

        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Create Account</button>
        </form>

        <br>
        <a href="/">← Back Explorer</a>
    </body>
    </html>
    """


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].upper()
        password = request.form["password"]

        conn = sqlite3.connect("nova.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT wallet FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            wallet_address = result[0]
            session["username"] = username
            session["wallet"] = wallet_address

            return f"""
            <html>
            <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:100px;">
                <h1 style="color:#f39c12;">✅ Login Success</h1>
                <h2>{username}</h2>
                <p>Your NOVA Wallet:</p>
                <h2 style="color:#7dffb2;">{wallet_address}</h2>
                <br>
                <a href="/">← Back Explorer</a>
            </body>
            </html>
            """

        return """
        <html>
        <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:100px;">
            <h1 style="color:#ff6b6b;">❌ Login Failed</h1>
            <p>Wrong username or password</p>
            <a href="/login">Try Again</a>
            <br><br>
            <a href="/">← Back Explorer</a>
        </body>
        </html>
        """

    return """
    <html>
    <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:100px;">
        <h1 style="color:#f39c12;">🔐 NOVA Login</h1>

        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>

        <br>
        <a href="/">← Back Explorer</a>
    </body>
    </html>
    """
@app.route("/mywallet")
def mywallet():
    if "username" not in session:
        return """
        <h1>❌ Please Login First</h1>
        <a href="/login">Login</a>
        <br><br>
        <a href="/">Back Explorer</a>
        """

    username = session["username"]

    conn = sqlite3.connect("nova.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT wallet FROM users WHERE username = ?",
        (username,)
    )

    result = cursor.fetchone()
    conn.close()

    if not result:
        return """
        <h1>❌ Wallet Not Found</h1>
        <a href="/">Back Explorer</a>
        """

    wallet_address = result[0]
    balance = jincoin.get_balance(username)

    return f"""
    <html>
    <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:80px;">
        <h1 style="color:#f39c12;">👤 My NOVA Wallet</h1>

        <h2>{username}</h2>

        <p>Wallet Address:</p>
        <h2 style="color:#7dffb2;">{wallet_address}</h2>

        <p>Balance:</p>
        <h2 style="color:#7dffb2;">{balance} NOVA</h2>

        <br>
        <a href="/">← Back Explorer</a>
    </body>
    </html>
    """
@app.route("/transactions")
def transactions():

    if "username" not in session:
        return """
        <h1>❌ Please Login First</h1>
        <a href="/login">Login</a>
        """

    username = session["username"]

    html = f"""
    <html>
    <body style="
        background:#0f1117;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:50px;
    ">
    <h1>📜 My Transactions</h1>
    <h2>{username}</h2>
    """

    for block in reversed(jincoin.chain):

        for tx in block.transactions:

            if isinstance(tx, dict):

                sender = tx.get("from", "")
                receiver = tx.get("to", "")
                amount = tx.get("amount", 0)

                if sender == username:

                    html += f"""
                    <p style="color:#ff6b6b;">
                    - {amount} NOVA → {receiver}
                    </p>
                    """

                elif receiver == username:

                    html += f"""
                    <p style="color:#7dffb2;">
                    + {amount} NOVA ← {sender}
                    </p>
                    """

    html += """
    <br>
    <a href="/">← Back Explorer</a>
    </body>
    </html>
    """

    return html

@app.route("/logout")
def logout():
    session.clear()
    return """
    <html>
    <body style="background:#0f1117; color:white; font-family:Arial; text-align:center; padding-top:100px;">
        <h1 style="color:#f39c12;">👋 Logged Out</h1>
        <a href="/">← Back Explorer</a>
    </body>
    </html>
    """


@app.route("/create_wallet")
def create_wallet():
    wallet_address = new_wallet_address()
    wallets.append(wallet_address)

    return f"""
    <html>
    <head>
        <title>New NOVA Wallet</title>
        <style>
            body {{
                background:#0f1117;
                color:white;
                font-family:Arial, sans-serif;
                text-align:center;
                padding-top:120px;
            }}

            h1 {{
                color:#f39c12;
                font-size:48px;
            }}

            .wallet-box {{
                background:#1c1f26;
                padding:30px;
                border-radius:20px;
                display:inline-block;
                margin-top:30px;
            }}

            .wallet-address {{
                color:#7dffb2;
                font-size:32px;
                font-weight:bold;
                letter-spacing:1px;
            }}

            a {{
                color:#7ecbff;
                font-size:20px;
                text-decoration:none;
            }}
        </style>
    </head>

    <body>
        <h1>🔐 NEW NOVA WALLET</h1>

        <div class="wallet-box">
            <p>Your new wallet address:</p>

            <div id="wallet" class="wallet-address">
                {wallet_address}
            </div>

            <br>

            <button onclick="copyWallet()">📋 Copy Address</button>

            <script>
            function copyWallet() {{
                navigator.clipboard.writeText(
                    document.getElementById("wallet").innerText
                );
                alert("Wallet copied!");
            }}
            </script>
        </div>

        <br><br>
        <a href="/">← Back Explorer</a>
    </body>
    </html>
    """


@app.route("/mine")
def mine():

    if "username" in session:
        miner = session["username"]
    else:
        miner = "NOVA_WALLET"

    jincoin.mine_pending_transactions(miner)

    return """
    <html>
    <head>
        <meta http-equiv="refresh" content="2; url=/">
        <style>
            body {
                background:#0f1117;
                color:white;
                font-family:Arial;
                text-align:center;
                padding-top:120px;
            }

            h1 {
                font-size:48px;
                color:#f39c12;
            }

            p {
                font-size:24px;
                color:#7dffb2;
            }

            .loader {
                border:8px solid #222;
                border-top:8px solid #f39c12;
                border-radius:50%;
                width:80px;
                height:80px;
                animation:spin 1s linear infinite;
                margin:auto;
                margin-top:40px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>

    <body>
        <h1>⛏ Mining New Block...</h1>
        <p>NOVA Network Processing Transaction</p>
        <div class="loader"></div>
    </body>
    </html>
    """


@app.route("/send_form", methods=["POST"])
def send_form():
    sender = request.form["sender"].strip()
    receiver = request.form["receiver"].strip()
    amount_text = request.form["amount"].strip()

    if sender == "" or receiver == "" or amount_text == "":
        return """
        <h1>❌ Please fill all fields</h1>
        <a href="/">Back Explorer</a>
        """

    amount = int(amount_text)

    if amount <= 0:
        return """
        <h1>❌ Amount must be greater than 0</h1>
        <a href="/">Back Explorer</a>
        """

    if jincoin.get_balance(sender) < amount:
        return """
        <h1>❌ Not Enough Balance</h1>
        <a href="/">Back Explorer</a>
        """

    jincoin.create_transaction(sender, receiver, amount)

    return f"""
        <h1>✅ Transaction Added</h1>
        <p>{sender} → {receiver} : {amount} NOVA</p>
        <a href="/">Back Explorer</a>
        """


@app.route("/wallet_search", methods=["POST"])
def wallet_search():
    wallet_name = request.form["wallet_name"].upper()
    balance = jincoin.get_balance(wallet_name)

    history = []

    for block in jincoin.chain:
        for tx in block.transactions:
            if isinstance(tx, dict) and (
                tx["from"] == wallet_name or tx["to"] == wallet_name
            ):
                history.append(tx)

    total_received = 0
    total_sent = 0
    tx_count = 0
    transactions_html = ""

    for tx in history:
        tx_count += 1

        if tx["to"] == wallet_name:
            total_received += tx["amount"]

        if tx["from"] == wallet_name:
            total_sent += tx["amount"]

        transactions_html += f"""
        <p>{tx["from"]} → {tx["to"]} : {tx["amount"]} NOVA</p>
        """

    return f"""
    <html>
    <head>
        <title>NOVA Wallet Search</title>
        <style>
            body {{
                background:#0f1117;
                color:white;
                font-family:Arial;
                text-align:center;
                padding-top:100px;
            }}

            .box {{
                background:#1c1f26;
                display:inline-block;
                padding:35px;
                border-radius:20px;
            }}

            h1 {{
                color:#f39c12;
            }}

            h2 {{
                color:#7dffb2;
            }}

            a {{
                color:#7ecbff;
                font-size:20px;
            }}
        </style>
    </head>

    <body>
        <div class="box">
            <h1>🔍 NOVA Wallet Lookup</h1>
            <p>Wallet Address:</p>
            <h2>{wallet_name}</h2>
            <p>Balance:</p>
            <h2>{balance} NOVA</h2>
            <h3>📊 Wallet Analytics</h3>
            <p>📥 Total Received: {total_received} NOVA</p>
            <p>📤 Total Sent: {total_sent} NOVA</p>
            <p>📜 Transaction Count: {tx_count}</p>
            <p>💰 Net Balance: {balance} NOVA</p>
            <h3>📜 Recent Transactions</h3>

            {transactions_html}

            <br>
            <a href="/">← Back Explorer</a>
        </div>
    </body>
    </html>
    """


@app.route("/transaction_search", methods=["POST"])
def transaction_search():
    keyword = request.form["keyword"].upper()
    results = []

    for block in jincoin.chain:
        for tx in block.transactions:
            if isinstance(tx, dict):
                from_name = tx["from"].upper()
                to_name = tx["to"].upper()

                if keyword in from_name or keyword in to_name:
                    results.append((block.index, tx))

    results_html = ""

    if len(results) == 0:
        results_html = "<p>No transactions found</p>"
    else:
        for block_index, tx in results:
            results_html += f"""
            <p>
                Block {block_index} |
                {tx["from"]} → {tx["to"]} : {tx["amount"]} NOVA
            </p>
            """

    return f"""
    <html>
    <body style="
        background:#0f1117;
        color:white;
        font-family:Arial;
        text-align:center;
        padding-top:80px;
    ">
        <div style="
            background:#1c1f26;
            display:inline-block;
            padding:35px;
            border-radius:20px;
        ">
            <h1 style="color:#f39c12;">🔎 Transaction Search</h1>
            <h2 style="color:#7dffb2;">{keyword}</h2>

            {results_html}

            <br>
            <a href="/" style="color:#7ecbff;">← Back Explorer</a>
        </div>
    </body>
    </html>
    """


@app.route("/block_search", methods=["POST"])
def block_search():
    block_index_text = request.form["block_index"]

    if block_index_text == "":
        return """
        <h1>❌ Please enter a block number</h1>
        <a href="/">Back Explorer</a>
        """

    block_index = int(block_index_text)

    if block_index >= len(jincoin.chain):
        return "<h1>Block Not Found</h1>"

    block = jincoin.chain[block_index]

    return f"""
    <html>
    <body style="
        background:#0f1117;
        color:white;
        font-family:Arial;
        padding:40px;
    ">

    <h1>📦 Block {block.index}</h1>

    <p>Hash:</p>
    <p>{block.hash}</p>

    <p>Previous Hash:</p>
    <p>{block.previous_hash}</p>

    <p>Nonce:</p>
    <p>{block.nonce}</p>

    <p>Transactions:</p>
    <p>{len(block.transactions)}</p>

    <br>

    <a href="/">Back Explorer</a>

    </body>
    </html>
    """


@app.route("/api/chain")
def api_chain():
    chain_data = []

    for block in jincoin.chain:
        chain_data.append(
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "transactions": block.transactions,
                "previous_hash": block.previous_hash,
                "hash": block.hash,
                "nonce": block.nonce,
            }
        )

    return jsonify(chain_data)


@app.route("/")
def home():
    user_names = [
        "Michael",
        "Sophia",
        "Daniel",
        "Emma",
        "Lucas",
        "Olivia",
        "James",
        "Charlotte",
        "Ethan",
        "Mia",
        "Benjamin",
        "Amelia",
        "Noah",
        "Harper",
        "Henry",
        "Minho",
        "Hyoungjoo Ha",
        "Jisoo",
        "Yuna",
        "Jihoon",
        "Seoyeon",
        "JINKYO SUH",
        "ARIM KIM",
    ]

    receivers = [
        "JINKYO SUH",
        "ARIM KIM",
        "NOVA_WALLET",
        "Michael",
        "Sophia",
        "Jisoo",
        "Yuna",
    ]

    if random.randint(1, 3) == 1:
        sender = random.choice(user_names)
        receiver = random.choice(receivers)
        amount = random.randint(1, 20)

        if sender != receiver:
            jincoin.create_transaction(sender, receiver, amount)

    nova_price = round(random.uniform(0.05, 0.15), 4)
    nova_change = round(random.uniform(-5, 15), 2)
    total_mined = (len(jincoin.chain) - 1) * jincoin.mining_reward
    market_cap = round(nova_price * total_mined, 2)

    total_transactions = 0
    for block in jincoin.chain:
        total_transactions += len(block.transactions)

    active_nodes = random.randint(5, 25)
    network_power = active_nodes * jincoin.difficulty * 13

    conn = sqlite3.connect("nova.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, wallet FROM users")
    users_db = cursor.fetchall()
    conn.close()

    wallet_count = len(user_names) + len(users_db)

    holders = []
    for username, wallet in users_db:
        holders.append((username, jincoin.get_balance(username)))

    holders.append(
    ("NOVA_WALLET",
     jincoin.get_balance("NOVA_WALLET"))
)

    holders.sort(
    key=lambda x: x[1], reverse=True
)

    holders.sort(key=lambda x: x[1], reverse=True)

    login_info = ""
    if "username" in session:
        login_info = f"""
        <h3>👋 {session["username"]} 님 환영합니다</h3>
        <p>🔐 Wallet: {session.get("wallet", "")}</p>
         
        """

    html = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="15">
        <title>NOVA CHAIN</title>

        <style>
            body {{
                background: #0f1117;
                color: white;
                font-family: Arial, sans-serif;
                padding: 40px;
            }}

            h1 {{
                font-size: 48px;
                margin-bottom: 30px;
            }}

            .card {{
                background: #1c1f26;
                padding: 25px;
                border-radius: 20px;
                margin-bottom: 25px;
            }}

            .block {{
                background: #181b22;
                padding: 20px;
                border-radius: 16px;
                margin-bottom: 20px;
                border: 1px solid #333846;
                transition: 0.2s;
            }}

            .block:hover {{
                transform: scale(1.01);
            }}

            .hash {{
                color: #7ecbff;
                word-break: break-all;
            }}

            .prev-hash {{
                color: #f39c12;
                word-break: break-all;
            }}

            .nonce {{
                color: #7dffb2;
                font-weight: bold;
            }}

            .tx {{
                color: #7dffb2;
                word-break: break-all;
            }}

            .mine-btn {{
                padding: 15px 22px;
                font-size: 20px;
                background: #f39c12;
                color: white;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                margin-bottom: 20px;
            }}

            input {{
                padding: 10px;
                border: none;
                border-radius: 8px;
                margin-right: 8px;
            }}

            button {{
                padding: 10px 14px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                margin-right: 8px;
            }}
        </style>
    </head>

    <body>
        <h1>🟠 NOVA CHAIN</h1>

        {login_info}

        <a href="/signup"><button>👤 Sign Up</button></a>
        <a href="/login"><button>🔐 Login</button></a>
        <a href="/mywallet"><button>👤 My Wallet</button></a>
        <a href="/transactions"><button>📜 My Transactions</button></a>
        <a href="/logout"><button>🚪 Logout</button></a>

        <br><br>

        <div class="card">
            <h2>📈 NOVA Market</h2>
            <p>💵 Price: ${nova_price}</p>
            <p>📊 24h Change: {nova_change}%</p>
            <p>🏦 Market Cap: ${market_cap}</p>
            <p>⛏ Total Mined: {total_mined} NOVA</p>
            <p>🌍 Active Nodes: {active_nodes}</p>
            <p>⏳ Pending Count: {len(jincoin.pending_transactions)}</p>
        </div>

        <div class="card">
            <h2>📊 BLOCKCHAIN STATS</h2>
            <p>📦 Total Transactions: {total_transactions}</p>
            <p>🧱 Total Blocks: {len(jincoin.chain)}</p>
            <p>👛 Total Wallets: {wallet_count}</p>
            <p>⚡ Network Power: {network_power} H/s</p>
        </div>

        <div class="card">
            <h2>🔎 Transaction Search</h2>
            <form action="/transaction_search" method="POST">
                <input type="text" name="keyword" placeholder="Name or wallet">
                <button type="submit">Search Transaction</button>
            </form>
        </div>

        """
    
    html += """
        <div class="card">
            <h2>Wallet Balances</h2>
        """

    for username, wallet in users_db:
        html += f"<p>{username}: {jincoin.get_balance(username)} NOVA</p>"

    html += f"""
        <p>NOVA_WALLET: {jincoin.get_balance("NOVA_WALLET")} NOVA</p>
        </div>

        <div class="card">
            <h2>Created Wallets</h2>
    """

    for wallet in wallets:
        html += f"<p>{wallet}</p>"

    html += """
        </div>

        <div class="card">
            <h2>TOP HOLDERS</h2>
    """

    medals = ["1","2","3","4","5","6","7","8","9","10"]

    for i, holder in enumerate(holders[:10]):
        html += f"<p>{medals[i]} {holder[0]} : {holder[1]} NOVA</p>"

    html += """
        </div>

        <div class="card">
            <h2>LIVE TRANSACTIONS</h2>
    """

    for block in jincoin.chain:
        for tx in block.transactions:
            if isinstance(tx, dict):
                html += f"""
                <p class="tx">
                    {tx["from"]} → {tx["to"]} : {tx["amount"]} NOVA
                    <br>
                    <span style="color:#7ecbff;">
                        TX: {tx.get("tx_id", "GENESIS")}
                    </span>
                </p>
                """

    html += """
        </div>

        <div class="card">
            <h2>⏳ Pending Transactions</h2>
    """

    if len(jincoin.pending_transactions) == 0:
        html += "<p>No pending transactions</p>"
    else:
        for tx in jincoin.pending_transactions:
            html += f'<p class="tx">{tx["from"]} → {tx["to"]} : {tx["amount"]} NOVA</p>'

    html += """
        </div>

        <a href="/create_wallet">
            <button class="mine-btn">🔐 Create Wallet</button>
        </a>

        <a href="/mine">
            <button class="mine-btn">⛏ Mine New Block</button>
        </a>

        <div class="card">
            <h2>🔍 Wallet Search</h2>
            <form action="/wallet_search" method="POST">
                <input type="text" name="wallet_name" placeholder="Wallet name or address">
                <button type="submit">Search Wallet</button>
            </form>
        </div>

        <div class="card">
            <h2>📦 Block Search</h2>
            <form action="/block_search" method="POST">
                <input type="number" name="block_index" placeholder="Block Number">
                <button type="submit">Search Block</button>
            </form>
        </div>

        <form action="/send_form" method="POST">
            <input type="text" name="sender" placeholder="Sender">
            <input type="text" name="receiver" placeholder="Receiver">
            <input type="number" name="amount" placeholder="Amount">
            <button type="submit">Send Transaction</button>
        </form>

        <br><br>
    """

    for block in jincoin.chain:
        html += f"""
        <div class="block">
            <h2>Block {block.index}</h2>

            <p><b>Hash:</b></p>
            <p class="hash">{block.hash}</p>

            <p><b>Previous:</b></p>
            <p class="prev-hash">{block.previous_hash}</p>

            <p><b>Transactions:</b></p>
            <p class="tx">{block.transactions}</p>

            <p class="nonce">⛏ Nonce: {block.nonce}</p>
        </div>
        """

    html += """
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
