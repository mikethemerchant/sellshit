from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from selenium.webdriver import ActionChains


DEFAULT_DEBUGGER_ADDRESS = os.getenv("DEBUGGER_ADDRESS", "127.0.0.1:9222")


def create_driver(debugger_address: str = DEFAULT_DEBUGGER_ADDRESS):
    """Create and return a Chrome webdriver using a remote debugger address.

    Keeps original options (remote debugger) so you can attach to an already-open
    browser for a logged-in session.
    """
    options = Options()
    # attach to an existing debug-enabled Chrome instance if provided
    if debugger_address:
        options.debugger_address = debugger_address
        # when attaching to an existing Chrome via debugger address, don't set
        # certain experimental chrome options (they can be rejected by the
        # remote browser). Keep options minimal.
        options.add_argument("--start-maximized")
    else:
        options.add_argument("--start-maximized")
        # when starting a new Chrome session, it's safe to reduce automation
        # flags to make the browser look more like a regular user session.
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def find_and_click(driver, selectors, wait_seconds: int = 20):
    """Attempt to find and click one of the selectors. Returns True if clicked."""
    wait = WebDriverWait(driver, wait_seconds)
    for by, sel in selectors:
        try:
            print("Trying selector:", sel)
            elem = wait.until(EC.element_to_be_clickable((by, sel)))
            print("Found element text:", getattr(elem, 'text', ''))
            try:
                outer = driver.execute_script("return arguments[0].outerHTML.slice(0,200);", elem)
            except Exception:
                outer = None
            print("Found element snippet:", outer)
            # scroll into view and try native click first
            driver.execute_script("arguments[0].scrollIntoView(true);", elem)
            # Try a sequence of click methods until one appears to work (i.e. page navigates
            # to the create listing area or a known create-form element appears).
            click_methods = []
            click_methods.append(('native', lambda e: e.click()))
            click_methods.append(('actionchains', lambda e: ActionChains(driver).move_to_element(e).click(e).perform()))
            click_methods.append(('js', lambda e: driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));", e)))
            # Try a JS click targeted at the element's center (some handlers rely on coordinates)
            def js_center_click(e):
                driver.execute_script(
                    "var r = arguments[0].getBoundingClientRect();"
                    "var cx = r.left + r.width/2; var cy = r.top + r.height/2;"
                    "arguments[0].dispatchEvent(new MouseEvent('mousemove', {clientX: cx, clientY: cy, bubbles: true}));"
                    "arguments[0].dispatchEvent(new MouseEvent('mousedown', {clientX: cx, clientY: cy, bubbles: true}));"
                    "arguments[0].dispatchEvent(new MouseEvent('mouseup', {clientX: cx, clientY: cy, bubbles: true}));"
                    "arguments[0].dispatchEvent(new MouseEvent('click', {clientX: cx, clientY: cy, bubbles: true}));",
                    e
                )

            click_methods.append(('js_center', js_center_click))

            for name, fn in click_methods:
                try:
                    fn(elem)
                    print(f"Tried click method: {name}")
                    # wait briefly to see if navigation or create-form appears
                    try:
                        short_wait = WebDriverWait(driver, 5)
                        # check for URL change to the create path OR presence of common create-form inputs
                        created = short_wait.until(lambda d: (
                            '/marketplace/create' in d.current_url
                            or d.find_elements(By.CSS_SELECTOR, 'input[type=file]')
                            or d.find_elements(By.CSS_SELECTOR, 'textarea')
                            or d.find_elements(By.XPATH, "//input[contains(@placeholder, 'Title') or contains(@aria-label, 'Title')]")
                        ))
                    except Exception:
                        created = False

                    if created:
                        print(f"[SUCCESS] Click produced expected create UI (method={name})")
                        return True
                    else:
                        print(f"Click method {name} did not produce create UI; trying next method")
                except Exception as e:
                    print(f"Click method {name} failed: {e}")
                    continue
            # none of the click methods produced the create UI for this selector
            print("All click methods tried for selector but create UI not detected yet.")
            return False
        except Exception as e:
            print("Selector failed:", sel, "-", e)
            continue
    return False


def main():
    driver = create_driver()
    try:
        driver.get("https://www.facebook.com/marketplace")
        # wait for initial page load to complete instead of sleeping
        WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == 'complete')

        # Use case-insensitive contains via translate() to be more robust
        selectors = [
            (By.XPATH, "//span[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing') ]"),
            (By.XPATH, "//div[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing') ]"),
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create new listing') ]"),
        ]

        clicked = find_and_click(driver, selectors)
        if not clicked:
            print("[ERROR] Could not find or click the Create new listing button")

    # no static sleep here - find_and_click verifies the create UI appears
    finally:
        driver.quit()


if __name__ == '__main__':
    main()
