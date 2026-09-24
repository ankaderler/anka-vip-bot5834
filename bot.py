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
        self.wfile.write(b"ANKA VIP Ultimate SMS Bot is running perfectly!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

BOT_TOKEN = "8874989367:AAE4ARinymcurNpCG9gF3hBrR0cKIoAP8aA"
IBAN = "TR62 0006 2000 5000 0006 8107 73"
RECIPIENT = "Resul Sakal"
SUPPORT_USERNAME = "SMSPATRONUM"

SMS_API_KEY = "osms_ff02e69d0bdd0ddf9106b60644059c77df21bb3b5a738a9e"
SMS_API_URL = "https://onaylasms.com.tr/stubs/handler_api.php"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Eksiksiz Ürün Listesi ve Genişletilmiş Küresel Stok Havuzları
SERVICES = {
    "ph_wp": {
        "name": "🔥 Filipinler WhatsApp (En Çok Satan - %0 Risk)",
        "code": "whatsapp",
        "countries": ["philippines", "indonesia", "vietnam", "malaysia", "russia", "kazakhstan", "ukraine"],
        "price_tl": 200
    },
    "uk_wp": {
        "name": "🇬🇧 İngiltere WhatsApp",
        "code": "whatsapp",
        "countries": ["uk", "england", "russia", "romania", "poland", "kazakhstan"],
        "price_tl": 150
    },
    "uk_tg": {
        "name": "🇬🇧 Yurt Dışı / İngiltere Telegram",
        "code": "telegram",
        "countries": ["uk", "england", "russia", "kazakhstan", "ukraine", "indonesia", "philippines"],
        "price_tl": 150
    },
    "tr_tg": {
        "name": "🇹🇷 TR Telegram",
        "code": "telegram",
        "countries": ["turkey", "russia", "kazakhstan", "ukraine"],
        "price_tl": 200
    },
    "tr_wp": {
        "name": "🇹🇷 TR WhatsApp",
        "code": "whatsapp",
        "countries": ["turkey", "russia", "kazakhstan"],
        "price_tl": 300
    },
    "tr_ig": {
        "name": "📸 TR Instagram",
        "code": "instagram",
        "countries": ["turkey", "russia", "indonesia"],
        "price_tl": 60
    },
    "tr_fb": {
        "name": "📘 TR Facebook",
        "code": "facebook",
        "countries": ["turkey", "russia", "vietnam"],
        "price_tl": 50
    },
    "tr_go": {
        "name": "🌐 TR Google / Gmail",
        "code": "google",
        "countries": ["turkey", "russia", "kazakhstan", "indonesia"],
        "price_tl": 30
    }
}

def main_menu():
    keyboard = []
    for key, info in SERVICES.items():
        keyboard.append([InlineKeyboardButton(f"{info['name']} — {info['price_tl']} TL", callback_data=f"iban_{key}")])
    keyboard.append([InlineKeyboardButton("📞 Canlı Destek", url=f"https://t.me/{SUPPORT_USERNAME}")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = (
            "💎 *ANKA VIP — PREMIUM SMS ONAY SERVİSİ*\n\n"
            "⚡ Kesintisiz Otomatik Numara Tedariği\n"
            "Aşağıdaki menüden almak istediğiniz güvenli servisi seçebilirsiniz."
        )
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
        elif update.callback_query:
            await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Start komutu hatası: {e}")

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dekont haricinde yazı yazıldığında kullanıcıya direkt ana menüyü gösterir"""
    try:
        if update.message and update.message.text:
            text = (
                "💎 *ANKA VIP — PREMIUM SMS ONAY SERVİSİ*\n\n"
                "⚡ Kesintisiz Otomatik Numara Tedariği\n"
                "Aşağıdaki menüden almak istediğiniz güvenli servisi seçebilirsiniz."
            )
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Metin mesajı işleme hatası: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()
        data = query.data

        if data.startswith("iban_"):
            service_key = data.replace("iban_", "")
            service_info = SERVICES.get(service_key, SERVICES["ph_wp"])
            
            context.user_data["selected_service"] = service_key

            text = (
                f"💳 *IBAN İLE ÖDEME EKRANI*\n\n"
                f"📦 Ürün: *{service_info['name']}*\n"
                f"💰 Tutar: *{service_info['price_tl']} TL*\n\n"
                f"IBAN:\n`{IBAN}`\n\n"
                f"Alıcı: *{RECIPIENT}*\n\n"
                "━━━━━━━━━━━━━━━━\n"
                f"1️⃣ Yukarıdaki hesaba tam *{service_info['price_tl']} TL* gönderin.\n"
                "2️⃣ Ödeme yaptıktan sonra banka dekontunun ekran görüntüsünü veya dosyasını **doğrudan bu sohbete gönderin**."
            )
            keyboard = [[InlineKeyboardButton("⬅️ Geri", callback_data="home")]]
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data.startswith("refresh_num_"):
            service_key = data.replace("refresh_num_", "")
            service_info = SERVICES.get(service_key, SERVICES["ph_wp"])
            
            await query.edit_message_text("🔄 Küresel havuzlar taranıyor, yeni numara aranıyor...")
            
            number, activation_id, country_used = await fetch_number_with_fallback(service_info["code"], service_info["countries"])
            
            if number:
                context.user_data["active_activation_id"] = activation_id
                text = (
                    f"✅ *Yeni Numara Başarıyla Tanımlandı!*\n\n"
                    f"📦 Ürün: *{service_info['name']}*\n"
                    f"🌍 Bölge/Ülke: `{country_used.upper()}`\n"
                    f"📱 *Yeni Numara:* `{number}`\n"
                    f"🆔 *İşlem ID:* `{activation_id}`\n\n"
                    f"⚠️ Kod gelmezse aşağıdaki butondan tekrar numara değiştirebilirsiniz."
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Numarayı Değiştir / Yenile", callback_data=f"refresh_num_{service_key}")],
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
                ]
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                text = (
                    f"⚠️ *Şu an alternatif havuzlarda yoğunluk var.*\n\n"
                    f"Lütfen hemen canlı desteğe bildirin, anında manuel numara verilsin:\n\n"
                    f"📞 Canlı Destek: @{SUPPORT_USERNAME}"
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Tekrar Dene", callback_data=f"refresh_num_{service_key}")],
                    [InlineKeyboardButton("📞 Canlı Destek", url=f"https://t.me/{SUPPORT_USERNAME}")],
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
                ]
                await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

        elif data == "home":
            text = (
                "💎 *ANKA VIP — PREMIUM SMS ONAY SERVİSİ*\n\n"
                "⚡ Kesintisiz Otomatik Numara Tedariği\n"
                "Aşağıdaki menüden almak istediğiniz güvenli servisi seçebilirsiniz."
            )
            await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        logging.error(f"Buton işleme hatası: {e}")

async def fetch_number_with_fallback(service_code, countries_list):
    """Küresel ülke listesini sırayla dener, stok bulunan ilk ülkeden numarayı çeker"""
    async with httpx.AsyncClient(timeout=15.0) as client:
        for country in countries_list:
            params = {
                "api_key": SMS_API_KEY,
                "action": "getNumber",
                "service": service_code,
                "country": country
            }
            try:
                response = await client.get(SMS_API_URL, params=params)
                res_text = response.text.strip()
                logging.info(f"API İstek [{service_code} - {country}] Yanıt: {res_text}")
                
                if "ACCESS_NUMBER" in res_text:
                    parts = res_text.split(":")
                    activation_id = parts[1] if len(parts) > 1 else "Bilinmiyor"
                    phone_number = parts[2] if len(parts) > 2 else res_text
                    return phone_number, activation_id, country
            except Exception as e:
                logging.error(f"API Bağlantı Hatası ({country}): {e}")
        
        return None, None, None

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message and (update.message.photo or update.message.document):
            service_key = context.user_data.get("selected_service", "ph_wp")
            service_info = SERVICES.get(service_key, SERVICES["ph_wp"])

            processing_msg = await update.message.reply_text("🔄 Dekont onaylandı, küresel stok havuzları taranıyor...")

            number, activation_id, country_used = await fetch_number_with_fallback(service_info["code"], service_info["countries"])

            if number:
                context.user_data["active_activation_id"] = activation_id
                text = (
                    f"✅ *Dekont Onaylandı & Numara Verildi!*\n\n"
                    f"📦 Ürün: *{service_info['name']}*\n"
                    f"🌍 Bölge/Ülke: `{country_used.upper()}`\n"
                    f"📱 *Numara:* `{number}`\n"
                    f"🆔 *İşlem ID:* `{activation_id}`\n\n"
                    f"⚠️ Kod gelmezse aşağıdaki **'Numarayı Değiştir / Yenile'** butonunu kullanabilirsiniz."
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Numarayı Değiştir / Yenile", callback_data=f"refresh_num_{service_key}")],
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
                ]
                await processing_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                text = (
                    f"✅ *Dekontunuz Onaylandı!*\n\n"
                    f"⚠️ Küresel havuzda anlık yoğunluk yaşandı.\n"
                    f"Lütfen dekontunuzla birlikte canlı desteğe yazın, hemen manuel verilsin:\n\n"
                    f"📞 Canlı Destek: @{SUPPORT_USERNAME}"
                )
                keyboard = [
                    [InlineKeyboardButton("📞 Canlı Destek", url=f"https://t.me/{SUPPORT_USERNAME}")],
                    [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
                ]
                await processing_msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            return
    except Exception as e:
        logging.error(f"Dekont işleme hatası: {e}")

def main():
    import requests
    # Telegram tarafındaki eski webhook'ları ve bekleyen güncellemeleri tamamen temizler
    try:
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
        logging.info("Telegram Webhook başarıyla sıfırlandı.")
    except Exception as e:
        logging.error(f"Webhook sıfırlama hatası: {e}")

    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    # Dekont harici herhangi bir yazı yazıldığında da menüyü açar
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    print("ANKA VIP Ürün Menüsü ve Küresel Stok Botu Aktif!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
