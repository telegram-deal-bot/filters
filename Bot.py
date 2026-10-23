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

# Railway Variables থেকে অটোমেটিক টোকেন ও আইডি রিড করা
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "your_affiliate_id")

EASYPARSER_API_KEY = os.environ.get("EASYPARSER_API_KEY")
GEEKFLARE_API_KEY = os.environ.get("GEEKFLARE_API_KEY")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")
APIFY_API_TOKEN = os.environ.get("APIFY_API_TOKEN")

def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Error] Telegram Token or Chat ID missing in Environment Variables!")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"[Telegram Error] Failed to send message: {response.text}")
    except Exception as e:
        print(f"Telegram sending error: {e}")

# আপনার সম্পূর্ণ ক্যাটাগরি ও প্রতিটি প্রাইস রেঞ্জের তালিকা
CATEGORY_BUDGET_SLOTS = {
    'speaker': [(0, 500), (500, 700), (700, 1000), (1000, 1500), (1500, 2500), (2500, 5000)],
    'headphone': [(500, 1000), (1000, 1500), (1500, 2000), (2000, 3000), (3000, 4000), (4000, 5000)],
    'tws': [(0, 500), (500, 700), (700, 800), (800, 1000), (1000, 1500), (1500, 2000), (2000, 3000), (3000, 4000), (4000, 5000)],
    'sunglass': [(500, 1000), (1000, 1500), (1500, 2500), (2500, 4000), (4000, 5000)],
    'watch': [(500, 1000), (1000, 1500), (1500, 3000), (3000, 5000)],
    'smartwatch': [(1000, 2000), (2000, 3000), (3000, 4000), (4000, 5000)],
    'powerbank': [(500, 1000), (1000, 2000), (2000, 3000), (3000, 5000)],
    'wallet': [(500, 1500), (1500, 3000), (3000, 5000)],
    'backpack': [(500, 1500), (1500, 3000), (3000, 5000)],
    'perfume': [(500, 1500), (1500, 3000), (3000, 5000)],
    'grooming': [(100, 500), (500, 1000), (1000, 1500), (1500, 5000)],
    'kitchenware': [(500, 1500), (1500, 3000), (3000, 5000)],
    'induction': [(1000, 2000), (2000, 3500), (3500, 6000)],
    'kettle': [(600, 1200), (1200, 2500), (2500, 4000)],
    'scale': [(300, 600), (600, 1000), (1000, 1500)],
    'dispenser': [(200, 400), (400, 800), (800, 1200)],
    'ringlight': [(100, 500), (500, 1000), (1000, 2000), (2000, 5000)],
    'striplight': [(300, 700), (700, 1500), (1500, 3000)],
    'tripod': [(800, 3000), (700, 2500)],
    'mouse': [(0, 500), (500, 1000), (1000, 2500), (2500, 5000)],
    'keyboard': [(1500, 2500), (2500, 4500), (4500, 8000)]
}

curator = DealCuratorMaster()

def human_delay(min_sec=2.0, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))

def extract_features_from_text(text):
    t_low = text.lower()
    return {
        'has_uv400': 'uv400' in t_low or 'uv 400' in t_low,
        'is_polarized': 'polarized' in t_low,
        'has_warranty': any(x in t_low for x in ['warranty', '1 year', '12 months']),
        'is_amoled': 'amoled' in t_low or 'oled' in t_low,
        'has_rgb_backlight': 'rgb' in t_low or 'backlit' in t_low
    }

def make_api_request(url, operation_type="SEARCH"):
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

    if SERPAPI_API_KEY:
        try:
            serp_url = f"https://serpapi.com/search.json?engine=amazon&q={url}&api_key={SERPAPI_API_KEY}"
            res = requests.get(serp_url, timeout=30)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            print(f"[Fallback] SerpApi failed: {e}")

    return None

def deep_visit_product(asin, category, price):
    product_url = f"https://www.amazon.in/dp/{asin}"
    api_endpoint = "https://realtime.easyparser.com/v1/request"
    params = {"api_key": EASYPARSER_API_KEY, "platform": "AMZ", "operation": "DETAIL", "domain": ".in", "url": product_url}
    
    try:
        human_delay(1.5, 3.0)
        res = requests.get(api_endpoint, params=params, timeout=30)
        if res.status_code == 200:
            data = res.json()
            result_data = data.get('result', {})
            detail_info = result_data.get('detail', {})
            features_list = detail_info.get('feature_bullets', [])
            description_text = " ".join(features_list)
            
            specs = extract_features_from_text(description_text)
            _, issues = curator.evaluate_product(category, price, specs)
            return len(issues)
    except Exception as e:
        print(f"API Detail Error for ASIN {asin}: {e}")
    return 99

