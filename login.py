import json
import os
import sys
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

SESSION_FILE = "substack_session.json"

import argparse
from urllib.parse import urlparse


def get_brave_path():
    override = os.getenv("BRAVE_EXECUTABLE_PATH")
    if override:
        return override
    if sys.platform == "darwin":
        return "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    if sys.platform.startswith("linux"):
        return "/usr/bin/brave-browser"
    if sys.platform == "win32":
        return r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    raise RuntimeError("Unsupported platform; set BRAVE_EXECUTABLE_PATH")


def run():
    parser = argparse.ArgumentParser(description="Login helper for Substack scraper")
    parser.add_argument("url", nargs="?", help="Newsletter URL (e.g. https://www.lennysnewsletter.com)")
    args = parser.parse_args()

    print("Launching browser for login...")
    brave_path = get_brave_path()
    if not os.path.exists(brave_path):
        raise FileNotFoundError(
            f"Brave not found at {brave_path}. "
            "Install Brave or set BRAVE_EXECUTABLE_PATH in your .env / shell."
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, executable_path=brave_path)
        context = browser.new_context()
        page = context.new_page()

        if args.url:
             print(f"Navigating to {args.url} ...")
             page.goto(args.url)
             domain = urlparse(args.url).netloc
             session_file = f"substack_session_{domain}.json"
        else:
             print("Navigating to Substack login...")
             page.goto("https://substack.com/sign-in")
             session_file = "substack_session.json"

        print("\n" + "="*50)
        print("ACTION REQUIRED: Log in to Substack in the browser window.")
        print("Once you are successfully logged in and can see your dashboard/posts,")
        print("press Enter here to save your session.")
        print("="*50 + "\n")
        
        input("Press Enter to save session and exit...")

        # Get cookies
        cookies = context.cookies()
        
        # Get local storage (sometimes needed for auth tokens)
        local_storage = page.evaluate("() => JSON.stringify(localStorage)")

        # Save to file
        session_data = {
            "cookies": cookies,
            "local_storage": json.loads(local_storage),
            "user_agent": page.evaluate("navigator.userAgent")
        }
        
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
            
        print(f"Session saved to {session_file}")
        browser.close()

if __name__ == "__main__":
    run()
