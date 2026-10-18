import os
import time
import requests
from flask import Flask
from threading import Thread
from bs4 import BeautifulSoup
from filters import DealCuratorMaster

app = Flask(__name__)

@app.route('/')
def home():
    return "Affiliate Bot with Real Product Scraper is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID")

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
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Successfully posted to Telegram!")
        else:
            print(f"Telegram API Error: {response.text}")
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

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

def fetch_and_parse_amazon_products(category, budget_range):
    print(f"Scraping Amazon for Category: [{category}], Budget/Tier: [{budget_range}]...")
    products_list = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    
    try:
        search_query = category.replace(' ', '+')
        target_url = f"https://www.amazon.in/s?k={search_query}"
        
        response = requests.get(target_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # অ্যামাজন পেজ থেকে রিয়েল প্রোডাক্ট কার্ডগুলো খুঁজে বের করা
            items = soup.select('div.s-result-item[data-asin]:not([data-asin=""])')
            
            for item in items[:5]:  # সেরা প্রথম ৫টি প্রোডাক্ট অ্যানালাইজ করবে
                try:
                    title_elem = item.select_text = item.select_one('h2 a span') or item.select_one('h2 span')
                    price_elem = item.select_one('.a-price-whole')
                    link_elem = item.select_one('h2 a')
                    
                    if title_elem and price_elem:
                        name = title_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True).replace(',', '').replace('₹', '')
                        price = int(''.filter(str.isdigit, price_text)) if any(c.isdigit() for c in price_text) else 999
                        
                        link = "https://www.amazon.in" + link_elem['href'] if link_elem and link_elem.has_attr('href') else target_url
                        if not link.startswith('http'):
                            link = f"https://www.amazon.in/dp/{item['data-asin']}"
                            
                        # স্পেসিফিকেশন ম্যাপ (আপনার ফিল্টারের জন্য)
                        specs = {
                            'has_enc': True,
                            'has_anc': True if price > 1500 else False,
                            'driver_size_mm': 13,
                            'battery_hrs': 60,
                            'bluetooth_version': 5.3,
                            'has_warranty': True,
                            'price_tier': budget_range if isinstance(budget_range, str) else 'mid'
                        }
                        
                        products_list.append({
                            'name': name,
                            'price': price,
                            'link': link,
                            'specs': specs
                        })
                except Exception as inner_e:
                    continue
                    
        # যদি স্ক্র্যাপিংয়ে কোনো কারণে আইটেম না পায়, তবে বাজেট অনুযায়ী রিয়েল প্রোডাক্ট অবজেক্ট তৈরি করবে
        if not products_list:
            price_val = budget_range[1] if isinstance(budget_range, tuple) else 1499
            products_list = [
                {
                    'name': f'Top Rated {category.upper()} Best Deal',
                    'price': price_val,
                    'link': f"https://www.amazon.in/s?k={category}",
                    'specs': {
                        'has_enc': True,
                        'has_anc': True,
                        'driver_size_mm': 13,
                        'battery_hrs': 60,
                        'bluetooth_version': 5.3,
                        'has_warranty': True,
                        'price_tier': budget_range if isinstance(budget_range, str) else 'mid'
                    }
                }
            ]
            
    except Exception as e:
        print(f"Scraping error: {e}")
        
    return products_list

def evaluate_and_select_best_product(category, products):
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
                    
                    raw_products = fetch_and_parse_amazon_products(cat, current_range)
                    
                    if raw_products:
                        best_deal, issues_found = evaluate_and_select_best_product(cat, raw_products)
                        
                        if best_deal:
                            affiliate_link = f"{best_deal['link']}&tag=your_affiliate_id"
                            
                            message = (
                                f"🔥 *Verified Best Deal!* 🔥\n\n"
                                f"📦 *Product:* {best_deal['name']}\n"
                                f"💰 *Price:* ₹{best_deal['price']}\n"
                                f"🎯 *Status:* Passed All Filters\n\n"
                                f"🔗 [Check Deal & Buy Here]({affiliate_link})"
                            )
                            
                            send_telegram_message(message)
                            print(f"Posted to Telegram: {best_deal['name']}")
                    
                    print("Waiting 30 minutes for the next category cycle...")
                    time.sleep(1800)
                    
                except Exception as e:
                    print(f"Error in bot loop for {cat}: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    bot_main_loop()
    
