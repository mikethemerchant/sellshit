import json
import time
import os
import argparse
from datetime import datetime
from urllib.parse import urlparse
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

OUTPUT_JSON = "output.json"

try:
    from buyer_state import BuyerStateStore
except Exception:
    BuyerStateStore = None

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
        self.state = BuyerStateStore() if BuyerStateStore else None

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
                "//a[@role='link' and contains(@href, '/messages/t/')]",  # Direct thread links first
                "//div[@aria-label='Chats']//div[@role='row']",  # Chats pane rows
                "//div[@role='grid']//div[@role='row']",  # Grid rows (broad)
                "//div[@role='listitem']",  # List items
            ]
            # Try to force-load more rows by scrolling any visible grid/list container
            try:
                for container_sel in ["//div[@aria-label='Chats']", "//div[@role='grid']", "//div[@role='list']"]:
                    try:
                        container = self.driver.find_element(By.XPATH, container_sel)
                        self.driver.execute_script("arguments[0].scrollTop = 0;", container)
                        time.sleep(0.3)
                        for _ in range(4):
                            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;", container)
                            time.sleep(0.3)
                        break
                    except Exception:
                        continue
            except Exception:
                pass
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
                                # Determine click target; prefer nested link with /messages/t/
                                click_target = el
                                try:
                                    link = el.find_element(By.XPATH, ".//a[contains(@href, '/messages/t/')]")
                                    click_target = link
                                except Exception:
                                    try:
                                        link = el.find_element(By.XPATH, ".//a[@role='link']")
                                        click_target = link
                                    except Exception:
                                        pass
                                # Skip if el is a direct <a> but doesn't contain /messages/t/ (nav link)
                                if el.tag_name == 'a':
                                    href = el.get_attribute('href') or ''
                                    if '/messages/t/' not in href:
                                        continue
                                # Also skip if no href found at all
                                target_href = click_target.get_attribute('href') if hasattr(click_target, 'get_attribute') else ''
                                if not target_href or '/messages/t/' not in target_href:
                                    # If it's a row element, might still be valid if it has text
                                    if el.tag_name not in ['div']:
                                        continue
                                # Heuristic: unread if aria-label mentions unread/new
                                aria_labels = [
                                    (el.get_attribute("aria-label") or ""),
                                    (click_target.get_attribute("aria-label") or ""),
                                ]
                                all_aria = " ".join(aria_labels).lower()
                                unread = any(w in all_aria for w in ["unread", "new message", "new messages", "new"]) 
                                # Additional heuristics for unread: row text contains 'new message(s)'
                                text_preview = (el.text or "").strip().replace("\n", " ")
                                if ("new message" in text_preview.lower()) or ("new messages" in text_preview.lower()):
                                    unread = True
                                # Detect marketplace aggregate row like 'Marketplace 2 new messages'
                                is_marketplace_group = False
                                tp_low = text_preview.lower()
                                if tp_low.startswith("marketplace") and ("new message" in tp_low or "new messages" in tp_low):
                                    is_marketplace_group = True
                                
                                # Visual unread indicators: blue dot (background-color) and bold font-weight
                                has_blue_dot = False
                                has_bold_text = False
                                try:
                                    # Check for blue dot indicator (common in unread rows)
                                    # Look for small circular elements with blue background
                                    dots = el.find_elements(By.XPATH, ".//div | .//span")
                                    for dot in dots[:20]:  # Limit search
                                        try:
                                            bg = self.driver.execute_script(
                                                "return window.getComputedStyle(arguments[0]).backgroundColor;", dot
                                            )
                                            # Blue dot typically rgb(0, 132, 255) or similar
                                            if bg and 'rgb' in bg.lower():
                                                # Extract RGB values
                                                import re
                                                match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)', bg)
                                                if match:
                                                    r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
                                                    # Blue-ish: low red, moderate-high blue
                                                    if r < 50 and b > 200:
                                                        has_blue_dot = True
                                                        break
                                        except Exception:
                                            continue
                                except Exception:
                                    pass
                                
                                # Bold font-weight detection on title spans
                                try:
                                    title_spans = el.find_elements(By.CSS_SELECTOR, "span[dir='auto']")
                                    for title_span in title_spans[:3]:
                                        fw = self.driver.execute_script(
                                            "return window.getComputedStyle(arguments[0]).fontWeight;",
                                            title_span,
                                        )
                                        try:
                                            fw_num = int("" + str(fw))
                                        except Exception:
                                            fw_num = 400
                                        if fw_num >= 600:
                                            has_bold_text = True
                                            break
                                except Exception:
                                    pass
                                
                                # Mark as unread if blue dot or bold text detected
                                if has_blue_dot or has_bold_text:
                                    unread = True
                                enriched.append({
                                    "element": el,
                                    "click": click_target,
                                    "unread": unread,
                                    "is_marketplace_group": is_marketplace_group,
                                    "has_blue_dot": has_blue_dot,
                                    "has_bold_text": has_bold_text,
                                    "text": text_preview,
                                    "aria": all_aria[:120],
                                    "idx": idx,
                                })
                            except Exception:
                                continue
                        # Debug print the first few with flags
                        for info in enriched[:8]:
                            print(f"  [{info['idx']}] unread={info['unread']} agg={info['is_marketplace_group']} dot={info['has_blue_dot']} bold={info['has_bold_text']} text='{(info['text'] or '')[:80]}'")
                        # Pick unread first; if none, keep original order
                        unread_items = [x for x in enriched if x["unread"]]
                        # Prefer non-aggregate unread threads over aggregate
                        unread_non_agg = [x for x in unread_items if not x["is_marketplace_group"]]
                        if unread_non_agg:
                            chosen = unread_non_agg
                        elif unread_items:
                            chosen = unread_items
                        else:
                            # As a last resort, pick non-aggregate rows
                            non_agg = [x for x in enriched if not x["is_marketplace_group"]]
                            chosen = non_agg if non_agg else enriched
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
            
            # If this is a Marketplace aggregate thread, try to drill down
            try:
                tid, buyer = self.get_thread_info()
                if buyer and 'marketplace' in buyer.lower():
                    print("🔎 In Marketplace aggregate; attempting to open first unread buyer thread…")
                    self._open_first_unread_within_main()
            except Exception:
                pass
            
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

    def send_message(self, text, send=True):
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
            if send:
                input_box.send_keys(Keys.ENTER)
                print(f"📤 Sent: {text}")
            else:
                print(f"📝 (DEBUG) Would send: {text}")

        except Exception as e:
            print("⚠️ Failed to type message:", e)

    def get_thread_info(self):
        """Extract thread id from URL, buyer name, and item title from header/banner."""
        tid = None
        name = None
        item_title = None
        try:
            url = self.driver.current_url
            p = urlparse(url)
            # Expect /messages/e2ee/t/<id> or /messages/t/<id>
            parts = [x for x in p.path.split('/') if x]
            if 'messages' in parts and 't' in parts:
                idx = parts.index('t')
                if idx + 1 < len(parts):
                    tid = parts[idx + 1]
        except Exception:
            pass
        
        # Buyer name and item title in header/banner region
        try:
            # Look for buyer name and item in header - often formatted as "Name · Item Title"
            header_selectors = [
                "div[aria-label='Conversation Information'] h1 span[dir='auto']",
                "header h2 span[dir='auto']",
                "div[role='banner'] span[dir='auto']",
                "h2[class] span[dir='auto']",
            ]
            header_text = None
            for sel in header_selectors:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    t = (el.text or '').strip()
                    if t and len(t) > 1:
                        header_text = t
                        break
                if header_text:
                    break
            
            # Parse "Name · Item Title" format
            if header_text and ' · ' in header_text:
                parts = header_text.split(' · ', 1)
                name = parts[0].strip()
                item_title = parts[1].strip() if len(parts) > 1 else None
            elif header_text:
                name = header_text
        except Exception:
            pass
        
        # If item title not found yet, look for Marketplace listing banner/link
        if not item_title:
            try:
                # Common patterns for item title in conversation header
                item_selectors = [
                    "a[href*='/marketplace/item/'] span[dir='auto']",  # Marketplace item link
                    "div[aria-label*='Marketplace'] span[dir='auto']",
                    "a[role='link'][href*='/marketplace/'] span",
                ]
                for sel in item_selectors:
                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in els:
                        txt = (el.text or '').strip()
                        # Item titles are typically longer than just a name
                        if txt and len(txt) > 5 and txt != name and txt.lower() != 'marketplace':
                            item_title = txt
                            break
                    if item_title:
                        break
                
                # Fallback: scan all visible text in header/banner region for longest non-name string
                if not item_title:
                    try:
                        banner = self.driver.find_element(By.XPATH, "//div[@role='banner'] | //header")
                        all_spans = banner.find_elements(By.CSS_SELECTOR, "span[dir='auto']")
                        candidates = []
                        for sp in all_spans:
                            txt = (sp.text or '').strip()
                            if txt and len(txt) > 10 and txt != name and txt.lower() != 'marketplace':
                                candidates.append(txt)
                        # Pick the longest as likely item title
                        if candidates:
                            item_title = max(candidates, key=len)
                    except Exception:
                        pass
            except Exception:
                pass
        
        return tid, name, item_title

    def update_item_status(self, item, status: str):
        try:
            if not item:
                return
            # Support lowercase and Title-case keys
            if 'status' in item:
                item['status'] = status
            else:
                item['Status'] = status
            self.inventory.save()
            print(f"🗂️ Updated item status to {status}")
        except Exception as e:
            print(f"⚠️ Failed to update item status: {e}")

    def infer_intent_and_reply(self, last_message: str, matched_item: dict):
        """Simple rule-based intent + response. Placeholder for LLM integration."""
        if not last_message:
            return None
        text = last_message.lower()

        # Extract price offer if any
        import re
        offer = None
        m = re.search(r"\$?\b(\d{2,4})\b", text)
        if m:
            try:
                offer = int(m.group(1))
            except Exception:
                offer = None

        # Read item pricing
        price = None
        bottom = None
        if matched_item:
            price = matched_item.get('price') or matched_item.get('Price')
            bottom = matched_item.get('bottom') or matched_item.get('Bottom')

        # Availability checks
        if any(kw in text for kw in ["available", "still available", "is this still"]):
            p = price if price is not None else "the listed"
            return f"Yes, it's available. Price is {p}. Are you looking to pick up today or tomorrow?"

        # Shipping inquiries
        if any(kw in text for kw in ["ship", "shipping", "paypal", "mail"]):
            return "I can ship via USPS and accept PayPal. What city/ZIP should I ship to?"

        # Offers
        if offer is not None and bottom is not None:
            if offer < int(bottom):
                return f"I can't go that low. I can do {bottom} if you can pick up. Interested?"
            elif price is not None and int(bottom) <= offer < int(price):
                return f"I can meet you at {offer}. When would you like to pick up?"
            else:
                return f"{offer} works for me. When would you like to pick up?"

        # Generic scheduling
        if any(kw in text for kw in ["pick up", "pickup", "today", "tomorrow", "when"]):
            return "Great — I’m free this evening and tomorrow afternoon. What time works for you?"

        # Fallback
        title = matched_item.get('Title') or matched_item.get('title') if matched_item else None
        if title:
            return f"Hi! Yes, I’m the seller of '{title}'. Do you have any questions or would you like to make an offer?"
        return "Hi! Do you have any questions or would you like to make an offer?"
    def process_conversations(self, convos=None):
        print("🔎 Checking conversations...")
        # Use provided convos or scan for them
        if not convos:
            convos = self.get_recent_conversations(mode="messages")
        if not convos:
            print("No conversations found.")
            return

        # Click the first candidate (unread prioritized in get_recent_conversations)
        target = convos[0]
        print("📨 Opening conversation (prioritized)…")
        self.open_conversation(target)

        last_message = self.get_last_message()
        print(f"📩 Last message: {last_message}")
        if not last_message:
            return

        # Thread info + state (now includes item_title from header)
        thread_id, buyer_name, item_title_from_header = self.get_thread_info()
        if buyer_name and self.state:
            self.state.set_buyer_name(thread_id or "unknown", buyer_name)
        print(f"🧵 Thread: id={thread_id} buyer={buyer_name}")
        if item_title_from_header:
            print(f"🏷️  Item from header: {item_title_from_header}")

        # Dedupe: only respond to new messages
        if self.state and thread_id:
            if not self.state.has_new_message(thread_id, last_message):
                print("⛔ No new buyer message — skipping reply.")
                return

        # Match item: prioritize header title, fallback to message text
        matched_item = None
        if item_title_from_header:
            matched_item = self.inventory.get_item_by_title(item_title_from_header)
            if matched_item:
                print(f"✅ Matched item from header: {(matched_item.get('Title') or matched_item.get('title'))}")
        
        if not matched_item:
            # Fallback: try matching from message text
            matched_item = self.inventory.get_item_by_title(last_message)
            if matched_item:
                print(f"✅ Matched item from message: {(matched_item.get('Title') or matched_item.get('title'))}")
        
        if matched_item:
            # Update status to IN_CONVO and persist item association
            self.update_item_status(matched_item, "IN_CONVO")
            if self.state and thread_id:
                item_id = matched_item.get('id') or matched_item.get('ID')
                if item_id:
                    self.state.set_item_id(thread_id, item_id)
        else:
            print("⚠️ Could not match item from header or message text")

        # Generate response (rule-based for now)
        response = self.infer_intent_and_reply(last_message, matched_item)
        if not response:
            print("⚠️ No response generated")
            return

        # Send reply
        self.send_message(response, send=True)

        # Mark state after sending
        if self.state and thread_id:
            self.state.mark_seen_message(thread_id, last_message)
        time.sleep(1)

    def _open_first_unread_within_main(self):
        """Inside a 'Marketplace' aggregate thread, try to find and open first unread buyer sub-thread."""
        try:
            main = None
            try:
                main = self.driver.find_element(By.XPATH, "//div[@role='main']")
            except Exception:
                pass
            containers = [main] if main else [self.driver]
            candidates = []
            for root in containers:
                try:
                    links = root.find_elements(By.XPATH, 
                        ".//a[@role='link' and contains(@href, '/messages/t/')]"
                    )
                    for a in links:
                        txt = (a.text or '').strip().lower()
                        aria = (a.get_attribute('aria-label') or '').lower()
                        unread = any(k in txt for k in ['new message', 'new messages']) or any(k in aria for k in ['unread','new'])
                        # Avoid links that are clearly the aggregate itself
                        agg = 'marketplace' in txt and ('new message' in txt or 'new messages' in txt)
                        candidates.append((a, unread, agg, txt[:80]))
                except Exception:
                    continue
            # Prefer unread and non-aggregate
            prio = [c for c in candidates if c[1] and not c[2]] or [c for c in candidates if c[1]] or [c for c in candidates if not c[2]]
            if not prio:
                print("⚠️ No sub-thread links found in main area.")
                return
            chosen = prio[0][0]
            print("➡️ Opening sub-thread from aggregate…")
            try:
                chosen.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", chosen)
            time.sleep(3)
        except Exception as e:
            print(f"⚠️ Drill-down failed: {e}")


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
        # Skip Marketplace Inbox; go directly to Messages
        print("➡️ Navigating directly to Messages page...")
        agent.open_messages()
        convos = agent.get_recent_conversations(mode="messages")
        if not convos:
            print("⚠️ No conversations found on Messages page.")
            return
        # If only aggregate found, try clicking it to expand, then re-scan
        if len(convos) == 1:
            first_text = (convos[0].text or '').lower()
            if 'marketplace' in first_text and ('new message' in first_text or 'new messages' in first_text):
                print("🔓 Clicking Marketplace aggregate to expand…")
                try:
                    convos[0].click()
                    time.sleep(3)
                    # Re-scan after expanding
                    convos = agent.get_recent_conversations(mode="messages")
                    if not convos:
                        print("⚠️ Still no individual threads after expanding aggregate.")
                        return
                except Exception as e:
                    print(f"⚠️ Failed to expand aggregate: {e}")
                    return
        # Process first conversation
        agent.process_conversations(convos)

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
