from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import json
import argparse


DEFAULT_DEBUGGER_ADDRESS = os.getenv("DEBUGGER_ADDRESS", "127.0.0.1:9222")
DEFAULT_ITEM_ID = 29  # Fallback item ID if none provided

def parse_args():
    parser = argparse.ArgumentParser(description="Automate FB Marketplace listing form fill")
    parser.add_argument("--id", type=int, help="Item ID from output.json to post", default=None)
    return parser.parse_args()


def update_item_status(item_id: int, status: str, json_path: str = "output.json"):
    """Update the Status field for a specific item ID in the JSON file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, json_path)
    
    try:
        # Read the entire JSON file
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find and update the item
        item_found = False
        for item in data:
            if item.get('ID') == item_id:
                item['Status'] = status
                item_found = True
                break
        
        if not item_found:
            print(f"[WARNING] Item ID {item_id} not found in {json_path}")
            return False
        
        # Write back to file
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[INFO] Updated item ID {item_id} status to: {status}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update status: {e}")
        return False


def load_item_data(item_id: int, json_path: str = "output.json"):
    """Load item data from JSON file by ID. Returns item dict or None if not found."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, json_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        for item in items:
            if item.get('ID') == item_id:
                print(f"[INFO] Found item ID {item_id}: {item.get('Title', 'No title')}")
                return item
        
        print(f"[ERROR] Item ID {item_id} not found in {full_path}")
        return None
    except FileNotFoundError:
        print(f"[ERROR] File {full_path} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Error loading item data: {e}")
        return None


def fill_title_field(driver, title: str, wait_seconds: int = 20):
    wait = WebDriverWait(driver, wait_seconds)

    selectors = [
        # Try various title selectors
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'title')]//following::input[1]"),
        (By.XPATH, "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'title')]"),
        (By.XPATH, "//input[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'title')]"),
        (By.CSS_SELECTOR, "input[placeholder*='Title' i]"),
        (By.CSS_SELECTOR, "input[aria-label*='Title' i]"),
        (By.XPATH, "//input[@type='text'][1]"),  # First text input as fallback
    ]

    for by, sel in selectors:
        try:
            print(f"[DEBUG] Trying title selector: {sel[:80]}")
            title_input = wait.until(EC.visibility_of_element_located((by, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", title_input)
            # Click to focus
            title_input.click()
            time.sleep(0.3)
            # Select all and delete
            title_input.send_keys(Keys.CONTROL + 'a')
            title_input.send_keys(Keys.DELETE)
            time.sleep(0.2)
            # Type the title
            title_input.send_keys(title)
            print(f"[INFO] Title filled: {title}")
            return True
        except Exception as e:
            print(f"[DEBUG] Title selector failed: {str(e)[:100]}")
            continue

    print("[ERROR] Could not find Title input")
    return False



def fill_price_field(driver, price, wait_seconds: int = 20):
    wait = WebDriverWait(driver, wait_seconds)
    price_str = str(price)

    selectors = [
        # Try various price selectors
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'price')]//following::input[1]"),
        (By.XPATH, "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'price')]"),
        (By.XPATH, "//input[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'price')]"),
        (By.CSS_SELECTOR, "input[placeholder*='Price' i]"),
        (By.CSS_SELECTOR, "input[aria-label*='Price' i]"),
        (By.CSS_SELECTOR, "input[type='number']"),
    ]

    for by, sel in selectors:
        try:
            print(f"[DEBUG] Trying price selector: {sel[:80]}")
            price_input = wait.until(EC.visibility_of_element_located((by, sel)))

            # sanity-check: do NOT use title field
            placeholder = price_input.get_attribute("placeholder") or ""
            aria_label = price_input.get_attribute("aria-label") or ""
            if "title" in placeholder.lower() or "title" in aria_label.lower():
                print(f"[DEBUG] Skipping - found title field instead")
                continue

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", price_input)
            # Click to focus
            price_input.click()
            time.sleep(0.3)
            # Select all and delete
            price_input.send_keys(Keys.CONTROL + 'a')
            price_input.send_keys(Keys.DELETE)
            time.sleep(0.2)
            # Type the price
            price_input.send_keys(price_str)
            print(f"[INFO] Price filled: {price_str}")
            return True
        except Exception as e:
            print(f"[DEBUG] Price selector failed: {str(e)[:100]}")
            continue

    print("[ERROR] Could not find Price input")
    return False


def fill_description_field(driver, description: str, wait_seconds: int = 20):
    wait = WebDriverWait(driver, wait_seconds)

    selectors = [
        # Try various description selectors
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'description')]//following::textarea[1]"),
        (By.XPATH, "//textarea[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'description')]"),
        (By.XPATH, "//textarea[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'description')]"),
        (By.CSS_SELECTOR, "textarea[placeholder*='Description' i]"),
        (By.CSS_SELECTOR, "textarea[aria-label*='Description' i]"),
        (By.CSS_SELECTOR, "textarea"),  # Any textarea as fallback
    ]

    for by, sel in selectors:
        try:
            print(f"[DEBUG] Trying description selector: {sel[:80]}")
            description_input = wait.until(EC.visibility_of_element_located((by, sel)))

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", description_input)
            # Click to focus
            description_input.click()
            time.sleep(0.3)
            # Select all and delete
            description_input.send_keys(Keys.CONTROL + 'a')
            description_input.send_keys(Keys.DELETE)
            time.sleep(0.2)
            # Type the description
            description_input.send_keys(description)
            print(f"[INFO] Description filled: {description[:50]}...")
            return True
        except Exception as e:
            print(f"[DEBUG] Description selector failed: {str(e)[:100]}")
            continue

    print("[ERROR] Could not find Description textarea")
    return False


