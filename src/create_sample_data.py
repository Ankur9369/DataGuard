
from pathlib import Path

import numpy as np
import pandas as pd

# Store sample data inside the project
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "sample"
DATA_DIR.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)
n = 120

# Create fictional source data
source = pd.DataFrame({
    "order_id": [f"ORD{i:04d}" for i in range(1, n + 1)],
    "customer_id": [
        f"CUST{i:03d}" for i in rng.integers(1, 41, n)
    ],
    "quantity": rng.integers(1, 6, n),
    "unit_price": rng.choice([499, 799, 999, 1499, 2499], n),
    "country": rng.choice(["India", "USA", "UK", "Canada"], n),
})

source.to_csv(DATA_DIR / "source_orders.csv", index=False)

# Create a separate target dataset with intentional defects
target = source.copy()

target.loc[3, "customer_id"] = None
target.loc[7, "order_id"] = target.loc[6, "order_id"]
target.loc[10, "quantity"] = -3
target.loc[15, "unit_price"] = -100
target.loc[20, "unit_price"] = 50000
target.loc[25, "unit_price"] = 1234

# Remove one row and add a different row
target = target.drop(index=30).reset_index(drop=True)

extra = source.iloc[[40]].copy()
extra["order_id"] = "ORD_EXTRA"
target = pd.concat([target, extra], ignore_index=True)

target.to_csv(DATA_DIR / "target_orders.csv", index=False)

print("Synthetic datasets created successfully.")
print(f"Source records: {len(source)}")
print(f"Target records: {len(target)}")
print(f"Location: {DATA_DIR}")
