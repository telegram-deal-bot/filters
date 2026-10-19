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
    return "Advanced Verified Product Multi-Stage Scraper is Active!"

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
        print(f"Telegram sending error: {e}")

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

def human_delay(min_sec=3.0, max_sec=6.0):
    """কার্সার মুভমেন্ট থিওরি: মানুষের স্ক্রলিং ও রিডিং স্পিড নকল করার বিলম্ব"""
    time.sleep(random.uniform(min_sec, max_sec))

def extract_features_from_text(text):
    """প্রোডাক্ট পেজের ভেতরের আসল বড় ডেসক্রিপশন এবং বুলেট থেকে ফিচার খোঁজার লজিক"""
    t_low = text.lower()
    return {
        'has_enc': any(x in t_low for x in ['enc', 'environmental noise', 'clear call', 'noise reduction']),
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
    """১০০% ডাইরেক্ট প্রোডাক্ট পেজের ভেতরে ঢুকে ডেসক্রিপশন স্ক্র্যাপ করার মেথড"""
    url = f"https://amazon.in{asin}"
    try:
        human_delay(3.5, 6.5) # মানুষের মতো র্যান্ডম পেজ রিডিং ডিলে
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # বুলেট পয়েন্ট এবং প্রোডাক্ট বিবরণী এক জায়গায় করা
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
    return 99 # কোনো সমস্যা হলে বড় নাম্বার দেওয়া যাতে সেটি সেরা প্রোডাক্টের রেস থেকে বাদ পড়ে

def fetch_and_select_ultimate_deal(category, budget_range):
    # ইউআরএল ফিক্সিং: সম্পূর্ণ আলাদা প্যারামিটার স্ট্রাকচার তৈরি করা হলো যাতে .intws টাইপো হওয়ার কোনো সুযোগ না থাকে
    clean_category = str(category).strip().replace(' ', '+')
    target_search_url = "https://www.amazon.in/s"

    
    # ডোমেন এবং কুয়েরিকে আলাদা প্যারামিটার (params) হিসেবে পাঠানো হচ্ছে যাতে ব্যাকএন্ডে ইউআরএল সঠিকভাবে তৈরি হয়
    search_params = {
        'k': clean_category
    }
    
    if isinstance(budget_range, tuple):
        min_p, max_p = budget_range
        search_params['rh'] = f"p_36:{min_p}00-{max_p}00"

    print(f"\n[Crawl Start] Requesting: {target_search_url} with params: {search_params}")
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
}

    
    try:
        human_delay(2.5, 5.0)
        # params ডিকশনারি ব্যবহারের কারণে ডোমেন নেম সম্পূর্ণ সুরক্ষিত থাকবে
        response = requests.get(target_search_url, params=search_params, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"[Warning] Amazon main page search returned status: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('div[data-component-type="s-search-result"]')
        
        valid_items_pool = []
        
        # ধাপ ১: কঠোর প্রাইস এবং অ্যাসিন আইডি ফিল্টারিং (বাইরে থেকে দাম না মিললে প্রোডাক্টটি স্কিপ করা হবে)
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
                
                if isinstance(budget_range, tuple):
                    min_b, max_b = budget_range
                    if not (min_b <= price <= max_b):
                        continue # বাজেট রেঞ্জ ফিল্টার আউট
                        
                valid_items_pool.append({'asin': asin, 'name': name, 'price': price})
                
        if not valid_items_pool:
            print(f"[Info] No items matched the initial price requirements outside.")
            return None
            
        # ধাপ ২: ৫টি করে প্রোডাক্টের ব্যাচ সাজানো এবং প্রতিটি প্রোডাক্ট পেজ আলাদা করে ডিপ ভিজিট করা
        ultimate_round_contenders = []
        chunk_size = 5
        batches = [valid_items_pool[i:i + chunk_size] for i in range(0, len(valid_items_pool), chunk_size)][:5]
        
        for batch_idx, batch in enumerate(batches, 1):
            print(f" -> Checking Batch {batch_idx}/5 (Size: {len(batch)} items) with Human Emulation Theory...")
            batch_evaluated = []
            
            for prod in batch:
                # সুনির্দিষ্ট প্রোডাক্টের ভেতরে ঢোকা এবং বিবরণী বিশ্লেষণ করা
                issues_count = deep_visit_product(prod['asin'], category, prod['price'], headers)
                prod['issues_count'] = issues_count
                batch_evaluated.append(prod)
                
            if batch_evaluated:
                # এই নির্দিষ্ট ৫টির ব্যাচের মধ্যে সবথেকে কম ইস্যু থাকা বেস্ট প্রোডাক্টটি বেছে নেওয়া
                best_in_batch = sorted(batch_evaluated, key=lambda x: x['issues_count'])[0]
                ultimate_round_contenders.append(best_in_batch)
                
        # ধাপ ৩: চূড়ান্ত উইনার সিলেকশন (৫টি ব্যাচের ৫টি সেরা প্রোডাক্টের মধ্যে অন্তিম তুলনা)
        if ultimate_round_contenders:
            final_winner = sorted(ultimate_round_contenders, key=lambda x: x['issues_count'])[0]
            final_winner['link'] = f"https://amazon.in{final_winner['asin']}?tag={AFFILIATE_TAG}"
            return final_winner
            
    except Exception as e:
        print(f"Critical execution error inside main script: {e}")
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
                            f"🎯 *ম্যাচ কোয়ালিটি:* ৫টি ব্যাচ গভীরভাবে স্ক্যান করে ফিল্টারের সাথে সর্বোচ্চ মিল পাওয়া গেছে।\n\n"
                            f"🛒 *সরাসরি কিনতে নিচের লিংকে ক্লিক করুন (Buy Now পেজ):* \n"
                            f"🔗 [এখানে ক্লিক করে অর্ডার করুন]({winner_deal['link']})"
                        )
                        send_telegram_message(message)
                        print(f"[Success] Ultimate verified direct deal posted for {cat} to Telegram!")
                    else:
                        print(f"[Skip] No optimal verified product found for {cat} in range {current_range} after deep analysis.")
                        
                    print("Sleeping for 30 minutes before next category crawl...")
                    time.sleep(1800)
                except Exception as e:
                    print(f"Loop runtime error: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_main_loop()
    
