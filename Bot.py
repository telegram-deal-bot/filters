import os
import time
import requests
from flask import Flask
from threading import Thread
from filters import DealCuratorMaster  # আপনার তৈরি করা filters.py থেকে মডিউল ইমপোর্ট করা হলো

app = Flask(__name__)

@app.route('/')
def home():
    return "Affiliate Bot with Cookie Session & Modular Filters is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# টেলিগ্রাম কনফিগারেশন (এনভায়রনমেন্ট ভেরাবেল থেকে টোকেন ও চ্যাট আইডি নেওয়া হবে)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

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
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Failed to send telegram message: {e}")

# ক্যাটাগরি এবং তাদের বাজেট রেঞ্জ সাইকেল
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

def fetch_products_with_cookies(category, budget_range):
    """
    আইডিয়া ২ অনুযায়ী: এখানে ইউজারের সেভ করা লগইন কুকিজ বা সেশন ব্যবহার করে 
    আমাজন/ফ্লিপকার্ট থেকে রিয়েল প্রোডাক্ট ডেটা ও লিংক ফেচ করা হবে।
    """
    print(f"Fetching products for Category: {category} in Budget/Tier: {budget_range} using authenticated session...")
    
    # ডেমো হিসেবে মক প্রোডাক্ট লিস্ট (আপনার স্ক্র্যাপিং লজিক এখানে যুক্ত হবে যা কুকিজ ব্যবহার করবে)
    # স্ক্র্যাপিং করার সময় অবশ্যই ইউজারের ব্রাউজার কুকিজ হেডার হিসেবে পাস করতে হবে যাতে ক্যাপচা না আসে।
    scraped_products = [
        {
            'name': f'Sample Best {category.upper()} Pro',
            'price': budget_range[1] if isinstance(budget_range, tuple) else 1999,
            'link': 'https://amazon.in/sample-affiliate-link',
            'specs': {
                'has_enc': True,
                'driver_size_mm': 13,
                'battery_hrs': 60,
                'bluetooth_version': 5.3,
                'has_warranty': True,
                'price_tier': budget_range if isinstance(budget_range, str) else 'mid'
            }
        }
    ]
    return scraped_products

def evaluate_and_select_best_product(category, products):
    """
    সবচেয়ে বেশি স্পেক্স মিলবে (সবচেয়ে কম ইস্যু বা ত্রুটি থাকবে) এমন সেরা প্রোডাক্টটি বেছে নেওয়ার স্কোরিং লজিক।
    """
    best_product = None
    min_issues_count = 9999

    for prod in products:
        is_valid, issues = curator.evaluate_product(category, prod['price'], prod['specs'])
        
        # সব কন্ডিশন হুবহু না মিললেও, যেটিতে সবচেয়ে কম ইস্যু বা ত্রুটি থাকবে তাকেই স্কোরিংয়ের মাধ্যমে বিবেচনা করা হবে
        issue_count = len(issues)
        
        # যদি প্রোডাক্টটি সম্পূর্ণ ভ্যালিড হয় অথবা আগেরগুলোর চেয়ে কম ইস্যু থাকে
        if issue_count < min_issues_count:
            min_issues_count = issue_count
            best_product = prod

    return best_product, min_issues_count

def bot_main_loop():
    """
    অটোপাইলটে ক্যাটাগরি ও বাজেট রেঞ্জ সাইকেল ঘুরিয়ে সেরা ডিল পোস্ট করার লজিক
    """
    categories = list(CATEGORY_BUDGET_CYCLES.keys())
    
    while True:
        for cat in categories:
            ranges = CATEGORY_BUDGET_CYCLES[cat]
            for current_range in ranges:
                try:
                    print(f"\n--- Cycling: Category [{cat}], Range/Tier [{current_range}] ---")
                    
                    # ১. কুকিজ ও সেশন ব্যবহার করে প্রোডাক্ট ফেচ করা
                    raw_products = fetch_products_with_cookies(cat, current_range)
                    
                    if raw_products:
                        # ২. স্কোরের ভিত্তিতে সেরা প্রোডাক্ট নির্বাচন করা
                        best_deal, issues_found = evaluate_and_select_best_product(cat, raw_products)
                        
                        if best_deal:
                            # আপনার অ্যাফিলিয়েট টোকেন বা ট্যাগ লিংকের সাথে জুড়ে দেওয়া
                            affiliate_link = f"{best_deal['link']}?tag=your_affiliate_id"
                            
                            message = (
                                f"🔥 *Best Deal Found!* 🔥\n\n"
                                f"📦 *Product:* {best_deal['name']}\n"
                                f"💰 *Price:* ₹{best_deal['price']}\n"
                                f"🎯 *Status:* Top Spec-to-Price Match\n\n"
                                f"🔗 [Check Deal & Buy Here]({affiliate_link})"
                            )
                            
                            send_telegram_message(message)
                            print(f"Posted to Telegram: {best_deal['name']}")
                    
                    # প্রতি সাইকেলের মাঝে নির্দিষ্ট বিরতি (যেমন ৩০ মিনিট বা ১ ঘণ্টা)
                    time.sleep(1800)
                    
                except Exception as e:
                    print(f"Error in bot loop for {cat}: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    # ফ্লাস্ক সার্ভার ডেমোন ব্যাকগ্রাউন্ডে চালু রাখা (Railway Heartbeat-এর জন্য)
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # মূল বট লজিক রান করা
    bot_main_loop()
      
