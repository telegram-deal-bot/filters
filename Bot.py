import os
import time
import random
import requests
from flask import Flask
from threading import Thread
from filters import DealCuratorMaster

app = Flask(__name__)

@app.route('/')
def home():
    return "Multi-API Deal Bot with Smart Progressive Price-Range Round-Robin is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "technicalbot2-21")

EASYPARSER_API_KEY = os.environ.get("EASYPARSER_API_KEY")
GEEKFLARE_API_KEY = os.environ.get("GEEKFLARE_API_KEY")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN")

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Error] Telegram Token or Chat ID missing!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram sending error: {e}")

# আপনার নির্ধারিত মাস্টার সিকোয়েন্স ও প্রাইস স্লট
CATEGORY_BUDGET_SLOTS = [
    ('sunglass', (500, 1000)),
    ('watch', (500, 1000)),
    ('smartwatch', (1000, 2000)),
    ('powerbank', (500, 1000)),
    ('wallet', (500, 1500)),
    ('backpack', (500, 1500)),
    ('perfume', (500, 1500)),
    ('grooming', (100, 500)),
    ('kitchenware', (500, 1500)),
    ('induction', (1000, 2000)),
    ('kettle', (600, 1200)),
    ('scale', (300, 600)),
    ('dispenser', (200, 400)),
    ('ringlight', (100, 500)),
    ('striplight', (300, 700)),
    ('tripod', (800, 3000)),
    ('mouse', (0, 500)),
    ('keyboard', (1500, 2500)),

    ('tws', (500, 700)),
    ('speaker', (500, 700)),
    ('headphone', (1000, 1500)),
    ('sunglass', (1000, 1500)),
    ('watch', (1000, 1500)),
    ('smartwatch', (2000, 3000)),
    ('powerbank', (1000, 2000)),
    ('wallet', (1500, 3000)),
    ('backpack', (1500, 3000)),
    ('perfume', (1500, 3000)),
    ('grooming', (500, 1000)),
    ('kitchenware', (1500, 3000)),
    ('induction', (2000, 3500)),
    ('kettle', (1200, 2500)),
    ('scale', (600, 1000)),
    ('dispenser', (400, 800)),
    ('ringlight', (500, 1000)),
    ('striplight', (700, 1500)),
    ('tripod', (700, 2500)),
    ('mouse', (500, 1000)),
    ('keyboard', (2500, 4500)),

    ('tws', (700, 800)),
    ('speaker', (700, 1000)),
    ('headphone', (1500, 2000)),
    ('sunglass', (1500, 2500)),
    ('watch', (1500, 3000)),
    ('smartwatch', (3000, 4000)),
    ('powerbank', (2000, 3000)),
    ('wallet', (3000, 5000)),
    ('backpack', (3000, 5000)),
    ('perfume', (3000, 5000)),
    ('grooming', (1000, 1500)),
    ('kitchenware', (3000, 5000)),
    ('induction', (3500, 6000)),
    ('kettle', (2500, 4000)),
    ('scale', (1000, 1500)),
    ('dispenser', (800, 1200)),
    ('ringlight', (1000, 2000)),
    ('striplight', (1500, 3000)),
    ('mouse', (1000, 2500)),
    ('keyboard', (4500, 8000)),

    ('tws', (800, 1000)),
    ('speaker', (1000, 1500)),
    ('headphone', (2000, 3000)),
    ('sunglass', (2500, 4000)),
    ('watch', (3000, 5000)),
    ('smartwatch', (4000, 5000)),
    ('powerbank', (3000, 5000)),
    ('grooming', (1500, 5000)),
    ('tws', (1000, 1500)),
    ('speaker', (1500, 2500)),
    ('headphone', (3000, 4000)),
    ('sunglass', (4000, 5000)),
    ('tws', (1500, 2000)),
    ('speaker', (2500, 5000)),
    ('headphone', (4000, 5000)),
    ('tws', (2000, 3000)),
    ('tws', (3000, 4000)),
    ('tws', (4000, 5000)]

curator = DealCuratorMaster()

def human_delay(min_sec=1.5, max_sec=3.0):
    time.sleep(random.uniform(min_sec, max_sec))

def make_api_request(url, operation_type="SEARCH"):
    # ১. প্রথমে SerpApi দিয়ে চেষ্টা করবে
    if SERPAPI_API_KEY:
        try:
            serp_url = f"https://serpapi.com/search.json?engine=amazon&q={url}&api_key={SERPAPI_API_KEY}"
            res = requests.get(serp_url, timeout=30)
            if res.status_code == 200:
                data = res.json()
                if "error" not in str(data).lower():
                    return data
        except Exception as e:
            print(f"[Fallback] SerpApi failed: {e}")

    # ২. SerpApi ফেইল করলে Geekflare-এ অটো শিফট হবে
    if GEEKFLARE_API_KEY:
        try:
            headers = {'x-api-key': GEEKFLARE_API_KEY}
            gf_url = f"https://api.geekflare.com/search?url={url}"
            res = requests.get(gf_url, headers=headers, timeout=30)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"[Fallback] Geekflare failed: {e}")

    # ৩. সবশেষে Easyparser ব্যাকআপ হিসেবে কাজ করবে
    if EASYPARSER_API_KEY:
        try:
            api_endpoint = "https://realtime.easyparser.com/v1/request"
            params = {"api_key": EASYPARSER_API_KEY, "platform": "AMZ", "operation": operation_type, "domain": ".in", "url": url}
            res = requests.get(api_endpoint, params=params, timeout=30)
            if res.status_code == 200:
                data = res.json()
                if "depleted" not in str(data).lower():
                    return data
        except Exception as e:
            print(f"[Fallback] Easyparser failed: {e}")

    return None

