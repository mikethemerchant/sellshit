import json
import time
import os
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

OUTPUT_JSON = "output.json"

###########################################################################
# SETUP: Connect to already-open Chrome in remote debugging mode
###########################################################################
def get_driver():
    """Connect to existing Chrome instance via remote debugging."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    print("🔗 Connecting to existing Chrome instance at 127.0.0.1:9222...")
    chrome_options.debugger_address = "127.0.0.1:9222"

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Successfully connected to Chrome")
        return driver
    except Exception as e:
        print(f"❌ Failed to connect to Chrome: {e}")
        print("💡 Make sure Chrome is running with: --remote-debugging-port=9222")
        raise


###########################################################################
# JSON Storage Helpers
###########################################################################
class Inventory:
    def __init__(self, output_path):
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(script_dir, output_path)
        self.items = self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Warning: {self.path} not found. Starting with empty inventory.")
            return []
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parsing {self.path}: {e}")
            return []

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.items, f, indent=4)

    def get_item_by_title(self, message_text):
        """Find item if any words from its Title appear in the message."""
        for item in self.items:
            item_title = item.get("Title", "")  # Note: Capital T to match output.json
            if not item_title:
                continue
            # Check if any significant words from title appear in message
            title_words = [w.lower() for w in item_title.split() if len(w) > 3]
            message_lower = message_text.lower()
            if any(word in message_lower for word in title_words):
                return item
        return None


###########################################################################
# Messenger Agent (Selenium)
###########################################################################
class MessengerAgent:
    def __init__(self, driver, inventory):
        self.driver = driver
        self.inventory = inventory

    def open_messenger(self):
        print("🔗 Opening Facebook Marketplace Inbox...")
        
        # Check current URL first
        try:
            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}")
            
            # Only navigate if not already on inbox
            if "marketplace/inbox" not in current_url.lower():
                print("➡️ Navigating to inbox...")
                self.driver.get("https://www.facebook.com/marketplace/inbox")
                time.sleep(8)  # Wait longer for dynamic content
            else:
                print("✅ Already on inbox page")
                time.sleep(3)
            
            # Wait for page to fully load
            print("⏳ Waiting for inbox to fully load...")
            time.sleep(3)
            # Ensure we're at the top-level DOM to start
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            
        except Exception as e:
            print(f"❌ Error accessing browser: {e}")
            raise

    def open_messages(self):
        print("🔗 Opening Facebook Messages (fallback)...")
        try:
            current_url = self.driver.current_url
            if "/messages" not in current_url:
                self.driver.get("https://www.facebook.com/messages")
                time.sleep(8)
            else:
                time.sleep(3)
            try:
                self.driver.switch_to.default_content()
            except Exception:
                pass
            print("⏳ Waiting for messages page to load...")
            time.sleep(3)
        except Exception as e:
            print(f"❌ Error opening messages: {e}")
            raise

    def get_recent_conversations(self, mode: str = "marketplace"):
        """
        Returns a list of visible conversation elements.
        """
        print(f"🔍 Scanning page for conversation elements (mode={mode})...")
        # Small extra wait to allow dynamic content to populate
        time.sleep(2)

        # Always start from default content
        try:
            self.driver.switch_to.default_content()
        except Exception:
            pass
        
        # Try XPath to find any links or divs that might be conversations
        if mode == "messages":
            xpath_selectors = [
                "//div[@aria-label='Chats']//div[@role='grid']//div[@role='row']",
                "//div[@aria-label='Chats']//div[@role='listitem' or @role='row']",
                "//div[@aria-label='Chats']//a[@role='link']",
                "//a[contains(@href, '/messages/t/')]",
            ]
        else:
            xpath_selectors = [
                "//a[contains(@href, '/t/')]",  # Messenger thread links
                "//div[@role='row']",  # Any row elements
                "//div[contains(@aria-label, 'onversation')]",  # Conversation labels
            ]
        
        for xpath in xpath_selectors:
            try:
                print(f"🔍 Trying XPath: {xpath}")
                elements = self.driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"✅ Found {len(elements)} elements")
                    # For messages mode, prefer unread items and preserve order
                    if mode == "messages":
                        ordered = elements
                        enriched = []
                        for idx, el in enumerate(ordered):
                            try:
                                # Determine click target
                                click_target = el
                                try:
                                    link = el.find_element(By.XPATH, ".//a[@role='link']")
                                    click_target = link
                                except Exception:
                                    pass
                                # Heuristic: unread if aria-label mentions unread/new
                                aria_labels = [
                                    (el.get_attribute("aria-label") or ""),
                                    (click_target.get_attribute("aria-label") or ""),
                                ]
                                all_aria = " ".join(aria_labels).lower()
                                unread = any(w in all_aria for w in ["unread", "new message", "new messages", "new"])
                                text_preview = (el.text or "").strip().replace("\n", " ")
                                enriched.append({
                                    "element": el,
                                    "click": click_target,
                                    "unread": unread,
                                    "text": text_preview,
                                    "aria": all_aria[:120],
                                    "idx": idx,
                                })
                            except Exception:
                                continue
                        # Debug print the first few with flags
                        for info in enriched[:5]:
                            print(f"  [{info['idx']}] unread={info['unread']} text='{(info['text'] or '')[:80]}' aria~='{info['aria']}'")
                        # Pick unread first; if none, keep original order
                        unread_items = [x for x in enriched if x["unread"]]
                        chosen = unread_items if unread_items else enriched
                        if chosen:
                            # Return the original elements in chosen order
                            return [x["element"] for x in chosen]
                    else:
                        # Marketplace mode: return elements without aggressive filtering
                        valid = [el for el in elements if el.is_displayed()]
                        if valid:
                            for i, el in enumerate(valid[:3]):
                                print(f"  [{i}] {el.text[:60].replace(chr(10), ' ')}")
                            return valid
            except Exception as e:
                print(f"⚠️ XPath failed: {str(e)[:100]}")
        
        print("⚠️ Could not find conversations")

        # DEBUG: Broader scan to understand DOM shape
        try:
            links = self.driver.find_elements(By.XPATH, "//a[@role='link']")
            print(f"🧭 Debug: Found {len(links)} link elements with role=link")
            for i, el in enumerate(links[:8]):
                href = el.get_attribute("href")
                txt = (el.text or "").strip().replace("\n", " ")
                print(f"   · Link[{i}] href={href} text='{txt[:80]}'")
        except Exception as e:
            print(f"🧭 Debug: Error listing role=link anchors: {e}")

        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"🧭 Debug: Found {len(iframes)} iframes")
            for i, fr in enumerate(iframes[:5]):
                src = fr.get_attribute("src")
                name = fr.get_attribute("name")
                title = fr.get_attribute("title")
                print(f"   · Iframe[{i}] name={name} title={title} src={src}")
        except Exception as e:
            print(f"🧭 Debug: Error enumerating iframes: {e}")
        
        # Attempt to search inside iframes for conversations (recursive up to depth 2)
        def scan_iframes(depth=0, max_depth=2):
            try:
                if depth > max_depth:
                    return None
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                print(f"🪟 Depth {depth}: scanning {len(frames)} iframes...")
                for idx, fr in enumerate(frames):
                    try:
                        print(f"   ↳ Switching into iframe at depth {depth} index {idx}...")
                        self.driver.switch_to.frame(fr)
                        time.sleep(1)
                        # Try selectors in this frame
                        for xpath in xpath_selectors:
                            print(f"      🔎 In depth {depth} iframe[{idx}] try: {xpath}")
                            elements = self.driver.find_elements(By.XPATH, xpath)
                            if elements:
                                valid = [el for el in elements if el.text.strip() and len(el.text.strip()) > 10]
                                if valid:
                                    print(f"      ✅ Found {len(valid)} candidate conversations in depth {depth} iframe[{idx}]")
                                    for i, el in enumerate(valid[:3]):
                                        print(f"        · [{i}] {el.text[:60].replace(chr(10), ' ')}")
                                    return valid
                        # Recurse into nested iframes
                        found = scan_iframes(depth + 1, max_depth)
                        if found:
                            return found
                    except Exception as e:
                        print(f"      ⚠️ Error scanning iframe at depth {depth} index {idx}: {str(e)[:120]}")
                    finally:
                        # Go back up one level after scanning this frame
                        try:
                            self.driver.switch_to.parent_frame()
                        except Exception:
                            try:
                                self.driver.switch_to.default_content()
                            except Exception:
                                pass
            except Exception as e:
                print(f"🧭 Debug: Error during iframe recursive scan at depth {depth}: {e}")
            return None

        found_in_iframes = scan_iframes(depth=0, max_depth=3)
        if found_in_iframes:
            return found_in_iframes

        # Final debug artifacts: save screenshot and page source for inspection
        try:
            out_png = os.path.join(os.getcwd(), "inbox_debug.png")
            out_html = os.path.join(os.getcwd(), "inbox_debug.html")
            if self.driver.save_screenshot(out_png):
                print(f"🖼️ Saved screenshot: {out_png}")
            with open(out_html, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"📝 Saved page source: {out_html}")
        except Exception as e:
            print(f"⚠️ Failed to save debug artifacts: {e}")
        return []

    def open_conversation(self, convo_element):
        """
        Click a conversation item to open the message thread.
        """
        try:
            # Scroll into view first
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", convo_element)
            time.sleep(0.5)
            
            # Try regular click first
            try:
                # If the convo_element isn't directly clickable, click nested link
                try:
                    link = convo_element.find_element(By.XPATH, ".//a[@role='link']")
                    link.click()
                except Exception:
                    convo_element.click()
                print("✅ Clicked conversation with element.click()")
            except:
                # Fallback to JS click
                try:
                    link = convo_element.find_element(By.XPATH, ".//a[@role='link']")
                    self.driver.execute_script("arguments[0].click();", link)
                except Exception:
                    self.driver.execute_script("arguments[0].click();", convo_element)
                print("✅ Clicked conversation with JS click")
            
            # Wait for conversation thread to load
            time.sleep(4)
            
            # Verify we're in a conversation thread
            current_url = self.driver.current_url
            print(f"📍 Conversation URL: {current_url}")
            
        except Exception as e:
            print("⚠️ Failed to click a conversation:", e)

    def get_last_message(self):
        """
        Returns the last message text in the open conversation.
        """
        try:
            # Wait longer for conversation to load
            print("⏳ Waiting for conversation to load...")
            time.sleep(3)
            
            # Try multiple selectors for messages - more specific to avoid timestamps
            message_selectors = [
                'div[role="row"] div[dir="auto"]',  # Message rows
                'div[data-scope="messages_table"] span',
                'div[aria-label*="message"] span',
                'span[dir="auto"]',  # Fallback to all spans
            ]
            
            for selector in message_selectors:
                messages = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if messages:
                    print(f"🔍 Found {len(messages)} message elements with selector: {selector}")
                    
                    # Debug: print first few messages found
                    for i, msg in enumerate(list(reversed(messages))[:10]):
                        text = msg.text.strip()
                        print(f"  [{i}] Text: '{text}' (len={len(text)})")
                    
                    # Get last non-empty message that's longer than 3 chars
                    for msg in reversed(messages):
                        text = msg.text.strip()
                        # Skip very short text (timestamps) and common UI text
                        if text and len(text) > 3 and text.lower() not in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']:
                            print(f"✉️ Selected message: {text[:100]}")
                            return text
            
            print("⚠️ No message text found with any selector")
            return None
        except Exception as e:
            print(f"⚠️ Error getting last message: {e}")
            return None

    def send_message(self, text):
        """
        Type into the Messenger input box but DO NOT send yet (debug mode).
        """
        try:
            # Try multiple selectors for the message input
            input_selectors = [
                "div[aria-label='Message'][contenteditable='true']",
                "div[contenteditable='true'][role='textbox']",
                "div[contenteditable='true'][aria-label*='message' i]",
                "div[contenteditable='true']",
            ]
            
            input_box = None
            for selector in input_selectors:
                try:
                    input_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if input_box:
                        print(f"✅ Found input box with: {selector}")
                        break
                except:
                    continue
            
            if not input_box:
                print("⚠️ Could not find message input box")
                return
            
            input_box.click()
            input_box.send_keys(text)
            print(f"📝 (DEBUG) Would send: {text}")

        except Exception as e:
            print("⚠️ Failed to type message:", e)

    def process_conversations(self):
        print("🔎 Checking conversations...")

        conversations = self.get_recent_conversations()
        if not conversations:
            print("No conversations found.")
            return

        # For debug: only open the first 3 conversations
        for convo in conversations[:3]:
            print("📨 Opening a conversation...")
            self.open_conversation(convo)

            last_message = self.get_last_message()
            print(f"📩 Last message: {last_message}")

            if not last_message:
                continue

            # Match item (debug: title match)
            matched_item = self.inventory.get_item_by_title(last_message)
            if matched_item:
                print(f"✅ Matched item: {matched_item.get('Title', 'Unknown')}")

            # DEBUG: do not send yet
            response = f"Thanks for reaching out! (DEBUG MODE) You said: '{last_message}'"
            self.send_message(response)

            time.sleep(2)


###########################################################################
# MAIN LOOP
###########################################################################
def main():
    print("🚀 Starting Marketplace Agent...")
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single pass and exit")
    args = parser.parse_args()

    inventory = Inventory(OUTPUT_JSON)
    driver = get_driver()
    agent = MessengerAgent(driver, inventory)

    agent.open_messenger()

    def single_pass():
        agent.process_conversations()
        # If marketplace scan found none, try messages fallback
        print("🔁 Fallback: trying Messages page scan...")
        agent.open_messages()
        convos = agent.get_recent_conversations(mode="messages")
        if not convos:
            print("⚠️ Still no conversations on Messages page.")
            return
        # Open first found conversation on messages page
        agent.open_conversation(convos[0])
        last_msg = agent.get_last_message()
        print(f"📩 Last message on Messages page: {last_msg}")

    if args.once:
        try:
            single_pass()
        except Exception as e:
            print("❌ Error in single pass:", e)
        return

    # MAIN LOOP (safe debug interval 60 sec)
    while True:
        try:
            single_pass()
        except Exception as e:
            print("❌ Error in main loop:", e)

        print("⏳ Sleeping 60s...\n")
        time.sleep(60)


if __name__ == "__main__":
    main()
