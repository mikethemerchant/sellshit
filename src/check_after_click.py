"""
After clicking Marketplace, look for ANY rows or elements that might be threads
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Connect to existing Chrome
chrome_options = Options()
chrome_options.debugger_address = "127.0.0.1:9222"
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

print("Connected to Chrome")
print(f"Current URL: {driver.current_url}")

# Check if we're in a thread or in a list view
if '/messages/t/' in driver.current_url:
    print("⚠️ We're in a specific thread, not a list view")
    print("This means clicking 'Marketplace' opened a specific thread directly")
    
    # Extract thread ID
    parts = driver.current_url.split('/messages/t/')
    if len(parts) > 1:
        thread_id = parts[1].split('/')[0].split('?')[0].split('#')[0]
        print(f"Thread ID: {thread_id}")
        
        # Check if this is a known thread
        known_threads = {
            "1476401086986855": "Alex",
            "3509688825837712": "WiFi",
            "1058253483035875": "Pisit",
            "1745768319324111": "Chris",
            "1187271722897711": "Patch",
        }
        
        buyer_name = known_threads.get(thread_id, "UNKNOWN - THIS MIGHT BE ANTONIO!")
        print(f"Buyer: {buyer_name}")
        
        # Get the thread info from the page
        try:
            # Look for buyer name in header
            header_spans = driver.find_elements(By.CSS_SELECTOR, "div[role='banner'] span[dir='auto'], header span[dir='auto']")
            for span in header_spans[:5]:
                text = (span.text or '').strip()
                if text and len(text) > 1:
                    print(f"Header text: {text}")
        except:
            pass
        
        # Get last message
        try:
            message_rows = driver.find_elements(By.CSS_SELECTOR, 'div[role="row"]')
            print(f"\nFound {len(message_rows)} message rows")
            
            # Get last few messages
            for row in message_rows[-5:]:
                try:
                    text_els = row.find_elements(By.CSS_SELECTOR, 'div[dir="auto"]')
                    if text_els:
                        text = text_els[0].text.strip()
                        if text and len(text) > 3:
                            print(f"  Message: {text[:100]}")
                except:
                    pass
        except:
            pass

else:
    print("✅ We're in a list/inbox view")
    
    # Look for conversation rows
    try:
        rows = driver.find_elements(By.XPATH, "//div[@role='row']")
        print(f"Found {len(rows)} rows")
        
        for i, row in enumerate(rows[:10]):
            text = (row.text or '').strip().replace('\n', ' ')[:150]
            print(f"  [{i}] {text}")
    except:
        pass

print("\n✅ Done")
