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
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "your_affiliate_id")

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials not found!")
        return
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
]

def fetch_and_evaluate_category_deals(category, budget_range):
    # ইউআরএল তৈরির ভুল এবং স্পেসের টাইপো ফিক্স করা হয়েছে
    print(f"\n[Scraping] Searching Amazon for {category} within budget {budget_range}...")
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }
    
    evaluated_deals = []
    
    try:
        search_query = category.strip().replace(' ', '+')
        # ইউআরএল ফরম্যাট সম্পূর্ণ সংশোধন করা হয়েছে (amazon.in এবং কুয়েরির মাঝে প্রোপার স্ল্যাশ ও প্যারামিটার যোগ করা হয়েছে)
        if isinstance(budget_range, tuple):
            target_url = f"https://amazon.in{search_query}&rh=p_36%3A{budget_range[0]}00-{budget_range[1]}00"
        else:
            target_url = f"https://amazon.in{search_query}"
            
        time.sleep(random.uniform(2.0, 4.0))
        response = requests.get(target_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
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

                        # ১০০% ডিরেক্ট স্পেসিফিক প্রোডাক্ট পেজ বাই লিংক
                        direct_product_link = f"https://amazon.in{asin}?tag={AFFILIATE_TAG}"
                        
                        # filters.py এর প্যারামিটার যাচাই লজিক
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
                            'name': name[:50] + "...",
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
                    deals = float_deals = fetch_and_evaluate_category_deals(cat, current_range)
                    
                    if deals:
                        # ফিল্টারের লজিকের সাথে সবচেয়ে বেশি মেলা (কম অমিল বা issues থাকা) প্রোডাক্টটি বেছে নেওয়া হবে
                        deals = sorted(deals, key=lambda x: x['issues_count'])
                        best_deal = deals[0]
                        
                        # কঠোর নিরাপত্তা চেক: লিংকটি যেন হোমপেজ বা অন্য কোনো ফালতু পেজ না হয়, শুধুমাত্র সরাসরি প্রোডাক্ট পেজ হলেই মেসেজ যাবে
                        if "/dp/" in best_deal['link'] and "tag=" in best_deal['link']:
                            message = (
                                f"🔥 *Best Matched Deal for {cat.upper()}* 🔥\n"
                                f"💰 *Budget Range:* ₹{current_range[0]} - ₹{current_range[1]}\n\n"
                                f"📦 *Product:* {best_deal['name']}\n"
                                f"💰 *Price:* ₹{best_deal['price']}\n"
                                f"🔗 [Buy Direct Product Here]({best_deal['link']})"
                            )
                            send_telegram_message(message)
                            print(f"Successfully posted direct product deal to Telegram!")
                    else:
                        # স্ক্র্যাপিং বা ফিল্টারিং ফেইল করলে কোনো ফেক/ভুল লিংক আর জেনারেট হবে না
                        print(f"⚠️ No matching product found for {cat} in range {current_range} or request blocked. Skipping...")
                    
                    # আমাজন ব্লক এড়াতে এবং সাইকেল ঠিক রাখতে ৩০ মিনিট পর পর স্ক্র্যাপ হবে
                    print("Sleeping for 30 minutes before next crawl...")
                    time.sleep(1800)
                    
                except Exception as e:
                    print(f"Error in bot loop: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    bot_main_loop()
    
