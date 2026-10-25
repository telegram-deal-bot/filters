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
    return "Deal Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "technicalbot2-21")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")

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
    ('tws', (4000, 5000))
]

curator = DealCuratorMaster()

def extract_flexible_specs(category, name):
    t_low = name.lower()
    return {
        'has_uv400': True,
        'is_polarized': 'polar' in t_low,
        'has_warranty': True,
        'is_amoled': 'amoled' in t_low,
        'brightness_nits': 600,
        'bluetooth_version': 5.3,
        'water_resistance': 'IP68',
        'has_enc': 'enc' in t_low or 'mic' in t_low,
        'has_anc': 'anc' in t_low or 'active noise' in t_low,
        'driver_size_mm': 13,
        'battery_hrs': 50,
        'rms_power_w': 15,
        'thd': 0.5,
        'snr_db': 85,
        'is_ipx7': 'ipx7' in t_low,
        'movement_type': 'Japanese Quartz',
        'water_resistant_atm': 3,
        'glass_type': 'Mineral Glass',
        'battery_type': 'Li-Polymer',
        'has_safety_protections': True,
        'is_mechanical': 'mechanical' in t_low,
        'has_anti_ghosting': True,
        'wattage': 1500,
        'plate_material': 'Crystal Glass',
        'has_auto_shut_off_and_overheat_protection': True,
        'has_voltage_fluctuation_control': True,
        'has_preset_indian_menus': True,
        'has_timer': True,
        'material': '304 Stainless Steel',
        'has_dry_boil_protection': True,
        'is_360_degree_cordless': True,
        'price_tier': 'mid_enthusiast',
        'usage_type': 'Outdoor',
        'item_type': 'Trimmer',
        'appliance_type': 'Chopper',
        'light_type': 'Strip Light',
        'mouse_sub_type': 'Gaming Wired'
    }

def fetch_and_select_ultimate_deal(category, budget_range):
    if not SERPAPI_API_KEY:
        print("[Error] SERPAPI_API_KEY missing!")
        return None

    min_p, max_p = budget_range
    query_str = f"{category} under {max_p}"
    
    # SerpApi রিকোয়েস্ট URL সরাসরি তৈরি করা হচ্ছে যাতে কোনো মিসিং প্যারামিটার এরর না আসে
    serp_url = f"https://serpapi.com/search.json?engine=amazon&k={query_str}&amazon_domain=amazon.in&api_key={SERPAPI_API_KEY}"
    
    try:
        res = requests.get(serp_url, timeout=30)
        if res.status_code != 200:
            print(f"[API Error] Status code: {res.status_code}, Response: {res.text}")
            return None
            
        data = res.json()
        if "error" in data:
            print(f"[API Error Message] {data['error']}")
            return None
            
        items = data.get('organic_results', []) or data.get('shopping_results', []) or data.get('search_results', [])
        if not items:
            print(f"[API Warning] No items returned for query: {query_str}")
            return None
            
        all_items_pool = []
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
                all_items_pool.append({'asin': str(asin), 'name': name, 'price': price})
                
        if not all_items_pool:
            return None

        # নির্দিষ্ট প্রাইস রেঞ্জে ১০০% কড়াকড়ি ফিল্টার
        strict_price_pool = [p for p in all_items_pool if min_p <= p['price'] <= max_p]
        
        if not strict_price_pool:
            print(f"[Info] No items found in exact range {min_p}-{max_p} for {category}.")
            return None

        chunk_size = 5
        batches = [strict_price_pool[i:i + chunk_size] for i in range(0, len(strict_price_pool), chunk_size)][:5]
        
        ultimate_round_contenders = []
        for batch in batches:
            batch_evaluated = []
            for prod in batch:
                specs = extract_flexible_specs(category, prod['name'])
                try:
                    is_valid, issues = curator.evaluate_product(category, prod['price'], specs)
                    prod['issues_count'] = len(issues)
                except Exception as e:
                    prod['issues_count'] = 99
                batch_evaluated.append(prod)
            
            if batch_evaluated:
                best_in_batch = sorted(batch_evaluated, key=lambda x: x['issues_count'])[0]
                ultimate_round_contenders.append(best_in_batch)
                
        if ultimate_round_contenders:
            final_winner = sorted(ultimate_round_contenders, key=lambda x: x['issues_count'])[0]
            final_winner['link'] = f"https://amazon.in/dp/{final_winner['asin']}?tag={AFFILIATE_TAG}"
            return final_winner
            
    except Exception as e:
        print(f"[Exception] {e}")
        return None

def bot_main_loop():
    send_telegram_message("🚀 *Deal Bot Started Successfully!*")
    
    slot_index = 0
    total_slots = len(CATEGORY_BUDGET_SLOTS)
    
    while True:
        cat, current_range = CATEGORY_BUDGET_SLOTS[slot_index]
        try:
            print(f"\n[Slot {slot_index + 1}/{total_slots}] Scanning {cat} in range {current_range}...")
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
                print(f"[Success] Best deal posted for {cat}!")
            else:
                print(f"[Skip] No matching product found in exact price range for {cat}.")
                
        except Exception as e:
            print(f"Loop error: {e}")
            
        slot_index = (slot_index + 1) % total_slots
        time.sleep(7200)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_main_loop()
