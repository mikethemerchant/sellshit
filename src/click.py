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


DEFAULT_DEBUGGER_ADDRESS = os.getenv("DEBUGGER_ADDRESS", "127.0.0.1:9222")
ITEM_ID = 26  # Item ID to use for posting


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


def fill_category_field(driver, category: str, wait_seconds: int = 20):
    wait = WebDriverWait(driver, wait_seconds)

    selectors = [
        # Try various category selectors
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'category')]//following::input[1]"),
        (By.XPATH, "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'category')]"),
        (By.XPATH, "//input[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'category')]"),
        (By.CSS_SELECTOR, "input[placeholder*='Category' i]"),
        (By.CSS_SELECTOR, "input[aria-label*='Category' i]"),
    ]

    for by, sel in selectors:
        try:
            print(f"[DEBUG] Trying category selector: {sel[:80]}")
            category_input = wait.until(EC.visibility_of_element_located((by, sel)))

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", category_input)
            # Click to focus
            category_input.click()
            time.sleep(0.3)
            # Select all and delete
            category_input.send_keys(Keys.CONTROL + 'a')
            category_input.send_keys(Keys.DELETE)
            time.sleep(0.2)
            # Type the category
            category_input.send_keys(category)
            print(f"[INFO] Category filled: {category}")
            # Wait a moment for any autocomplete dropdown to appear
            time.sleep(0.5)
            # Press Enter to select the first match or confirm
            category_input.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            print(f"[DEBUG] Category selector failed: {str(e)[:100]}")
            continue

    print("[ERROR] Could not find Category input")
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
            
            # Wait a moment for files to be processed
            time.sleep(1)
            
            print(f"[INFO] Successfully uploaded {len(valid_paths)} photo(s)")
            return True
            
        except Exception as e:
            print(f"[DEBUG] File input selector failed: {str(e)[:100]}")
            continue
    
    print("[ERROR] Could not find file input element")
    return False