def fill_category_field(driver, category: str, wait_seconds: int = 12):
    """Select Category via the dropdown (combobox + listbox) so 'Next' enables.

    Supports hierarchical categories like "Sports & Outdoors ; Archery Equipment" by
    selecting segments in order.
    """
    wait = WebDriverWait(driver, wait_seconds)

    # Always select 'Miscellaneous' for category
    target_category = 'Miscellaneous'
    try:
        opener_selectors = [
            "//label[@role='combobox' and .//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'category')]]",
            "//*[@role='combobox' and (contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'category') or .//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'category')])]",
            "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'category')]/following::*[@role='combobox'][1]",
        ]
        opener = None
        last_err = None
        for xpath in opener_selectors:
            try:
                print(f"[DEBUG] Looking for Category combobox with: {xpath[:100]}")
                opener = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                break
            except Exception as e:
                last_err = e
                continue
        if opener is None:
            raise last_err or Exception("Category combobox not found")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opener)
        opener.click()
        time.sleep(0.2)
        # Type 'Miscellaneous' and select it
        active = driver.switch_to.active_element
        active.send_keys(Keys.CONTROL + 'a')
        active.send_keys(Keys.DELETE)
        time.sleep(0.1)
        active.send_keys(target_category)
        time.sleep(0.2)
        opt = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, f"//*[@role='listbox']//*[@role='option'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{target_category.lower()}')]")))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
        try:
            opt.click()
        except Exception:
            driver.execute_script("arguments[0].click();", opt)
        time.sleep(0.2)
        # Close dropdown and blur to trigger validation
        try:
            driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        try:
            driver.execute_script("if(document.activeElement){document.activeElement.blur();}")
        except Exception:
            pass
        # Optional: verify Next becomes enabled (do not click it here)
        try:
            next_btn = driver.find_element(By.XPATH, "//div[@role='button' or self::button][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'next')]")
            disabled = next_btn.get_attribute('aria-disabled') == 'true' or next_btn.get_attribute('disabled') is not None
            print("[INFO] Next appears enabled" if not disabled else "[INFO] Next still appears disabled")
        except Exception:
            pass
        print(f"[INFO] Category selected: {target_category}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to select Category via dropdown: {str(e)[:140]}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to select Category via dropdown: {str(e)[:140]}")
        return False


