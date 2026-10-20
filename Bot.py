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
    return "Advanced Verified Product Multi-Stage Scraper with Easyparser API is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Railway Variables থেকে অটোমেটিক টোকেন ও আইডি রিড করার ব্যবস্থা
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "your_affiliate_id")
EASYPARSER_API_KEY = os.environ.get("EASYPARSER_API_KEY")

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

CATEGORY_BUDGET_CYCLES = {
    'tws': [(0, 500), (500, 700), (700, 800), (800, 1000), (1000, 1500)],
    'speaker': [(0, 500), (500, 700), (700, 1000), (1000, 1500)],
    'smartwatch': [(1000, 2000), (2000, 3000), (3000, 4000)]
}

curator = DealCuratorMaster()

def human_delay(min_sec=2.0, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))

def extract_features_from_text(text):
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

def deep_visit_product(asin, category, price):
    product_url = f"https://www.amazon.in/dp/{asin}"
    api_endpoint = "https://realtime.easyparser.com/v1/request"
    
    params = {
        "api_key": EASYPARSER_API_KEY,
        "platform": "AMZ",
        "operation": "DETAIL",
        "domain": ".in",
        "url": product_url
    }
    
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

    print(f"\n[Crawl Start] Requesting via Easyparser API for: {clean_category}")
    
    api_endpoint = "https://realtime.easyparser.com/v1/request"
    params = {
        "api_key": EASYPARSER_API_KEY,
        "platform": "AMZ",
        "operation": "SEARCH",
        "domain": ".in",
        "url": target_search_url
    }
    
    try:
        human_delay(2.0, 4.0)
        response = requests.get(api_endpoint, params=params, timeout=35)
        
        if response.status_code != 200:
            print(f"[Warning] Easyparser API search returned status: {response.status_code}")
            return None
            
        data = response.json()
        result_content = data.get('result', {})
        items = result_content.get('search_results', []) or result_content.get('items', [])
        
        valid_items_pool = []
        for item in items:
            asin = item.get('asin')
            if not asin or len(asin) != 10:
                continue
                
            name = item.get('title', '')
            price_val = item.get('price', 0)
            
            # সেফটি চেক: প্রাইস যদি ডিকশনারি হয় তবে সেখান থেকে সঠিক ভ্যালু বের করে নেওয়া
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
            
    except Exception as e:
        print(f"Critical execution error with Easyparser API: {e}")
    return None

def bot_main_loop():
    send_telegram_message("🚀 *Telegram Deal Bot Successfully Started & Connected!* \n\nEasyparser API secured mode is active. Now scanning for best deals...")
    
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
                            f"🎯 *ম্যাচ কোয়ালিটি:* এপিআই সিকিউরড ফিল্টারিং সম্পন্ন।\n\n"
                            f"🛒 *সরাসরি কিনতে লিংকে ক্লিক করুন:* \n"
                            f"🔗 [এখানে ক্লিক করে অর্ডার করুন]({winner_deal['link']})"
                        )
                        send_telegram_message(message)
                        print(f"[Success] API-secured verified deal posted for {cat}!")
                    else:
                        print(f"[Skip] No optimal verified product found for {cat} in range {current_range}.")
                        
                    print("Sleeping for 60 minutes before next category crawl...")
                    time.sleep(3600)
                except Exception as e:
                    print(f"Loop runtime error: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_main_loop()
                                  
