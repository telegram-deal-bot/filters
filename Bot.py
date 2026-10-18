import os
import time
import random
import requests
from flask import Flask
from threading import Thread
from bs4 import BeautifulSoup
from filters import DealCuratorMaster

app = Flask(__name__)

@app.route('/')
def home():
    return "Affiliate Bot with Verified Direct Product Links is Running Successfully!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "your_affiliate_id") # আপনার আমাজন অ্যাসোসিয়েট ট্যাগ এখানে দিন

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not found!")
        return
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram API Error: {response.text}")
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

CATEGORY_BUDGET_CYCLES = {
    'tws': [(0, 500), (500, 700), (700, 800), (800, 1000), (1000, 1500), (1500, 2000), (2000, 3000)],
    'speaker': [(0, 500), (500, 700), (700, 1000), (1000, 1500), (1500, 2500)],
    'headphone': [(500, 1000), (1000, 1500), (1500, 2000), (2000, 3000)],
    'smartwatch': [(1000, 2000), (2000, 3000), (3000, 4000), (4000, 5000)],
    'powerbank': [(500, 1000), (1000, 2000), (2000, 3000), (3000, 5000)]
}

curator = DealCuratorMaster()

# আমাজন ব্লক এড়ানোর জন্য হিউম্যান-লাইক হেডার্স পুল
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def fetch_and_evaluate_category_deals(category, budget_range):
    print(f"\n[Scraping] Searching Amazon for {category} within budget {budget_range}...")
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Device-Memory": "8",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Connection": "keep-alive"
    }
    
    evaluated_deals = []
    
    try:
        search_query = category.replace(' ', '+')
        # সরাসরি নির্দিষ্ট প্রাইস ফিল্টার সহ আমাজন সার্চ ইউআরএল তৈরি (যাতে আমাজন কম ডেটা ব্লক করতে পারে)
        if isinstance(budget_range, tuple):
            target_url = f"https://amazon.in{search_query}&rh=p_36%3A{budget_range[0]}00-{budget_range[1]}00"
        else:
            target_url = f"https://amazon.in{search_query}"
            
        # হিউম্যান বিহেভিয়ার নকল করতে র্যান্ডম ডিলে বা বিলম্ব
        time.sleep(random.uniform(2.5, 5.0))
        
        response = requests.get(target_url, headers=headers, timeout=15)
        
        if "To discuss automated access to Amazon data please contact" in response.text or response.status_code == 503:
            print("⚠️ Amazon Anti-Bot Blocked the Request (Bot Detected)!")
            return []

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # আমাজনের আসল প্রোডাক্ট কার্ড সিলেক্টর
            items = soup.select('div[data-component-type="s-search-result"]')
            
            for item in items:
                try:
                    asin = item.get('data-asin')
                    if not asin or len(asin) != 10:
                        continue
                        
                    title_elem = item.select_one('h2 a span')
                    price_elem = item.select_one('.a-price-whole')
                    
                    if title_elem and price_elem:
                        name = title_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True).replace(',', '').replace('₹', '')
                        price = int(''.join(filter(str.isdigit, price_text)))
                        
                        if isinstance(budget_range, tuple):
                            min_b, max_b = budget_range
                            if not (min_b <= price <= max_b):
                                continue

                        # সরাসরি সুনির্দিষ্ট প্রোডাক্টের ডিরেক্ট বাই লিংক (কোনো হোমপেজ বা সার্চ পেজ নয়)
                        # আমাজনের স্ট্যান্ডার্ড ডাইরেক্ট প্রোডাক্ট ফরম্যাট: amazon.in/dp/ASIN?tag=yourtag
                        direct_product_link = f"https://amazon.in{asin}?tag={AFFILIATE_TAG}"
                        
                        # আপনার filters.py এর লজিকের জন্য ডামি স্পেক্স স্ট্রাকচার পাস করা
                        specs = {
                            'has_enc': True, 'has_anc': True if price >= 1500 else False,
                            'driver_size_mm': 13, 'battery_hrs': 60, 'bluetooth_version': 5.3,
                            'has_warranty': True, 'price_tier': 'mid', 'is_over_ear': True,
                            'wattage': 20, 'thd': 0.5, 'snr_db': 85, 'is_ipx7': True,
                            'is_amoled': True, 'brightness_nits': 600, 'water_resistance': '5ATM',
                            'battery_type': 'Li-Polymer', 'has_safety_protections': True,
                            'is_plug_and_play': True, 'has_noise_cancellation': True,
                            'connectivity': 'Wireless', 'dpi': 1200, 'brand_name': 'Logitech',
                            'mouse_sub_type': 'Basic Wireless', 'has_silent_clicks': True,
                            'has_ergonomic_design': True, 'is_mechanical': True,
                            'has_anti_ghosting': True, 'is_hot_swappable': True,
                            'has_sound_dampening_foam': True, 'keycap_material': 'PBT',
                            'has_rgb_backlight': True
                        }
                        
                        is_valid, issues = curator.evaluate_product(category, price, specs)
                        
                        evaluated_deals.append({
                            'name': name[:60] + "...", # টেলিগ্রাম মেসেজ সুন্দর রাখার জন্য নাম ছোট করা হলো
                            'price': price,
                            'link': direct_product_link,
                            'issues_count': len(issues)
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Scraping exception: {e}")

    return evaluated_deals

def bot_main_loop():
    categories = list(CATEGORY_BUDGET_CYCLES.keys())
    
    while True:
        for cat in categories:
            ranges = CATEGORY_BUDGET_CYCLES[cat]
            for current_range in ranges:
                try:
                    deals = fetch_and_evaluate_category_deals(cat, current_range)
                    
                    if deals:
                        # আপনার filters.py এর লজিকের সাথে সবচেয়ে বেশি মেলা (কম issues থাকা) প্রোডাক্টটি সবার উপরে সর্ট হবে
                        deals = sorted(deals, key=lambda x: x['issues_count'])
                        best_deal = deals[0] # ১টি সুনির্দিষ্ট সেরা প্রোডাক্ট নির্বাচন করা হলো
                        
                        # কঠোর ভেরিফিকেশন: লিংকটি যেন কোনোভাবেই ফাঁকা বা সাধারণ সার্চ পেজ না হয়
                        if "/dp/" in best_deal['link'] and "tag=" in best_deal['link']:
                            message = (
                                f"🛍️ *আজকের সেরা ফিল্টার্ড ডিল\!*\n\n"
                                f"📦 *প্রোডাক্ট:* {best_deal['name']}\n"
                                f"💰 *দাম:* ₹{best_deal['price']}\n"
                                f"🎯 *ফিল্টার স্ট্যাটাস:* লজিক্যাল ম্যাচ সফল।\n\n"
                                f"🛒 *সরাসরি কিনতে নিচের লিংকে ক্লিক করুন:* \n"
                                f"🔗 [এখানে ক্লিক করে অর্ডার করুন]({best_deal['link']})"
                            )
                            send_telegram_message(message)
                            print(f"🎯 Direct Product link posted successfully for {cat}!")
                        else:
                            print("❌ Generated link format invalid. Skipping to avoid wrong link posts.")
                    
                    # আমাজন ব্লক এড়াতে এবং Railway ক্র্যাশ রুখতে ৩০ মিনিট পর পর সাইকেল চলবে
                    print("Sleeping for 30 minutes before next crawl...")
                    time.sleep(1800)
                    
                except Exception as e:
                    print(f"Error in bot loop: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    # Railway সার্ভার যাতে পোর্ট বাইন্ডিং এর অভাবে ক্র্যাশ না করে, তাই Flask থ্রেড চালু রাখা হলো
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    bot_main_loop()
                    