def fetch_and_select_ultimate_deal(category, budget_range):
    clean_category = str(category).strip().replace(' ', '+')
    target_search_url = f"https://www.amazon.in/s?k={clean_category}"
    
    if isinstance(budget_range, tuple):
        min_p, max_p = budget_range
        target_search_url += f"&rh=p_36%3A{min_p}00-{max_p}00"

    print(f"\n[Crawl Start] Requesting for: {clean_category} in range {budget_range}")
    
    data = make_api_request(target_search_url, operation_type="SEARCH")
    if not data:
        print(f"[Warning] All APIs failed or credits depleted for {category}.")
        return None
        
    result_content = data.get('result', {})
    items = result_content.get('search_results', []) or result_content.get('items', [])
    
    valid_items_pool = []
    for item in items:
        asin = item.get('asin')
        if not asin or len(asin) != 10:
            continue
            
        name = item.get('title', '')
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
            valid_items_pool.append({'asin': asin, 'name': name, 'price': price})
            
    if not valid_items_pool:
        print(f"[Info] No valid price items found for {category} in range {budget_range}.")
        return None
        
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
        
    return None

def bot_main_loop():
    send_telegram_message("🚀 *Telegram Deal Bot Started!* \n\nScanning sequentially across categories by price slots.")
    
    categories = list(CATEGORY_BUDGET_SLOTS.keys())
    
    # বর্তমান স্লট ইনডেক্স নির্ধারণ (যেহেতু স্পিকার, হেডফোন, টিডব্লিউএস এর প্রথম রেঞ্জ শেষ, 
    # তাই সানগ্লাস থেকে শুরু করতে চাইলে সানগ্লাসের ইনডেক্স থেকে শুরু হবে)
    slot_index = 0 
    
    while True:
        for cat in categories:
            slots = CATEGORY_BUDGET_SLOTS[cat]
            # যদি এই ক্যাটাগরির নির্দিষ্ট স্লটটি বিদ্যমান থাকে তবেই রান করবে
            if slot_index < len(slots):
                current_range = slots[slot_index]
                try:
                    print(f"Sleeping for 2 hours before scanning {cat} in range {current_range}...")
                    time.sleep(7200)  # প্রতি ২ ঘণ্টা পর পর রান হবে
                    
                    winner_deal = fetch_and_select_ultimate_deal(cat, current_range)
                    
                    if winner_deal and winner_deal['issues_count'] < 99:
                        message = (
                            f"🏆 *সেরার সেরা ফিল্টার্ড ডিল\!* 🏆\n\n"
                            f"📦 *প্রোডাক্ট:* {winner_deal['name'][:55]}...\n"
                            f"💰 *দাম:* ₹{winner_deal['price']}\n"
                            f"🎯 *ম্যাচ কোয়ালিটি:* এপিআই সিকিউরড ফিল্টারিং সম্পন্ন।\n\n"
                            f"🛒 *সরাসরি কিনতে লিংকে ক্লিক করুন:* \n"
                            f"🔗 [এখানে ক্লিক করে অর্ডার করুন]({winner_deal['link']})"
                        )
                        send_telegram_message(message)
                        print(f"[Success] Verified deal posted for {cat}!")
                    else:
                        print(f"[Skip] No optimal verified product found for {cat} in range {current_range}.")
                        
                except Exception as e:
                    print(f"Loop runtime error: {e}")
                    time.sleep(60)
            
        # সব ক্যাটাগরি ঘুরে আসার পর স্লট ইনডেক্স ১ বাড়াবে (যাতে পরবর্তী প্রাইস রেঞ্জে শিফট হয়)
        slot_index += 1
        # সর্বোচ্চ স্লট পার হয়ে গেলে আবার প্রথম স্লট (0) থেকে শুরু হবে
        if slot_index >= 10:  
            slot_index = 0

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_main_loop()
