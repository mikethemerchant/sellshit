import json
from buyer_state import BuyerStateStore

# Load the inventory to find Rich Dad Poor Dad
with open("output.json", "r", encoding="utf-8") as f:
    inventory = json.load(f)

# Find Rich Dad Poor Dad
for item in inventory:
    title = item.get("Title", "")
    if "rich dad" in title.lower() or "poor dad" in title.lower():
        print(f"Found item: {title}")
        print(f"  ID: {item.get('id') or item.get('ID')}")
        print(f"  Price: {item.get('price') or item.get('Price')}")
        print(f"  Bottom: {item.get('bottom') or item.get('Bottom')}")
        print()

# Check buyer state
state = BuyerStateStore()
print("Current buyer state threads:")
for thread_id, data in state.state.items():
    buyer = data.get("buyer_name", "Unknown")
    item_id = data.get("item_id", "None")
    print(f"  Thread {thread_id}: {buyer} (item {item_id})")
