import os
import threading
import http.server
import socketserver
import logging
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Render Port Ayarı
PORT = int(os.environ.get("PORT", 10000))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ANKA VIP SMS Bot is live and running!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# BOT VE API BİLGİLERİ
BOT_TOKEN = "8966819189:AAENmHdrI8XxNexWFsaAqyfHZn7kxi0N-CQ"
IBAN = "TR62 0006 2000 5000 0006 8107 73"
RECIPIENT = "Resul Sakal"
SUPPORT_USERNAME = "SMSPATRONUM"

SMS_API_KEY = "osms_1a63dee621f99dd7a01b8082b0de694c23a822dce4a24225"
SMS_API_URL = "https://onaylasms.com.tr/stubs/handler_api.php"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Kesin ve Net İstediğin Servis Listesi (Yıldız yok, sadece TL fiyatlar)
SERVICES = {
    "tr_wp": {"name": "🇹🇷 TR WhatsApp", "code": "wa", "country": "0", "price_tl": 300},
    "tr_tg": {"name": "🇹🇷 TR Telegram", "code": "tg", "country": "0", "price_tl": 200},
    "tr_ig": {"name": "📸 TR Instagram", "code": "ig", "country": "0", "price_tl": 60},
    "tr_fb": {"name": "📘 TR Facebook", "code": "fb", "country": "0", "price_tl": 50},
    "tr_go": {"name": "🌐 TR Google", "code": "go", "country": "0", "price_tl": 30},
    "uk_wp": {"name": "🇬🇧 İngiltere WhatsApp", "code": "wa", "country": "16", "price_tl": 150},
    "tr_dc": {"name": "🎮 TR Discord", "code": "dc", "country": "0", "price_tl": 75},
    "tr_tw": {"name": "🐦 TR Twitter / X", "code": "tw", "country": "0", "price_tl": 70},
    "tr_sn": {"name": "👻 TR Snapchat", "code": "sn", "country": "0", "price_tl": 90}
}

def main_menu():
    keyboard = []
    for key, info in SERVICES.items():
        keyboard.append([InlineKeyboardButton(f"{info['name']} — {info['price_tl']} TL", callback_data=f"iban_{key}")])
    keyboard.append([InlineKeyboardButton("📞 Canlı Destek", url=f"https://t.me/{SUPPORT_USERNAME}")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 *ANKA VIP — SMS ONAY SERVİSİ*\n\n"
        "⚡ Güvenli ve Hızlı Numara Tedariği\n"
        "Aşağıdaki menüden almak istediğiniz servisi seçerek ödeme adımına geçebilirsiniz."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("iban_"):
        service_key = data.replace("iban_", "")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])
        
        context.user_data["selected_service"] = service_key

        text = (
            f"💳 *IBAN İLE ÖDEME EKRANI*\n\n"
            f"📦 Paket: *{service_info['name']}*\n"
            f"💰 Tutar: *{service_info['price_tl']} TL*\n\n"
            f"IBAN:\n`{IBAN}`\n\n"
            f"Alıcı: *{RECIPIENT}*\n\n"
            "━━━━━━━━━━━━━━━━\n"
            f"1️⃣ Yukarıdaki hesaba tam *{service_info['price_tl']} TL* gönderin.\n"
            "2️⃣ Ödeme yaptıktan sonra banka dekontunun ekran görüntüsünü veya dosyasını **doğrudan bu sohbete gönderin**."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Geri", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "home":
        text = (
            "💎 *ANKA VIP — SMS ONAY SERVİSİ*\n\n"
            "⚡ Güvenli ve Hızlı Numara Tedariği\n"
            "Aşağıdaki menüden almak istediğiniz servisi seçebilirsiniz."
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

def fetch_real_number_with_retry(service_code, country_code):
    params = {
        "api_key": SMS_API_KEY,
        "action": "getNumber",
        "service": service_code,
        "country": country_code
    }
    
    last_response = ""
    for attempt in range(20):
        try:
            response = requests.get(SMS_API_URL, params=params, timeout=10)
            last_response = response.text.strip()
            logging.info(f"API İstek Detayı -> Servis: {service_code}, Ülke: {country_code}, Deneme: {attempt+1}, Yanıt: {last_response}")
            
            if "ACCESS_NUMBER" in last_response:
                parts = last_response.split(":")
                activation_id = parts[1] if len(parts) > 1 else "Bilinmiyor"
                phone_number = parts[2] if len(parts) > 2 else last_response
                return phone_number, f"Kod Bekleniyor (ID: {activation_id})"
            
            time.sleep(1)
        except Exception as e:
            last_response = str(e)
            logging.error(f"API Bağlantı Hatası: {last_response}")
            time.sleep(1)
            
    return None, last_response

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        service_key = context.user_data.get("selected_service", "tr_wp")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])

        processing_msg = await update.message.reply_text("🔄 Dekont alındı, numara hazırlanıyor...")

        assigned_number, sms_status = fetch_real_number_with_retry(service_info["code"], service_info["country"])

        if assigned_number:
            text = (
                f"✅ *Dekontunuz onaylandı!*\n\n"
                f"📦 Servis: *{service_info['name']}*\n"
                f"📱 *Numara:* `{assigned_number}`\n"
                f"💬 *Durum:* `{sms_status}`\n\n"
                f"⚠️ Sorun bildirimleri ve kod takibi için: @{SUPPORT_USERNAME}"
            )
            keyboard = [[InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="home")]]
            await processing_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = (
                "⚠️ *Anlık yoğunluk nedeniyle alternatif havuzda da numara kalmadı.*\n"
                f"Lütfen hemen canlı destekten numaranızı isteyin:\n\n"
                f"📞 İletişim / Destek: @{SUPPORT_USERNAME}"
            )
            keyboard = [
                [InlineKeyboardButton("📞 Canlı Destek ile Bağlan", url=f"https://t.me/{SUPPORT_USERNAME}")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
            ]
            await processing_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("📸 Lütfen geçerli bir banka dekontu görseli veya belgesi gönderin.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    
    print("ANKA VIP SMS BOT Tamamen Temizlendi ve Başlatılıyor...")
    # Eski webhook ve birikmiş güncellemeleri tamamen siler, botu sıfırdan konuşturur
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