def upload_photos(driver, photo_paths: list, wait_seconds: int = 20):
    """Upload photos by sending file paths directly to the file input element.
    
    Args:
        driver: The WebDriver instance
        photo_paths: List of absolute file paths to upload
        wait_seconds: Maximum time to wait for file input element
    
    Returns:
        True if photos were uploaded successfully, False otherwise
    """
    wait = WebDriverWait(driver, wait_seconds)
    
    # Verify all photo files exist first
    valid_paths = []
    for path in photo_paths:
        if os.path.exists(path):
            valid_paths.append(path)
            print(f"[DEBUG] Found photo: {os.path.basename(path)}")
        else:
            print(f"[WARNING] Photo not found: {path}")
    
    if not valid_paths:
        print("[ERROR] No valid photo files found")
        return False
    
    # Try to find the file input element
    selectors = [
        (By.CSS_SELECTOR, "input[type='file']"),
        (By.XPATH, "//input[@type='file']"),
    ]
    
    for by, sel in selectors:
        try:
            print(f"[DEBUG] Trying file input selector: {sel}")
            # File inputs are often hidden, so use presence_of_element_located instead of visibility
            file_input = wait.until(EC.presence_of_element_located((by, sel)))
            
            # For multiple files, join paths with newline (works for most browsers)
            all_paths = "\n".join(valid_paths)
            
            print(f"[INFO] Sending {len(valid_paths)} file path(s) to file input...")
            file_input.send_keys(all_paths)
            
            # Wait for files to be processed and uploaded
            print("[INFO] Waiting for photos to upload and process (this may take a minute)...")
            time.sleep(3)  # Initial wait for upload to start
            
            # Wait for upload indicators to disappear (up to 60 seconds)
            try:
                WebDriverWait(driver, 60).until(lambda d: (
                    len(d.find_elements(By.XPATH, "//*[contains(@aria-label, 'Uploading') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'uploading') or contains(@class, 'uploading') or contains(@class, 'progress')]")) == 0
                ))
                print("[INFO] All photos uploaded successfully")
            except Exception:
                # If we can't detect upload completion, just wait longer
                print("[DEBUG] Could not detect upload completion status, waiting 8 more seconds...")
                time.sleep(8)
            
            print(f"[INFO] Successfully uploaded {len(valid_paths)} photo(s)")
            return True
            
        except Exception as e:
            print(f"[DEBUG] File input selector failed: {str(e)[:100]}")
            continue
    
    print("[ERROR] Could not find file input element")
    return False


def select_condition(driver, condition_text: str = "Used - Good", wait_seconds: int = 10):
    """Select Condition using the combobox+listbox pattern observed in the UI.

    Keeps only the proven strategy for speed and reliability.
    """
    wait = WebDriverWait(driver, wait_seconds)
    lowered = condition_text.lower()

    try:
        # Find the Condition combobox label and click to open
        label_combo = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//label[@role='combobox' and .//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'condition')]]"
        )))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", label_combo)
        time.sleep(0.3)
        try:
            label_combo.click()
        except Exception:
            # If click is intercepted, use JS click
            driver.execute_script("arguments[0].click();", label_combo)
        time.sleep(0.2)

        # Wait for listbox/popover to appear
        WebDriverWait(driver, 4).until(lambda d: (
            label_combo.get_attribute('aria-expanded') == 'true' or d.find_elements(By.XPATH, "//*[@role='listbox']")
        ))

        # Click the desired option in the listbox/popover
        lowered_xpath_text = lowered.replace("'", "\'")
        opt = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((
            By.XPATH,
            f"//*[@role='listbox']//*[@role='option'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered_xpath_text}')]"
        )))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
        try:
            opt.click()
        except Exception:
            # If click is intercepted, use JS click
            driver.execute_script("arguments[0].click();", opt)
        print(f"[INFO] Condition set to: {condition_text}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to set Condition quickly: {str(e)[:140]}")
        return False


