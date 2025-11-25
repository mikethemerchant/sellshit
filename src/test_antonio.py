"""
Test script to directly process Antonio's message
Thread ID: 5065340080357696
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import MessengerAgent, Inventory, get_driver

# Initialize
inventory = Inventory("output.json")
driver = get_driver()
agent = MessengerAgent(driver, inventory)

# Navigate directly to Antonio's thread
antonio_thread_id = "5065340080357696"
print(f"🎯 Navigating directly to Antonio's thread: {antonio_thread_id}")

url = f"https://www.facebook.com/messages/t/{antonio_thread_id}"
driver.get(url)
import time
time.sleep(5)

print(f"📍 Current URL: {driver.current_url}")

# Get thread info
thread_id, buyer_name, item_title_from_header = agent.get_thread_info()
print(f"🧵 Thread: id={thread_id} buyer={buyer_name}")
if item_title_from_header:
    print(f"🏷️  Item from header: {item_title_from_header}")

# Check if this is a new buyer
if agent.state and thread_id:
    if thread_id not in agent.state.state:
        print(f"🆕 NEW BUYER DETECTED! This is Antonio!")
    else:
        print(f"⚠️ Thread already in buyer_state")

# Get last message
last_message = agent.get_last_message()
print(f"📩 Last message: {last_message}")

# Check if it's new
if agent.state and thread_id:
    is_new = agent.state.has_new_message(thread_id, last_message)
    print(f"🔍 Is new message: {is_new}")

# Match item
matched_item = None
if item_title_from_header:
    matched_item = inventory.get_item_by_title(item_title_from_header)
    if matched_item:
        print(f"✅ Matched item from header: {matched_item.get('Title')}")

if not matched_item:
    matched_item = inventory.get_item_by_title(last_message)
    if matched_item:
        print(f"✅ Matched item from message: {matched_item.get('Title')}")

if not matched_item:
    print("⚠️ No item matched")

# Generate response
response = agent.infer_intent_and_reply(last_message, matched_item)
print(f"\n💬 Generated response: {response}")

# Send the response
print("\n" + "="*80)
agent.send_message(response, send=True)
print("✅ Message sent!")

# Update state
if agent.state and thread_id:
    if buyer_name:
        agent.state.set_buyer_name(thread_id, buyer_name)
    agent.state.mark_seen_message(thread_id, last_message)
    if matched_item:
        item_id = matched_item.get('id') or matched_item.get('ID')
        if item_id:
            agent.state.set_item_id(thread_id, item_id)
    print("✅ State updated!")

print("\n✅ Done")
