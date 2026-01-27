from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import yaml
import time

def investigate():
    load_dotenv()
    
    with open('config/config.yaml', 'r') as f:
        conf = yaml.safe_load(f)
    print("Loaded config.")
    
    roi_conf = conf['roi_online']
    email = os.getenv('ROI_EMAIL')
    password = os.getenv('ROI_PASSWORD')
    
    if not email or not password:
        print("Error: Credentials not found in environment.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Navigating to {roi_conf['url']}...")
        page.goto(roi_conf['url'])
        
        print("Logging in...")
        try:
            page.fill(f"#{roi_conf['username_field_id']}", email)
            page.fill(f"#{roi_conf['password_field_id']}", password)
            page.click(f"#{roi_conf['login_button_id']}")
            page.wait_for_load_state('networkidle')
            print("Logged in.")
        except Exception as e:
            print(f"Login failed: {e}")
            return
        
        # Dump current URL
        print(f"Current URL: {page.url}")
        
        # Look for buttons related to week navigation
        buttons = page.query_selector_all('button, input[type="button"], input[type="submit"], a.btn, span.btn, div[role="button"]')
        print(f"Found potential interactive elements. Scanning for navigation cues...")
        
        for btn in buttons:
            try:
                txt = btn.inner_text()
                val = btn.get_attribute('value') or ''
                title = btn.get_attribute('title') or ''
                id_attr = btn.get_attribute('id') or ''
                
                # Check for keywords
                s = (txt + val + title + id_attr).lower()
                if any(k in s for k in ['next', 'prev', 'volgende', 'vorige', 'week', 'fwd', 'bwd', 'cal', 'date']):
                    print(f"Candidate: Text='{txt}', Value='{val}', ID='{id_attr}', Title='{title}'")
            except:
                pass

        # Also dump the page HTML to a file
        with open('page_dump.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print("Saved page_dump.html")
        
        browser.close()

if __name__ == "__main__":
    investigate()
