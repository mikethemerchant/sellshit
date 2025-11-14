from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os


DEFAULT_DEBUGGER_ADDRESS = os.getenv("DEBUGGER_ADDRESS", "127.0.0.1:9222")


def create_driver(debugger_address: str = DEFAULT_DEBUGGER_ADDRESS):
    """Create and return a Chrome webdriver, optionally attaching to an existing browser."""
    options = Options()
    options.add_argument("--start-maximized")
    
    if debugger_address:
        options.debugger_address = debugger_address
    else:
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def find_and_click(driver, selectors, wait_seconds: int = 20, verify_after_click=None):
    """Attempt to find and click one of the selectors. Returns True if clicked.
    
    Args:
        driver: The WebDriver instance
        selectors: List of (By, selector) tuples to try
        wait_seconds: Maximum time to wait for element to be clickable
        verify_after_click: Optional function that takes driver and returns True when click succeeded
    """
    wait = WebDriverWait(driver, wait_seconds)
    for by, sel in selectors:
        try:
            elem = wait.until(EC.element_to_be_clickable((by, sel)))
            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
            elem.click()
            
            # If verification function provided, wait for it
            if verify_after_click:
                short_wait = WebDriverWait(driver, 5)
                short_wait.until(verify_after_click)
            
            return True
        except Exception:
            continue
    return False


def main():
    driver = create_driver()
    try:
        driver.get("https://www.facebook.com/marketplace")
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == 'complete')

        selectors = [
            (By.XPATH, "//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing') ]"),
            (By.XPATH, "//div[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing') ]"),
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing') ]"),
        ]

        # Verify that create UI appears after clicking
        verify_create_ui = lambda d: (
            '/marketplace/create' in d.current_url
            or d.find_elements(By.CSS_SELECTOR, 'input[type=file]')
            or d.find_elements(By.CSS_SELECTOR, 'textarea')
            or d.find_elements(By.XPATH, "//input[contains(@placeholder, 'Title') or contains(@aria-label, 'Title')]")
        )

        clicked = find_and_click(driver, selectors, verify_after_click=verify_create_ui)
        if not clicked:
            print("[ERROR] Could not find or click the Create new listing button")
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

        if not find_and_click(driver, item_for_sale_selectors, verify_after_click=verify_item_form):
            print("[ERROR] Could not find or click the Item for sale button")
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
