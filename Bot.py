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
    return "Advanced Multi-Stage Product Deep Scraper is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "your_affiliate_id")

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

CATEGORY_BUDGET_CYCLES = {
    'tws': [(0, 500), (500, 700), (700, 800), (800, 1000), (1000, 1500)],
    'speaker': [(0, 500), (500, 700), (700, 1000), (1000, 1500)],
    'smartwatch': [(1000, 2000), (2000, 3000), (3000, 4000)]
}

curator = DealCuratorMaster()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
]

def human_delay(min_sec=2.0, max_sec=5.0):
    """কার্সার মুভমেন্ট থিওরি: মানুষের মতো করে ধীরে ধীরে পেজ স্ক্রল বা পড়ার বিরতি নকল করা"""
    time.sleep(random.uniform(min_sec, max_sec))

def extract_features_from_text(text):
    """প্রোডাক্টের ভেতরের ডেসক্রিপশন এবং বুলেট পয়েন্ট থেকে স্পেক্স খুঁজে বের করার লজিক"""
    t_low = text.lower()
    return {
        'has_enc': any(x in t_low for x in ['enc', 'environmental noise', 'clear call']),
        'has_anc': any(x in t_low for x in ['anc', 'active noise', 'hybrid anc']),
        'driver_size_mm': 13 if '13mm' in t_low or '13 mm' in t_low else 10,
        'battery_hrs': 60 if '60h' in t_low or '60 hours' in t_low else 40,
        'bluetooth_version': 5.4 if '5.4' in t_low else 5.3,
        'has_warranty': any(x in t_low for x in ['warranty', '1 year', '12 months']),
        'price_tier': 'mid',
        'is_over_ear': 'over' in t_low or 'cushion' in t_low,
        'is_amoled': 'amoled' in t_low or 'oled' in t_low,
        'has_rgb_backlight': 'rgb' in t_low or 'backlit' in t_low
    }

def deep_visit_product(asin, category, price, headers):
    """সুনির্দিষ্ট প্রোডাক্ট পেজের ভেতরে ঢুকে ডেসক্রিপশন এবং বুলেট পয়েন্ট স্ক্র্যাপ করার মেথড"""
    url = f"https://amazon.in{asin}"
    try:
        human_delay(3.0, 6.0) # মানুষের মতো রিডিং ডিলে
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # প্রোডাক্টের ভেতরের ডেসক্রিপশন এবং ফিচারের অংশগুলো রিড করা
            bullet_points = soup.select("#feature-bullets ul li span")
            description_text = " ".join([bp.get_text(strip=True) for bp in bullet_points])
            
            product_desc = soup.select_one("#productDescription")
            if product_desc:
                description_text += " " + product_desc.get_text(strip=True)
                
            specs = extract_features_from_text(description_text)
            _, issues = curator.evaluate_product(category, price, specs)
            return len(issues)
    except Exception:
        pass
    return 99 # ফেইল করলে হাই ইস্যু কাউন্ট দেওয়া হবে যাতে এটি ফিল্টারে বাদ পড়ে

