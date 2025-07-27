import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from datetime import datetime

def process_data(file_path):
    with open(file_path) as f:
        data = json.load(f)

    wallet_stats = defaultdict(list)

    for tx in data:
        wallet = tx["userWallet"]
        action = tx["action"]
        ts = datetime.utcfromtimestamp(tx["timestamp"])
        price = float(tx["actionData"]["assetPriceUSD"])
        try:
            amount = float(tx["actionData"]["amount"]) / 1e6  # default 6 decimals
        except:
            amount = 0
        amount_usd = amount * price
        wallet_stats[wallet].append((action, ts, amount_usd))

    scores = []

    for wallet, txs in wallet_stats.items():
        df = pd.DataFrame(txs, columns=["action", "timestamp", "amount_usd"])

        total_tx = len(df)
        duration_days = (df.timestamp.max() - df.timestamp.min()).days + 1

        total_deposit = df[df.action == "deposit"]["amount_usd"].sum()
        total_borrow = df[df.action == "borrow"]["amount_usd"].sum()
        total_repay = df[df.action == "repay"]["amount_usd"].sum()
        total_redeem = df[df.action == "redeemunderlying"]["amount_usd"].sum()
        num_liquidations = (df.action == "liquidationcall").sum()

        repay_ratio = total_repay / total_borrow if total_borrow else 1
        redeem_ratio = total_redeem / total_deposit if total_deposit else 1
        tx_frequency = total_tx / duration_days
        net_gain = total_deposit - total_borrow

        score = 1000
        score -= (num_liquidations * 100)
        score -= (1 - repay_ratio) * 200
        score -= (1 - redeem_ratio) * 100
        score += tx_frequency * 10
        score += net_gain / 1000
        score = max(0, min(1000, round(score)))

        scores.append({
            "wallet": wallet,
            "score": score
        })

    return pd.DataFrame(scores)


df = process_data("user-wallet-transactions.json")
df.to_csv("wallet_scores.csv", index=False)


bins = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
labels = [f"{i}-{i+100}" for i in bins[:-1]]
df["score_range"] = pd.cut(df["score"], bins=bins, labels=labels, include_lowest=True)

plt.figure(figsize=(10,6))
sns.countplot(data=df, x="score_range", palette="magma", order=labels)
plt.title("Wallet Credit Score Distribution")
plt.xlabel("Score Range")
plt.ylabel("Number of Wallets")
plt.xticks(rotation=45)
plt.grid(axis="y")
plt.tight_layout()
plt.savefig("score_distribution.png")  # ✅ Save the plot to file
plt.show()

