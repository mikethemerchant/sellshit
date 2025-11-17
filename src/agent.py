import json
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

OUTPUT_JSON = "output.json"

###########################################################################
# SETUP: Connect to already-open Chrome in remote debugging mode
###########################################################################
def get_driver():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # NOTE: UPDATE THIS TO MATCH YOUR LOCAL ENV
    CHROMEDRIVER_PATH = r"C:\temp\chromedriver.exe"

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()
    return driver


###########################################################################
# JSON Storage Helpers
###########################################################################
class Inventory:
    def __init__(self, output_path):
        self.path = output_path
        self.items = self.load()

    def load(self):
        with open(self.path, "r") as f:
            return json.load(f)

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.items, f, indent=4)

    def get_item_by_title(self, title):
        for item in self.items:
            if item["title"].lower() in title.lower():
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
        self.driver.get("https://www.facebook.com/marketplace/inbox")
        time.sleep(5)

    def get_recent_conversations(self):
        """
        Returns a list of visible conversation elements.
        """
        try:
            convo_selector = 'div[role="grid"] div[role="row"]'
            rows = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, convo_selector))
            )
            return rows
        except Exception as e:
            print("⚠️ Could not find conversations:", e)
            return []

    def open_conversation(self, convo_element):
        """
        Click a conversation item.
        """
        try:
            self.driver.execute_script("arguments[0].click();", convo_element)
            time.sleep(3)
        except Exception as e:
            print("⚠️ Failed to click a conversation:", e)

    def get_last_message(self):
        """
        Returns the last message text in the open conversation.
        """
        try:
            messages = self.driver.find_elements(By.CSS_SELECTOR, 'div[dir="auto"]')
            if not messages:
                return None
            return messages[-1].text
        except Exception:
            return None

    def send_message(self, text):
        """
        Type into the Messenger input box but DO NOT send yet (debug mode).
        """
        try:
            input_box = self.driver.find_element(By.CSS_SELECTOR, "div[aria-label='Message'][contenteditable='true']")
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
                print(f"Matched item: {matched_item['title']}")

            # DEBUG: do not send yet
            response = f"Thanks for reaching out! (DEBUG MODE) You said: '{last_message}'"
            self.send_message(response)

            time.sleep(2)


###########################################################################
# MAIN LOOP
###########################################################################
def main():
    print("🚀 Starting Marketplace Agent...")

    inventory = Inventory(OUTPUT_JSON)
    driver = get_driver()
    agent = MessengerAgent(driver, inventory)

    agent.open_messenger()

    # MAIN LOOP (safe debug interval 60 sec)
    while True:
        try:
            agent.process_conversations()
        except Exception as e:
            print("❌ Error in main loop:", e)

        print("⏳ Sleeping 60s...\n")
        time.sleep(60)


if __name__ == "__main__":
    main()
