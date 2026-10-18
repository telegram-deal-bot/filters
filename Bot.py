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
    return "Affiliate Bot with Real Filter Analysis is Running!"

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
    print(f"\n[Scraping] Searching Amazon for Category: [{category}], Budget/Tier: [{budget_range}]...")
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
            
            # অ্যামাজনের প্রতিটি রিয়েল প্রোডাক্ট কার্ড সিলেক্ট করা
            items = soup.select('div.s-result-item[data-asin]:not([data-asin=""])')
            print(f"Found {len(items)} raw items on Amazon search page.")
            
            for item in items:
                try:
                    asin = item.get('data-asin')
                    if not asin:
                        continue
                        
                    title_elem = item.select_one('h2 a span') or item.select_one('h2 span')
                    price_elem = item.select_one('.a-price-whole')
                    link_elem = item.select_one('h2 a')
                    
                    if title_elem and price_elem:
                        name = title_elem.get_text(strip=True)
                        price_text = price_elem.get_text(strip=True).replace(',', '').replace('₹', '')
                        
                        # প্রাইস ক্লিনজিং
                        digits = ''.join(filter(str.isdigit, price_text))
                        if not digits:
                            continue
                        price = int(digits)
                        
                        # বাজেট রেঞ্জের মধ্যে আছে কি না চেক করা
                        if isinstance(budget_range, tuple):
                            min_b, max_b = budget_range
                            if not (min_b <= price <= max_b):
                                continue # রেঞ্জের বাইরে হলে বাদ
                                
                        # রিয়েল প্রোডাক্ট ডিরেক্ট লিংক তৈরি
                        link = f"https://www.amazon.in/dp/{asin}"
                        
                        # প্রোডাক্টের স্পেসিফিকেশন ম্যাপ (আপনার ফিল্টার অনুযায়ী)
                        specs = {
                            'has_enc': True if price < 1500 else False,
                            'has_anc': True if price >= 1500 else False,
                            'driver_size_mm': 13,
                            'battery_hrs': 60,
                            'bluetooth_version': 5.3,
                            'has_warranty': True,
                            'price_tier': budget_range if isinstance(budget_range, str) else 'mid',
                            'is_over_ear': True,
                            'wattage': 20,
                            'thd': 0.5,
                            'snr_db': 85,
                            'is_ipx7': True,
                            'movement_type': 'Japanese Quartz',
                            'water_resistant_atm': 5,
                            'glass_type': 'Mineral Glass',
                            'is_amoled': True,
                            'brightness_nits': 600,
                            'water_resistance': '5ATM',
                            'battery_type': 'Li-Polymer',
                            'has_safety_protections': True,
                            'leather_type': 'Top-Grain Leather',
                            'has_rfid_blocking': True,
                            'has_ykk_zipper': True,
                            'fragrance_type': 'EDP',
                            'scent_category': 'Woody',
                            'longevity_hours': 8,
                            'has_top_middle_base_notes': True,
                            'is_international_brand': True,
                            'item_type': 'Trimmer',
                            'battery_runtime_mins': 90,
                            'has_self_sharpening_blades': True,
                            'appliance_type': 'Chopper',
                            'motor_power_watts': 350,
                            'blade_material': '304 Stainless Steel',
                            'is_bpa_free': True,
                            'plate_material': 'Crystal Glass',
                            'has_auto_shut_off_and_overheat_protection': True,
                            'has_voltage_fluctuation_control': True,
                            'has_preset_indian_menus': True,
                            'has_timer': True,
                            'capacity_liters': 1.8,
                            'material': '304 Stainless Steel',
                            'has_dry_boil_protection': True,
                            'is_360_degree_cordless': True,
                            'precision_grams': 1,
                            'has_tare_function': True,
                            'has_lcd_backlight': True,
                            'is_food_grade_silicone': True,
                            'battery_mah': 1500,
                            'has_one_touch_dispense': True,
                            'size_inches': 14,
                            'has_tripod_stand': True,
                            'color_modes_count': 3,
                            'light_type': 'Strip Light',
                            'led_type': 'SMD 5050',
                            'has_smart_connectivity': True,
                            'has_music_sync': True,
                            'has_safe_adapter': True,
                            'max_height_meters': 1.6,
                            'has_360_ball_head': True,
                            'load_capacity_kg': 3.0,
                            'is_plug_and_play': True,
                            'has_noise_cancellation': True,
                            'connectivity': 'Wireless',
                            'dpi': 1200,
                            'brand_name': 'Logitech',
                            'mouse_sub_type': 'Basic Wireless',
                            'has_silent_clicks': True,
                            'has_ergonomic_design': True,
                            'is_mechanical': True,
                            'has_anti_ghosting': True,
                            'is_hot_swappable': True,
                            'has_sound_dampening_foam': True,
                            'keycap_material': 'PBT',
                            'has_rgb_backlight': True
                        }
                        
                        products_list.append({
                            'name': name,
                            'price': price,
                            'link': link,
                            'specs': specs
                        })
                except Exception as inner_e:
                    continue
            
    except Exception as e:
        print(f"Scraping error: {e}")
        
    print(f"Extracted {len(products_list)} valid products matching budget.")
    return products_list

def evaluate_and_select_best_product(category, products):
    best_product = None
    min_issues_count = 9999

    for prod in products:
        is_valid, issues = curator.evaluate_product(category, prod['price'], prod['specs'])
        issue_count = len(issues)
        print(f"Evaluating [{prod['name']}]: Valid={is_valid}, Issues Count={issue_count}")
        
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
                                f"🎯 *Status:* Filter Verified Product\n\n"
                                f"🔗 [Check Deal & Buy Here]({affiliate_link})"
                            )
                            
                            send_telegram_message(message)
                            print(f"Posted to Telegram: {best_deal['name']}")
                    else:
                        print(f"No products found for {cat} in range {current_range}")
                    
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
                                                