def deep_visit_product(asin, category, price):
    product_url = f"https://www.amazon.in/dp/{asin}"
    if EASYPARSER_API_KEY:
        try:
            api_endpoint = "https://realtime.easyparser.com/v1/request"
            params = {"api_key": EASYPARSER_API_KEY, "platform": "AMZ", "operation": "DETAIL", "domain": ".in", "url": product_url}
            human_delay(1.0, 2.0)
            res = requests.get(api_endpoint, params=params, timeout=30)
            if res.status_code == 200:
                data = res.json().get('result', {}).get('detail', {})
                desc = " ".join(data.get('feature_bullets', []))
                specs = {'has_uv400': 'uv400' in desc.lower(), 'is_polarized': 'polarized' in desc.lower(), 'has_warranty': 'warranty' in desc.lower()}
                _, issues = curator.evaluate_product(category, price, specs)
                return len(issues)
        except:
            pass
    return 0

def fetch_and_select_ultimate_deal(category, budget_range):
    clean_category = str(category).strip().replace(' ', '+')
    target_search_url = f"https://www.amazon.in/s?k={clean_category}"
    
    if isinstance(budget_range, tuple):
        min_p, max_p = budget_range
        target_search_url += f"&rh=p_36%3A{min_p}00-{max_p}00"

    print(f"\n[Crawl Start] Scanning for: {clean_category} in range {budget_range}")
    
    data = make_api_request(target_search_url, operation_type="SEARCH")
    if not data:
        print(f"[Warning] All APIs failed for {category}.")
        return None
        
    result_content = data.get('result', {}) or data.get('organic_results', {})
    items = result_content.get('search_results', []) or result_content.get('items', []) or data.get('shopping_results', [])
    
    valid_items_pool = []
    for item in items:
        asin = item.get('asin') or item.get('product_id', '')
        if not asin:
            continue
            
        name = item.get('title', '') or item.get('name', '')
        price_val = item.get('price', 0)
        
        if isinstance(price_val, dict):
            price_val = price_val.get('value', 0) or price_val.get('raw', 0)

        if isinstance(price_val, str):
            price_text = price_val.replace(',', '').replace('₹', '')
            digits = ''.join(filter(str.isdigit, price_text))
            price = int(digits) if digits else 0
        else:
            try:
                price = int(price_val) if price_val else 0
            except:
                price = 0
            
        if price > 0:
            if isinstance(budget_range, tuple):
                min_b, max_b = budget_range
                if not (min_b <= price <= max_b):
                    continue
            valid_items_pool.append({'asin': str(asin), 'name': name, 'price': price})
            
    if not valid_items_pool:
        print(f"[Info] No valid items found for {category} in range {budget_range}.")
        return None
        
    # ৫টি করে প্রোডাক্টের ব্যাচ তৈরি করে সেরাটি বেছে নেওয়া (Tournament-Style Curation)
    ultimate_round_contenders = []
    chunk_size = 5
    batches = [valid_items_pool[i:i + chunk_size] for i in range(0, len(valid_items_pool), chunk_size)][:2]
    
    for batch in batches:
        batch_evaluated = []
        for prod in batch:
            issues_count = deep_visit_product(prod['asin'], category, prod['price'])
            prod['issues_count'] = issues_count
            batch_evaluated.append(prod)
        if batch_evaluated:
            best_in_batch = sorted(batch_evaluated, key=lambda x: x['issues_count'])[0]
            ultimate_round_contenders.append(best_in_batch)
            
    if ultimate_round_contenders:
        final_winner = sorted(ultimate_round_contenders, key=lambda x: x['issues_count'])[0]
        final_winner['link'] = f"https://amazon.in/dp/{final_winner['asin']}?tag={AFFILIATE_TAG}"
        return final_winner
        
    return valid_items_pool[0] if valid_items_pool else None

def bot_main_loop():
    send_telegram_message("🚀 *Multi-API Progressive Deal Bot Started!* \n\nSequential scanning with automatic API fallback active.")
    
    slot_index = 0
    total_slots = len(CATEGORY_BUDGET_SLOTS)
    
    while True:
        cat, current_range = CATEGORY_BUDGET_SLOTS[slot_index]
        try:
            print(f"\n[Slot {slot_index + 1}/{total_slots}] Processing {cat} in range {current_range}...")
            
            winner_deal = fetch_and_select_ultimate_deal(cat, current_range)
            
            if winner_deal:
                message = (
                    f"🏆 *সেরার সেরা ফিল্টার্ড ডিল\!* 🏆\n\n"
                    f"📦 *প্রোডাক্ট:* {winner_deal['name'][:55]}...\n"
                    f"💰 *দাম:* ₹{winner_deal['price']}\n"
                    f"🎯 *ক্যাটাগরি:* {cat.upper()} ({current_range[0]}\-{current_range[1]})\n\n"
                    f"🛒 *সরাসরি কিনতে লিংকে ক্লিক করুন:* \n"
                    f"🔗 [এখানে ক্লিক করে অর্ডার করুন]({winner_deal['link']})"
                )
                send_telegram_message(message)
                print(f"[Success] Deal posted for {cat} in range {current_range}!")
            else:
                print(f"[Skip] No deal found for {cat} in range {current_range}.")
                
        except Exception as e:
            print(f"Loop runtime error: {e}")
            
        slot_index = (slot_index + 1) % total_slots
        print("Sleeping for 2 hours before the next slot...")
        time.sleep(7200)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_main_loop()
