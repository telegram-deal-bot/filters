import os
import time
import requests
from flask import Flask
from threading import Thread
from filters import DealCuratorMaster

# Selenium ইম্পোর্ট (বট ডিটেকশন এড়াতে এবং রিয়েল ব্রাউজার সেশন ব্যবহার করতে)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)

@app.route('/')
def home():
    return "Affiliate Bot with Selenium & Modular Filters is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not found!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

# ক্যাটাগরি এবং বাজেট রেঞ্জ সাইকেল
CATEGORY_BUDGET_CYCLES = {
    'tws': [(0, 500), (500, 700), (700, 800), (800, 1000), (1000, 1500), (1500, 2000), (2000, 3000)],
    'speaker': [(0, 500), (500, 700), (700, 1000), (1000, 1500), (1500, 2500)],
    'headphone': [(500, 1000), (1000, 1500), (1500, 2000), (2000, 3000)],
    'smartwatch': [(1000, 2000), (2000, 3000), (3000, 4000), (4000, 5000)],
    'powerbank': [(500, 1000), (1000, 2000), (2000, 3000), (3000, 5000)],
    'keyboard': ['entry_pro', 'mid_enthusiast', 'flagship_custom'],
    'mouse': ['0-500', '500-1000', '1000-2500', '2500-5000']
}

curator = DealCuratorMaster()

def get_driver():
    """রিয়েল ব্রাউজার কনফিগারেশন যা বট ডিটেকশন এড়াতে সাহায্য করবে"""
    options = Options()
    options.add_argument("--headless") # রেলওয়ে সার্ভারে চালানোর জন্য হেডলেস মোড
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def fetch_products_with_selenium(category, budget_range):
    """
    আইডিয়া ২ অনুযায়ী: Selenium ব্রাউজার ব্যবহার করে অ্যামাজন/ফ্লিপকার্ট সার্চ পেজ ভিজিট করবে 
    এবং আপনার লগইন করা সেশন বা কুকিজের মাধ্যমে রিয়েল প্রোডাক্ট ডেটা তুলবে।
    """
    print(f"Fetching products for Category: {category} in Budget/Tier: {budget_range} using Selenium...")
    
    driver = get_driver()
    products_list = []
    
    try:
            # প্রথমে অ্যামাজনের হোমপেজে যাবে যাতে বট ডিটেক্ট করে ব্লক না করে
    driver.get("https://www.amazon.in")
    time.sleep(3)
    
    # এরপর আসল সার্চ পেজে যাবে
    search_query = category.replace(' ', '+')
    target_url = f"https://www.amazon.in/s?k={search_query}"
    
    driver.get(target_url)
    time.sleep(5)

        
        # এখানে পেজ থেকে প্রোডাক্টের নাম, প্রাইস, লিংক এবং স্পেক্স ফেচ করার লজিক থাকবে
        # ডেমো হিসেবে ফরম্যাট স্ট্রাকচার নিচে দেওয়া হলো:
        products_list = [
            {
                'name': f'Sample Real Amazon {category.upper()} Pro',
                'price': budget_range[1] if isinstance(budget_range, tuple) else 1499,
                'link': target_url,
                'specs': {
                    'has_enc': True,
                    'driver_size_mm': 13,
                    'battery_hrs': 60,
                    'bluetooth_version': 5.3,
                    'has_warranty': True,
                    'price_tier': budget_range if isinstance(budget_range, str) else 'mid'
                }
            }
        ]
        
    except Exception as e:
        print(f"Selenium scraping error: {e}")
    finally:
        driver.quit()
        
    return products_list

def evaluate_and_select_best_product(category, products):
    """সবচেয়ে কম ত্রুটি বা বেশি স্পেক্সযুক্ত সেরা প্রোডাক্ট বেছে নেওয়ার স্কোরিং লজিক"""
    best_product = None
    min_issues_count = 9999

    for prod in products:
        is_valid, issues = curator.evaluate_product(category, prod['price'], prod['specs'])
        issue_count = len(issues)
        
        if issue_count < min_issues_count:
            min_issues_count = issue_count
            best_product = prod

    return best_product, min_issues_count

def bot_main_loop():
    categories = list(CATEGORY_BUDGET_CYCLES.keys())
    
    while True:
        for cat in categories:
            ranges = CATEGORY_BUDGET_CYCLES[cat]
            for current_range in ranges:
                try:
                    print(f"\n--- Cycling: Category [{cat}], Range/Tier [{current_range}] ---")
                    
                    raw_products = fetch_products_with_selenium(cat, current_range)
                    
                    if raw_products:
                        best_deal, issues_found = evaluate_and_select_best_product(cat, raw_products)
                        
                        if best_deal:
                            affiliate_link = f"{best_deal['link']}&tag=your_affiliate_id"
                            
                            message = (
                                f"🔥 *Verified Deal Found!* 🔥\n\n"
                                f"📦 *Product:* {best_deal['name']}\n"
                                f"💰 *Price:* ₹{best_deal['price']}\n"
                                f"🎯 *Status:* Best Spec-to-Price Match\n\n"
                                f"🔗 [Check Deal & Buy Here]({affiliate_link})"
                            )
                            
                            send_telegram_message(message)
                            print(f"Posted to Telegram: {best_deal['name']}")
                    
                    time.sleep(1800) # প্রতি সাইকেলের মাঝে ৩০ মিনিটের বিরতি
                    
                except Exception as e:
                    print(f"Error in bot loop for {cat}: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    bot_main_loop()
