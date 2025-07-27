import pandas as pd
import requests
import time

# Load wallet list
wallets_df = pd.read_csv("Wallet_id_Sheet1.csv")
wallets = wallets_df["wallet_id"].tolist()

# Compound V3 (Ethereum) subgraph URL
SUBGRAPH_URL = "https://api.thegraph.com/subgraphs/name/compound-finance/compound-v3-ethereum"

# Fetch function
def fetch_compound_v3_data(wallet):
    query = {
        "query": f"""
        {{
          account(id: "{wallet.lower()}") {{
            id
            accountMarkets {{
              market {{
                id
              }}
              totalCollateralValue
              totalBorrowValue
            }}
          }}
        }}
        """
    }
    try:
        response = requests.post(SUBGRAPH_URL, json=query)
        return response.json()
    except Exception as e:
        print(f"Error fetching wallet {wallet}: {e}")
        return None

# Extract & Store
wallet_data = []

for wallet in wallets:
    print(f"Fetching Compound V3 data for: {wallet}")
    result = fetch_compound_v3_data(wallet)

    # Check if data exists safely
    if result and "data" in result and result["data"].get("account") is not None:
        markets = result["data"]["account"]["accountMarkets"]
        for m in markets:
            wallet_data.append({
                "wallet_id": wallet,
                "market": m["market"]["id"],
                "total_collateral": float(m["totalCollateralValue"]),
                "total_borrow": float(m["totalBorrowValue"])
            })
    else:
        # Handle errors gracefully and print the response for debugging
        print(f"⚠️ No data or error for wallet {wallet}. Raw response:\n{result}")
        wallet_data.append({
            "wallet_id": wallet,
            "market": None,
            "total_collateral": 0.0,
            "total_borrow": 0.0
        })

    time.sleep(0.5)

# Save output
df = pd.DataFrame(wallet_data)
df.to_csv("wallet_transaction_history_v3.csv", index=False)
print("✅ Compound V3 history saved to wallet_transaction_history_v3.csv")
