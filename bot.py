import os
import threading
import http.server
import socketserver
import logging
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

PORT = int(os.environ.get("PORT", 10000))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ANKA VIP SMS Bot is live and running smoothly!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

BOT_TOKEN = "8966819189:AAHjsR8eLkkdxpK4GjCUt7mdzBcFVnagi4Q"
IBAN = "TR62 0006 2000 5000 0006 8107 73"
RECIPIENT = "Resul Sakal"
SUPPORT_USERNAME = "SMSPATRONUM"

# Güncel ve Yeni API Anahtarın
SMS_API_KEY = "osms_ff02e69d0bdd0ddf9106b60644059c77df21bb3b5a738a9e"
SMS_API_URL = "https://onaylasms.com.tr/stubs/handler_api.php"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Onaylasms API standartlarına tam uyumlu servis ve ülke parametreleri
SERVICES = {
    "tr_wp": {"name": "🇹🇷 TR WhatsApp", "code": "whatsapp", "country": "turkey", "price_tl": 300},
    "tr_tg": {"name": "🇹🇷 TR Telegram", "code": "telegram", "country": "turkey", "price_tl": 200},
    "tr_ig": {"name": "📸 TR Instagram", "code": "instagram", "country": "turkey", "price_tl": 60},
    "tr_fb": {"name": "📘 TR Facebook", "code": "facebook", "country": "turkey", "price_tl": 50},
    "tr_go": {"name": "🌐 TR Google", "code": "google", "country": "turkey", "price_tl": 30},
    "uk_wp": {"name": "🇬🇧 İngiltere WhatsApp", "code": "whatsapp", "country": "uk", "price_tl": 150},
    "tr_dc": {"name": "🎮 TR Discord", "code": "discord", "country": "turkey", "price_tl": 75},
    "tr_tw": {"name": "🐦 TR Twitter / X", "code": "twitter", "country": "turkey", "price_tl": 70},
    "tr_sn": {"name": "👻 TR Snapchat", "code": "snapchat", "country": "turkey", "price_tl": 90}
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

async def fetch_real_number_async(service_code, country_code):
    params = {
        "api_key": SMS_API_KEY,
        "action": "getNumber",
        "service": service_code,
        "country": country_code
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(SMS_API_URL, params=params)
            res_text = response.text.strip()
            logging.info(f"API Yanıtı: {res_text} | Parametreler: {params}")
            
            if "ACCESS_NUMBER" in res_text:
                parts = res_text.split(":")
                activation_id = parts[1] if len(parts) > 1 else "Bilinmiyor"
                phone_number = parts[2] if len(parts) > 2 else res_text
                return phone_number, activation_id
            else:
                return None, res_text
        except Exception as e:
            logging.error(f"API Bağlantı Hatası: {e}")
            return None, "CONNECTION_ERROR"

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        service_key = context.user_data.get("selected_service", "tr_wp")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])

        processing_msg = await update.message.reply_text("🔄 Dekont onaylandı, numara alınıyor...")

        number, info = await fetch_real_number_async(service_info["code"], service_info["country"])

        if number:
            text = (
                f"✅ *Dekont Onaylandı & Numara Verildi!*\n\n"
                f"📦 Servis: *{service_info['name']}*\n"
                f"📱 *Numara:* `{number}`\n"
                f"🆔 *İşlem ID:* `{info}`\n\n"
                f"⚠️ Kod takibi için destek hattı: @{SUPPORT_USERNAME}"
            )
            keyboard = [[InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]]
            await processing_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = (
                f"✅ *Dekontunuz Onaylandı!*\n\n"
                f"⚠️ API Yanıtı: `{info}`\n"
                f"Lütfen dekontunuzla birlikte hemen canlı desteğe yazın, numaranız anında manuel verilsin:\n\n"
                f"📞 Canlı Destek: @{SUPPORT_USERNAME}"
            )
            keyboard = [
                [InlineKeyboardButton("📞 Canlı Destek", url=f"https://t.me/{SUPPORT_USERNAME}")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
            ]
            await processing_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("📸 Lütfen geçerli bir banka dekontu gönderin.")

def main():
    import requests
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
    except:
        pass

    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    
    print("ANKA VIP SMS BOT Yeni API ile Başlatıldı!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
