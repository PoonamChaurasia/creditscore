import pandas as pd
import requests
import time

# --- Load wallet addresses from CSV ---
wallet_df = pd.read_csv("Wallet_id_Sheet1.csv")
wallets = wallet_df["wallet_id"].tolist()

# --- Constants ---
SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2"

# --- Function to fetch Compound V2 data ---
def fetch_wallet_data(wallet):
    query = {
        "query": f"""
        {{
          account(id: "{wallet.lower()}") {{
            tokens {{
              symbol
              lifetimeSupply
              lifetimeBorrow
              supplyBalanceUnderlying
              borrowBalanceUnderlying
            }}
          }}
        }}
        """
    }
    try:
        response = requests.post(SUBGRAPH_URL, json=query)
        return response.json()
    except Exception as e:
        print(f"Error fetching for wallet {wallet}: {e}")
        return None

# --- Feature extraction ---
def extract_features(wallet_json):
    tokens = wallet_json.get("data", {}).get("account", {}).get("tokens", [])
    total_supply = 0
    total_borrow = 0

    for token in tokens:
        try:
            total_supply += float(token.get("lifetimeSupply", 0))
            total_borrow += float(token.get("lifetimeBorrow", 0))
        except:
            continue

    borrow_to_supply_ratio = (
        total_borrow / total_supply if total_supply > 0 else 0
    )
    repayment_ratio = (
        1 - (wallet_json.get("borrowBalanceUnderlying", 0) / total_borrow)
        if total_borrow > 0 else 1
    )
    average_utilization = (
        total_borrow / (total_borrow + total_supply)
        if (total_borrow + total_supply) > 0 else 0
    )

    return {
        "total_supply": total_supply,
        "total_borrow": total_borrow,
        "borrow_to_supply_ratio": borrow_to_supply_ratio,
        "repayment_ratio": repayment_ratio,
        "average_utilization": average_utilization,
        "liquidations": 0  # Placeholder (Compound V2 doesn't return this via subgraph)
    }

# --- Scoring Function ---
def compute_risk_score(features):
    base_score = 1000
    penalty = 0

    if features["borrow_to_supply_ratio"] > 1:
        penalty += 200
    if features["repayment_ratio"] < 0.8:
        penalty += 150
    if features["average_utilization"] > 0.9:
        penalty += 100
    if features["liquidations"] > 0:
        penalty += features["liquidations"] * 100

    return max(0, min(1000, base_score - penalty))

# --- Processing All Wallets ---
results = []

print("Processing wallets...")
for wallet in wallets:
    data = fetch_wallet_data(wallet)
    if data is None:
        score = 0
    else:
        features = extract_features(data)
        score = compute_risk_score(features)

    print(f"Wallet: {wallet}, Score: {score}")
    results.append({"wallet_id": wallet, "score": int(score)})

    time.sleep(0.5)  # avoid rate-limiting

# --- Save final output ---
output_df = pd.DataFrame(results)
output_df.to_csv("wallet_scores.csv", index=False)
print("✅ Saved to wallet_scores.csv")