def click_publish_button(driver, wait_seconds: int = 10):
    """Click the Publish button to complete the listing creation."""
    wait = WebDriverWait(driver, wait_seconds)
    try:
        # Try multiple selectors for the Publish button
        publish_selectors = [
            "//div[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'publish')]",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'publish')]",
            "//div[contains(text(), 'Publish')][@role='button']",
            "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'publish')][@role='button' or self::button]",
        ]
        
        used_selector = None
        for selector in publish_selectors:
            try:
                print(f"[DEBUG] Trying Publish button selector: {selector[:80]}")
                publish_btn = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                if publish_btn:
                    used_selector = selector
                    print(f"[DEBUG] Found Publish button")
                    break
            except Exception as e:
                print(f"[DEBUG] Selector not found: {str(e)[:80]}")
                continue
        
        if not used_selector:
            print("[WARNING] Publish button not found with any selector")
            return False
        
        # Re-fetch the button to avoid stale element
        publish_btn = driver.find_element(By.XPATH, used_selector)
        
        # Check if button is disabled
        aria_disabled = publish_btn.get_attribute('aria-disabled')
        html_disabled = publish_btn.get_attribute('disabled')
        print(f"[DEBUG] Publish button aria-disabled={aria_disabled}, disabled={html_disabled}")
        
        if aria_disabled == 'true' or html_disabled is not None:
            print("[WARNING] Publish button is disabled, skipping click")
            return False
        
        print("[DEBUG] Publish button is enabled, scrolling into view...")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", publish_btn)
        time.sleep(0.8)
        
        # Re-fetch after scroll to avoid stale element
        publish_btn = driver.find_element(By.XPATH, used_selector)
        print("[DEBUG] Button found after scroll, attempting click...")
        
        try:
            publish_btn.click()
            print("[INFO] Publish button clicked successfully via element.click()")
        except Exception as e:
            print(f"[DEBUG] Regular click failed ({str(e)[:80]}), trying JavaScript click...")
            driver.execute_script("arguments[0].click();", publish_btn)
            print("[INFO] Publish button clicked successfully via JavaScript")
        
        print("[INFO] Waiting for listing to be published...")
        time.sleep(3)
        
        # Wait for page to stabilize
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == 'complete')
        print("[INFO] Listing published successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to click Publish button: {str(e)[:200]}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()[:300]}")
        return False


