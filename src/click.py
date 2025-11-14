from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import time


DEFAULT_DEBUGGER_ADDRESS = os.getenv("DEBUGGER_ADDRESS", "127.0.0.1:9222")


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
        
        print("[INFO] Script completed.")
    finally:
        # Don't quit if using debugger - let user close manually
        if not using_debugger:
            driver.quit()
        else:
            print("[INFO] Browser remains open (debug mode). Close manually when done.")


if __name__ == '__main__':
    main()