def fetch_and_select_ultimate_deal(category, budget_range):
    print(f"\n[Crawl Start] Category: {category}, Range: {budget_range}")
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive"
    }
    
    try:
        search_query = category.strip().replace(' ', '+')
        url = f"https://amazon.in{search_query}"
        human_delay(2.0, 4.0)
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('div[data-component-type="s-search-result"]')
        
        valid_items_pool = []
        
        # ধাপ ১: আগে বাইরে থেকে শুধু প্রাইস মিললে তবেই পুলে নেওয়া হবে (বাজেটের বাইরের প্রোডাক্ট ফিল্টার আউট)
        for item in items:
            asin = item.get('data-asin')
            if not asin or len(asin) != 10:
                continue
                
            title_elem = item.select_one('h2 a span')
            price_elem = item.select_one('.a-price-whole')
            
            if title_elem and price_elem:
                name = title_elem.get_text(strip=True)
                price_text = price_elem.get_text(strip=True).replace(',', '').replace('₹', '')
                price = int(''.join(filter(str.isdigit, price_text)))
                
                # কঠোর প্রাইস ফিল্টার চেক
                if isinstance(budget_range, tuple):
                    min_b, max_b = budget_range
                    if not (min_b <= price <= max_b):
                        continue # বাজেট না মিললে প্রোডাক্টটি ভিজিটই করা হবে না
                        
                valid_items_pool.append({'asin': asin, 'name': name, 'price': price})
                
        if not valid_items_pool:
            return None
            
        # ধাপ ২: ৫টি করে প্রোডাক্ট ৫টি আলাদা আলাদা ব্যাচে ভাগ করা (আপনার ৫x৫ থিওরি)
        ultimate_round_contenders = []
        chunk_size = 5
        batches = [valid_items_pool[i:i + chunk_size] for i in range(0, len(valid_items_pool), chunk_size)][:5]
        
        for batch_idx, batch in enumerate(batches, 1):
            print(f"-> Processing Batch {batch_idx}/5 (Size: {len(batch)} items)")
            batch_evaluated = []
            
            for prod in batch:
                # ডাইরেক্ট প্রোডাক্ট পেজের ডেসক্রিপশন পড়তে ভেতরে ঢোকা
                issues_count = deep_visit_product(prod['asin'], category, prod['price'], headers)
                prod['issues_count'] = issues_count
                batch_evaluated.append(prod)
                
            if batch_evaluated:
                # এই ব্যাচের সবথেকে ভালো প্রোডাক্টটি বেছে নেওয়া (সবচেয়ে কম issues_count)
                best_in_batch = sorted(batch_evaluated, key=lambda x: x['issues_count'])[0]
                ultimate_round_contenders.append(best_in_batch)
                
        # ধাপ ৩: ৫টি ব্যাচের ৫টি সেরা প্রোডাক্টের মধ্যে ফাইনাল লড়াই (সেরার সেরা নির্বাচন)
        if ultimate_round_contenders:
            final_winner = sorted(ultimate_round_contenders, key=lambda x: x['issues_count'])[0]
            
            # ১০০% ডাইরেক্ট সুনির্দিষ্ট প্রোডাক্ট বাই লিংক জেনারেশন
            final_winner['link'] = f"https://amazon.in{final_winner['asin']}?tag={AFFILIATE_TAG}"
            return final_winner
            
    except Exception as e:
        print(f"Critical workflow error: {e}")
    return None

def bot_main_loop():
    categories = list(CATEGORY_BUDGET_CYCLES.keys())
    while True:
        for cat in categories:
            ranges = CATEGORY_BUDGET_CYCLES[cat]
            for current_range in ranges:
                try:
                    winner_deal = fetch_and_select_ultimate_deal(cat, current_range)
                    
                    if winner_deal and winner_deal['issues_count'] < 99:
                        message = (
                            f"🏆 *সেরার সেরা ফিল্টার্ড ডিল\!* 🏆\n\n"
                            f"📦 *প্রোডাক্ট:* {winner_deal['name'][:55]}...\n"
                            f"💰 *দাম:* ₹{winner_deal['price']}\n"
                            f"🎯 *ম্যাচ কোয়ালিটি:* ৫টি ব্যাচ যাচাই করে সর্বোচ্চ স্কোরপ্রাপ্ত।\n\n"
                            f"🛒 *সরাসরি কিনতে নিচের লিংকে ক্লিক করুন (Buy Now পেজ):* \n"
                            f"🔗 [এখানে ক্লিক করে অর্ডার করুন]({winner_deal['link']})"
                        )
                        send_telegram_message(message)
                        print(f"[Success] Ultimate verified direct deal posted for {cat}!")
                    else:
                        print(f"[Skip] No optimal verified product found for {cat} in range {current_range}.")
                        
                    print("Sleeping for 30 minutes before next category crawl...")
                    time.sleep(1800)
                except Exception as e:
                    print(f"Loop error: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_main_loop()
    