def select_condition(driver, condition_text: str = "Used - Good", wait_seconds: int = 20):
    """Select a condition value from the Condition dropdown/selector.

    Tries multiple strategies: typing into a combobox, clicking a button to open a
    menu, then clicking the desired option.
    """
    wait = WebDriverWait(driver, wait_seconds)

    lowered = condition_text.lower()

    # Strategy A: find an input/combobox with Condition label and type + Enter
    combo_selectors = [
        (By.XPATH, "//*[@role='combobox' and (contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'condition') or contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'condition'))]"),
        (By.XPATH, "//input[(contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'condition') or contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'condition'))]"),
    ]

    for by, sel in combo_selectors:
        try:
            print(f"[DEBUG] Trying condition combobox/input: {sel[:100]}")
            box = wait.until(EC.element_to_be_clickable((by, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", box)
            box.click()
            time.sleep(0.2)
            box.send_keys(Keys.CONTROL + 'a')
            box.send_keys(Keys.DELETE)
            time.sleep(0.1)
            box.send_keys(condition_text)
            time.sleep(0.3)
            box.send_keys(Keys.ENTER)
            # Verify text appears near condition control
            try:
                WebDriverWait(driver, 5).until(lambda d: d.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]"))
                print(f"[INFO] Condition set to: {condition_text}")
                return True
            except Exception:
                pass
        except Exception as e:
            print(f"[DEBUG] Condition combobox attempt failed: {str(e)[:100]}")

    # Strategy B: click a button/field labeled Condition to open a menu, then pick option
    opener_selectors = [
        (By.XPATH, "//*[@role='button' and contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'condition') ]"),
        (By.XPATH, "//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'condition')]/following::*[@role='button'][1]"),
        (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'condition')][ancestor::*[@role='button']][1]/ancestor::*[@role='button'][1]"),
    ]

    for by, sel in opener_selectors:
        try:
            print(f"[DEBUG] Trying condition opener: {sel[:100]}")
            opener = wait.until(EC.element_to_be_clickable((by, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opener)
            opener.click()
            time.sleep(0.3)

            # Now try to click the desired option
            option_selectors = [
                (By.XPATH, f"//*[@role='option' or @role='menuitem' or @role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]"),
                (By.XPATH, f"//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]"),
                (By.XPATH, f"//div[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]"),
            ]
            for oby, osel in option_selectors:
                try:
                    print(f"[DEBUG] Trying condition option: {osel[:100]}")
                    opt = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((oby, osel)))
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
                    opt.click()
                    print(f"[INFO] Condition set to: {condition_text}")
                    return True
                except Exception as e:
                    print(f"[DEBUG] Condition option failed: {str(e)[:100]}")
                    continue
        except Exception as e:
            print(f"[DEBUG] Condition opener failed: {str(e)[:100]}")

    # Strategy C: direct radio-style options search by text and click
    radio_option_selectors = [
        (By.XPATH, f"//*[@role='radio' and contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]"),
        (By.XPATH, f"//*[@role='button' and contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]"),
        (By.XPATH, f"//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]"),
        (By.XPATH, f"//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered}')]/ancestor::*[@role='radio' or @role='button'][1]"),
    ]

    for by, sel in radio_option_selectors:
        try:
            print(f"[DEBUG] Trying direct condition option: {sel[:100]}")
            opt = wait.until(EC.element_to_be_clickable((by, sel)))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
            opt.click()
            # Verify selection via ARIA state
            try:
                WebDriverWait(driver, 5).until(lambda d: (
                    opt.get_attribute('aria-checked') == 'true'
                    or opt.get_attribute('aria-selected') == 'true'
                    or condition_text.lower() in (opt.text or '').lower()
                ))
            except Exception:
                pass
            print(f"[INFO] Condition set to: {condition_text}")
            return True
        except Exception as e:
            print(f"[DEBUG] Direct option click failed: {str(e)[:100]}")
            continue

    # Strategy D (from provided HTML): label element acting as combobox containing a span with text 'Condition'
    try:
        print("[DEBUG] Trying label[role='combobox'] for Condition")
        label_combo = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//label[@role='combobox' and .//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'condition')]]"
        )))
        # Debug: print snippet
        try:
            snippet = driver.execute_script("return arguments[0].outerHTML.slice(0,300);", label_combo)
            print(f"[DEBUG] Combobox snippet: {snippet}")
        except Exception:
            pass

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", label_combo)
        label_combo.click()
        time.sleep(0.3)
        # Wait for aria-expanded to become true OR a listbox to appear
        try:
            WebDriverWait(driver, 5).until(lambda d: (
                label_combo.get_attribute('aria-expanded') == 'true' or d.find_elements(By.XPATH, "//*[@role='listbox']")
            ))
        except Exception:
            pass

        # Find option inside listbox/popover
        lowered_xpath_text = lowered.replace("'", "\'")
        option_in_listbox_selectors = [
            (By.XPATH, f"//*[@role='listbox']//*[@role='option'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered_xpath_text}')]"),
            (By.XPATH, f"//*[@role='listbox']//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered_xpath_text}')]"),
            (By.XPATH, f"//*[contains(@id,'mount') or contains(@role,'dialog') or @role='menu' or @role='listbox']//*[@role='option' or @role='menuitem' or @role='button'][contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{lowered_xpath_text}')]"),
        ]
        for oby, osel in option_in_listbox_selectors:
            try:
                print(f"[DEBUG] Trying listbox option: {osel[:120]}")
                opt = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((oby, osel)))
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", opt)
                opt.click()
                time.sleep(0.2)
                print(f"[INFO] Condition set to: {condition_text}")
                return True
            except Exception as e:
                print(f"[DEBUG] Listbox option failed: {str(e)[:100]}")
                continue
    except Exception as e:
        print(f"[DEBUG] Label combobox strategy failed: {str(e)[:120]}")

    print("[ERROR] Could not set Condition")
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
        print(f"[INFO] Loading item data for ID {ITEM_ID}...")
        item_data = load_item_data(ITEM_ID)
        if not item_data:
            print(f"[ERROR] Failed to load item data for ID {ITEM_ID}")
            return
        
        title = item_data.get('Title')
        if not title:
            print(f"[ERROR] No title found for item ID {ITEM_ID}")
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
            print(f"[WARNING] No price found for item ID {ITEM_ID}, skipping price field")
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
            print(f"[WARNING] No description found for item ID {ITEM_ID}, skipping description field")
        
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
            print(f"[WARNING] No category found for item ID {ITEM_ID}, skipping category field")
        
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
            print(f"[WARNING] No photos found for item ID {ITEM_ID}, skipping photo upload")
        
        print("[INFO] Script completed.")
    finally:
        # Don't quit if using debugger - let user close manually
        if not using_debugger:
            driver.quit()
        else:
            print("[INFO] Browser remains open (debug mode). Close manually when done.")


if __name__ == '__main__':
    main()