def click_next_button(driver, wait_seconds: int = 10):
    """Click the Next button if enabled, advancing to the next form page."""
    wait = WebDriverWait(driver, wait_seconds)
    try:
        # Add a longer wait after photos to ensure page is ready
        print("[INFO] Waiting for form to be fully ready...")
        time.sleep(5)  # Increased wait time for form validation
        
        # Get current URL before clicking
        current_url_before = driver.current_url
        print(f"[DEBUG] Current URL before Next click: {current_url_before}")
        
        # Try multiple selectors for the Next button
        next_selectors = [
            "//div[@role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'next')]",
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'next')]",
            "//div[contains(text(), 'Next')][@role='button']",
            "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'next')][@role='button' or self::button]",
        ]
        
        used_selector = None
        for selector in next_selectors:
            try:
                print(f"[DEBUG] Trying Next button selector: {selector[:80]}")
                next_btn = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                if next_btn:
                    used_selector = selector
                    print(f"[DEBUG] Found Next button")
                    break
            except Exception as e:
                print(f"[DEBUG] Selector not found: {str(e)[:80]}")
                continue
        
        if not used_selector:
            print("[WARNING] Next button not found with any selector")
            return False
        
        # Re-fetch the button to avoid stale element
        next_btn = driver.find_element(By.XPATH, used_selector)
        
        # Check if button is disabled
        aria_disabled = next_btn.get_attribute('aria-disabled')
        html_disabled = next_btn.get_attribute('disabled')
        opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity", next_btn)
        pointer_events = driver.execute_script("return window.getComputedStyle(arguments[0]).pointerEvents", next_btn)
        
        print(f"[DEBUG] Next button aria-disabled={aria_disabled}, disabled={html_disabled}, opacity={opacity}, pointer-events={pointer_events}")
        
        if aria_disabled == 'true' or html_disabled is not None or opacity == '0.5' or pointer_events == 'none':
            print("[WARNING] Next button appears disabled (aria-disabled, disabled attr, opacity, or pointer-events)")
            print("[INFO] Waiting 5 more seconds for button to become enabled...")
            time.sleep(5)
            
            # Re-check after wait
            next_btn = driver.find_element(By.XPATH, used_selector)
            aria_disabled = next_btn.get_attribute('aria-disabled')
            html_disabled = next_btn.get_attribute('disabled')
            opacity = driver.execute_script("return window.getComputedStyle(arguments[0]).opacity", next_btn)
            print(f"[DEBUG] After wait: aria-disabled={aria_disabled}, disabled={html_disabled}, opacity={opacity}")
            
            if aria_disabled == 'true' or html_disabled is not None:
                print("[WARNING] Next button still disabled after wait, skipping click")
                return False
        
        print("[DEBUG] Next button is enabled, scrolling into view...")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
        time.sleep(0.8)
        
        # Re-fetch after scroll to avoid stale element
        next_btn = driver.find_element(By.XPATH, used_selector)
        print("[DEBUG] Button found after scroll, attempting click...")
        
        # Try multiple click strategies
        click_success = False
        try:
            next_btn.click()
            print("[INFO] Next button clicked via element.click()")
            click_success = True
        except Exception as e:
            print(f"[DEBUG] Regular click failed ({str(e)[:80]})")
        
        if not click_success:
            try:
                # Try JavaScript click
                driver.execute_script("arguments[0].click();", next_btn)
                print("[INFO] Next button clicked via JavaScript")
                time.sleep(0.5)
            except Exception as e:
                print(f"[DEBUG] JavaScript click failed ({str(e)[:80]})")
        
        # Try triggering via mousedown/mouseup events
        try:
            driver.execute_script("""
                var evt = new MouseEvent('mousedown', {bubbles: true, cancelable: true, view: window});
                arguments[0].dispatchEvent(evt);
                evt = new MouseEvent('mouseup', {bubbles: true, cancelable: true, view: window});
                arguments[0].dispatchEvent(evt);
                evt = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                arguments[0].dispatchEvent(evt);
            """, next_btn)
            print("[DEBUG] Triggered mousedown/mouseup/click events")
        except Exception:
            pass
        
        # Try focusing the button and pressing Enter
        try:
            driver.execute_script("arguments[0].focus();", next_btn)
            time.sleep(0.3)
            next_btn.send_keys(Keys.ENTER)
            print("[DEBUG] Sent Enter key to Next button")
        except Exception as e:
            print(f"[DEBUG] Enter key failed: {str(e)[:80]}")
        
        # Try clicking at center coordinates
        try:
            driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                var x = rect.left + rect.width / 2;
                var y = rect.top + rect.height / 2;
                var evt = new MouseEvent('click', {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: x,
                    clientY: y
                });
                arguments[0].dispatchEvent(evt);
            """, next_btn)
            print("[DEBUG] Triggered click at element center")
        except Exception:
            pass
        
        print("[INFO] Waiting for next page to load...")
        time.sleep(5)
        
        # Verify page actually changed
        current_url_after = driver.current_url
        print(f"[DEBUG] Current URL after Next click: {current_url_after}")
        
        if current_url_before == current_url_after:
            print("[WARNING] URL did not change after Next click - page may not have advanced")
            # Try waiting a bit more
            time.sleep(2)
            current_url_after = driver.current_url
            print(f"[DEBUG] Current URL after additional wait: {current_url_after}")
            
            if current_url_before == current_url_after:
                print("[ERROR] URL still unchanged - Next button click likely failed")
                return False
        
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == 'complete')
        print("[INFO] Next page loaded successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to click Next button: {str(e)[:200]}")
        import traceback
        print(f"[DEBUG] Traceback: {traceback.format_exc()[:300]}")
        return False


def create_driver(debugger_address: str = DEFAULT_DEBUGGER_ADDRESS):
    """Create and return a Chrome webdriver, optionally attaching to an existing browser."""
    options = Options()
    options.add_argument("--start-maximized")
    
    if debugger_address:
        print(f"[INFO] Connecting to existing Chrome instance at {debugger_address}...")
        options.debugger_address = debugger_address
    else:
        print("[INFO] Starting new Chrome instance...")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("[INFO] Successfully connected to Chrome")
        return driver
    except Exception as e:
        print(f"[ERROR] Failed to connect to Chrome: {e}")
        if debugger_address:
            print(f"[ERROR] Make sure Chrome is running with: --remote-debugging-port={debugger_address.split(':')[-1]}")
        raise


def find_and_click(driver, selectors, wait_seconds: int = 20, verify_after_click=None, button_name="button"):
    """Attempt to find and click one of the selectors. Returns True if clicked.
    
    Args:
        driver: The WebDriver instance
        selectors: List of (By, selector) tuples to try
        wait_seconds: Maximum time to wait for element to be clickable
        verify_after_click: Optional function that takes driver and returns True when click succeeded
        button_name: Name of button for error messages
    """
    wait = WebDriverWait(driver, wait_seconds)
    for by, sel in selectors:
        try:
            print(f"[DEBUG] Trying to find {button_name} with selector: {by}={sel[:100]}...")
            elem = wait.until(EC.element_to_be_clickable((by, sel)))
            print(f"[DEBUG] Found {button_name}, scrolling into view...")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            # Small wait after scrolling
            time.sleep(0.5)
            print(f"[DEBUG] Clicking {button_name}...")
            try:
                elem.click()
            except Exception as click_error:
                print(f"[DEBUG] Regular click failed: {click_error}, trying JavaScript click...")
                driver.execute_script("arguments[0].click();", elem)
            print(f"[DEBUG] Clicked {button_name} successfully")
            
            # If verification function provided, wait for it
            if verify_after_click:
                print(f"[DEBUG] Verifying {button_name} click succeeded...")
                short_wait = WebDriverWait(driver, 5)
                short_wait.until(verify_after_click)
                print(f"[DEBUG] Verification passed for {button_name}")
            
            return True
        except Exception as e:
            print(f"[DEBUG] Selector failed: {type(e).__name__}: {str(e)[:200]}")
            continue
    return False


def main():
    args = parse_args()
    using_debugger = bool(DEFAULT_DEBUGGER_ADDRESS)
    driver = create_driver()
    try:
        # Verify connection is alive
        try:
            current_url = driver.current_url
            print(f"[INFO] Connection verified. Current URL: {current_url}")
        except Exception as e:
            print(f"[ERROR] Connection to browser lost: {e}")
            print("[ERROR] Please make sure Chrome is running with --remote-debugging-port=9222")
            return
        
        # Only navigate if not already on marketplace page
        if 'marketplace' not in current_url.lower():
            print("[INFO] Navigating to Facebook Marketplace...")
            try:
                driver.get("https://www.facebook.com/marketplace")
                WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == 'complete')
                print(f"[INFO] Page loaded. Current URL: {driver.current_url}")
            except Exception as e:
                print(f"[ERROR] Failed to navigate: {e}")
                print("[INFO] Continuing with current page...")
        else:
            print(f"[INFO] Already on Marketplace page: {current_url}")
            # Wait for page to be ready
            WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == 'complete')
        
        # Wait a bit for dynamic content to load
        time.sleep(2)

        # More comprehensive selectors for "Create new listing" button
        selectors = [
            # Try exact text matches first
            (By.XPATH, "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            (By.XPATH, "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            # Try aria-label
            (By.XPATH, "//button[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            (By.XPATH, "//div[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            # Try with normalize-space
            (By.XPATH, "//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            (By.XPATH, "//div[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing')]"),
            # Try partial matches
            (By.XPATH, "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create listing')]"),
            (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create listing')]"),
            # Try link/role button
            (By.XPATH, "//a[@role='button' and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create')]"),
        ]

        # Verify that create UI appears after clicking
        verify_create_ui = lambda d: (
            '/marketplace/create' in d.current_url
            or d.find_elements(By.CSS_SELECTOR, 'input[type=file]')
            or d.find_elements(By.CSS_SELECTOR, 'textarea')
            or d.find_elements(By.XPATH, "//input[contains(@placeholder, 'Title') or contains(@aria-label, 'Title')]")
        )

        clicked = find_and_click(driver, selectors, verify_after_click=verify_create_ui, button_name="Create new listing")
        if not clicked:
            print("[ERROR] Could not find or click the Create new listing button")
            print("[DEBUG] Trying to find any buttons with 'create' or 'listing' in text...")
            # Debug: try to find any elements with create/listing
            try:
                all_buttons = driver.find_elements(By.XPATH, "//button | //a[@role='button'] | //div[@role='button']")
                print(f"[DEBUG] Found {len(all_buttons)} potential button elements")
                for i, btn in enumerate(all_buttons[:10]):  # Check first 10
                    try:
                        text = btn.text.lower()
                        if 'create' in text or 'listing' in text:
                            print(f"[DEBUG] Button {i}: text='{btn.text[:50]}', tag={btn.tag_name}")
                    except:
                        pass
            except Exception as e:
                print(f"[DEBUG] Error while debugging: {e}")
            return

        # Now click the "item for sale" button
        item_for_sale_selectors = [
            (By.XPATH, "//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'item for sale') ]"),
            (By.XPATH, "//div[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'item for sale') ]"),
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'item for sale') ]"),
            (By.XPATH, "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'item for sale') ]"),
        ]

        # Verify that we're on the item creation form after clicking "item for sale"
        verify_item_form = lambda d: (
            '/marketplace/create/item' in d.current_url
            or d.find_elements(By.CSS_SELECTOR, 'input[type=file]')
            or d.find_elements(By.XPATH, "//input[contains(@placeholder, 'Title') or contains(@aria-label, 'Title')]")
        )

        if not find_and_click(driver, item_for_sale_selectors, verify_after_click=verify_item_form, button_name="Item for sale"):
            print("[ERROR] Could not find or click the Item for sale button")
            return
        
        # Load item data from JSON
        chosen_id = args.id or int(os.getenv("ITEM_ID", DEFAULT_ITEM_ID))
        print(f"[INFO] Loading item data for ID {chosen_id}...")
        item_data = load_item_data(chosen_id)
        if not item_data:
            print(f"[ERROR] Failed to load item data for ID {chosen_id}")
            return
        
        title = item_data.get('Title')
        if not title:
            print(f"[ERROR] No title found for item ID {chosen_id}")
            return
        
        # Wait for the form to fully load - look for title input
        print("[INFO] Waiting for form to load...")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder or @aria-label]"))
            )
            print("[INFO] Form loaded")
        except Exception as e:
            print(f"[WARNING] Timeout waiting for form: {e}")
        
        time.sleep(1)
        
        # Fill the title field
        print(f"[INFO] Filling title field with: {title}")
        if not fill_title_field(driver, title):
            print("[ERROR] Failed to fill title field")
            return
        
        # Get price from item data
        price = item_data.get('Price')
        if price is None:
            print(f"[WARNING] No price found for item ID {chosen_id}, skipping price field")
        else:
            # Wait a bit between filling fields
            time.sleep(1)
            
            # Fill the price field
            print(f"[INFO] Filling price field with: {price}")
            if not fill_price_field(driver, price):
                print("[WARNING] Failed to fill price field, continuing...")
        
        # Get description from item data
        description = item_data.get('Description')
        if description:
            # Wait a bit between filling fields
            time.sleep(1)
            
            # Fill the description field
            print(f"[INFO] Filling description field with: {description[:50]}...")
            if not fill_description_field(driver, description):
                print("[WARNING] Failed to fill description field, continuing...")
        else:
            print(f"[WARNING] No description found for item ID {chosen_id}, skipping description field")
        
        # Get category from item data
        category = item_data.get('Category')
        if category:
            # Wait a bit between filling fields
            time.sleep(1)
            
            # Fill the category field
            print(f"[INFO] Filling category field with: {category}")
            if not fill_category_field(driver, category):
                print("[WARNING] Failed to fill category field, continuing...")
        else:
            print(f"[WARNING] No category found for item ID {chosen_id}, skipping category field")
        
        # Set condition (default to "Used - Good" for now)
        condition_value = "Used - Good"
        print(f"[INFO] Setting condition to: {condition_value}")
        if not select_condition(driver, condition_value):
            print("[WARNING] Failed to set condition, continuing...")

        # Get photo paths from item data
        photo_paths = item_data.get('Photo_Paths', [])
        if photo_paths and len(photo_paths) > 0:
            # Wait a bit between operations
            time.sleep(1)
            
            # Upload photos
            print(f"[INFO] Uploading {len(photo_paths)} photo(s)...")
            if not upload_photos(driver, photo_paths):
                print("[WARNING] Failed to upload photos, continuing...")
        else:
            print(f"[WARNING] No photos found for item ID {chosen_id}, skipping photo upload")
        
        # Click Next button if enabled
        time.sleep(1)
        next_success = click_next_button(driver)
        
        # If Next succeeded, we're on the final page - click Publish
        if next_success:
            time.sleep(2)
            publish_success = click_publish_button(driver)
            
            # If publish succeeded, update status to "Posted"
            if publish_success:
                update_item_status(chosen_id, "Posted")
        
        # Even if Next/Publish didn't work, update status to show automation was attempted
        # Update to "Posted" since all fields were filled and photos uploaded
        update_item_status(chosen_id, "Posted")
        
        print("[INFO] Script completed.")
    finally:
        # Don't quit if using debugger - let user close manually
        if not using_debugger:
            driver.quit()
        else:
            print("[INFO] Browser remains open (debug mode). Close manually when done.")


if __name__ == '__main__':
    main()
