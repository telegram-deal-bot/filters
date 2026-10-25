import os
import time
import random
import requests
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Simple & Robust Sequential Deal Bot is Active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "technicalbot2-21")

# একটি মাত্রভিন্ন প্রাইমারি এপিআই কি (Railway থেকে কন্ট্রোল করার জন্য)
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
]

def fetch_deal(category, budget_range):
    if not SERPAPI_API_KEY:
        print("[Error] SERPAPI_API_KEY is missing in Railway Variables!")
        send_telegram_message("⚠️ *Alert:* SerpApi Key missing in Railway! Please update.")
        return None

    clean_query = str(category).strip().replace(' ', '+')
    min_p, max_p = budget_range
    serp_url = f"https://serpapi.com/search.json?engine=amazon&q={clean_query}&amazon_domain=amazon.in&api_key={SERPAPI_API_KEY}"
    
    try:
        res = requests.get(serp_url, timeout=30)
        if res.status_code != 200:
            print(f"[API Error] Status code: {res.status_code}")
            return None
            
        data = res.json()
        if "error" in data:
            print(f"[API Limit/Error] {data['error']}")
            send_telegram_message(f"⚠️ *API Credit Exhausted or Error:* {data['error']}\n\nPlease update key in Railway.")
            return None
            
        items = data.get('organic_results', []) or data.get('shopping_results', []) or data.get('search_results', [])
        
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
                
            if min_p <= price <= max_p:
                link = f"https://amazon.in/dp/{asin}?tag={AFFILIATE_TAG}"
                return {'name': name, 'price': price, 'link': link}
                
    except Exception as e:
        print(f"[Fetch Exception] {e}")
        
    return None

def bot_main_loop():
    send_telegram_message("🚀 *Sequential Deal Bot Started Successfully!* \n\nFollowing exact category & price slots.")
    
    slot_index = 0
    total_slots = len(CATEGORY_BUDGET_SLOTS)
    
    while True:
        cat, current_range = CATEGORY_BUDGET_SLOTS[slot_index]
        try:
            print(f"\n[Slot {slot_index + 1}/{total_slots}] Scanning {cat} in range {current_range}...")
            
            deal = fetch_deal(cat, current_range)
            
            if deal:
                message = (
                    f"🏆 *সেরার সেরা ডিল\!* 🏆\n\n"
                    f"📦 *প্রোডাক্ট:* {deal['name'][:55]}...\n"
                    f"💰 *দাম:* ₹{deal['price']}\n"
                    f"🎯 *ক্যাটাগরি:* {cat.upper()} ({current_range[0]}\-{current_range[1]})\n\n"
                    f"🛒 *সরাসরি কিনতে লিংকে ক্লিক করুন:* \n"
                    f"🔗 [এখানে ক্লিক করে অর্ডার করুন]({deal['link']})"
                )
                send_telegram_message(message)
                print(f"[Success] Deal posted for {cat}!")
            else:
                print(f"[Skip] No matching item found for {cat} in range {current_range}.")
                
        except Exception as e:
            print(f"Loop error: {e}")
            
        slot_index = (slot_index + 1) % total_slots
        print("Sleeping for 2 hours before the next slot...")
        time.sleep(7200)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    bot_main_loop()
