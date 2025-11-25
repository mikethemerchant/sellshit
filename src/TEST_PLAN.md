# Test Plan: Antonio's Unread Message

## Steps to Test

1. **Mark Antonio's message as unread** in Facebook Messenger
   - Open Antonio's conversation
   - Click the three dots (•••) or right-click
   - Select "Mark as unread"

2. **Run the agent**
   - The command will be: `python agent.py --once`
   - The agent should:
     - See "Marketplace 1 new message" in the sidebar
     - Click it
     - Open a thread (might be Antonio's or another marketplace thread)
     - Detect if it's a NEW buyer
     - Process the message and respond

## What to Look For

### Success Indicators:
- ✅ "🆕 NEW BUYER DETECTED!" message appears
- ✅ Agent extracts Antonio's name from the thread
- ✅ Agent matches "Rich Dad Poor Dad" item
- ✅ Agent generates and sends a response
- ✅ buyer_state.json gets updated with Antonio's thread ID

### Possible Issues:
- ⚠️ Agent opens a different marketplace thread (not Antonio's)
  - This happens if Facebook shows a different thread first
  - Solution: We may need to iterate through multiple marketplace threads
  
- ⚠️ Agent doesn't find the item match
  - Check if "Rich Dad Poor Dad" appears in the message or header
  - May need to adjust item matching logic

## Ready to Test

Once you've marked Antonio's message as unread, let me know and I'll run the agent!
