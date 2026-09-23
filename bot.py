import os
import threading
import http.server
import socketserver
import logging
import time
import requests
from telegram import Update, LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    ContextTypes,
    filters,
)

# Render Port Ayarı (Canlı kalması için)
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

# Onayla SMS Gerçek API Bilgileri
SMS_API_KEY = "osms_1a63dee621f99dd7a01b8082b0de694c23a822dce4a24225"
SMS_API_URL = "https://onaylasms.com.tr/stubs/handler_api.php"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Güncellenmiş Servisler (ABD çıkarıldı, İngiltere kaldı, Yıldızlar 25 artırıldı)
SERVICES = {
    "tr_wp": {"name": "TR WhatsApp", "code": "wa", "country": "62", "price_tl": 300, "price_stars": 175},
    "tr_tg": {"name": "TR Telegram", "code": "tg", "country": "62", "price_tl": 200, "price_stars": 125},
    "tr_ig": {"name": "TR Instagram", "code": "ig", "country": "62", "price_tl": 60, "price_stars": 55},
    "tr_fb": {"name": "TR Facebook", "code": "fb", "country": "62", "price_tl": 50, "price_stars": 50},
    "tr_go": {"name": "TR Google", "code": "go", "country": "62", "price_tl": 30, "price_stars": 40},
    "uk_wp": {"name": "İngiltere WhatsApp", "code": "wa", "country": "16", "price_tl": 150, "price_stars": 100}
}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🇹🇷 TR WhatsApp — 300 TL / 175 ⭐", callback_data="serv_tr_wp")],
        [InlineKeyboardButton("🇹🇷 TR Telegram — 200 TL / 125 ⭐", callback_data="serv_tr_tg")],
        [InlineKeyboardButton("📸 TR Instagram — 60 TL / 55 ⭐", callback_data="serv_tr_ig")],
        [InlineKeyboardButton("📘 TR Facebook — 50 TL / 50 ⭐", callback_data="serv_tr_fb")],
        [InlineKeyboardButton("🌐 TR Google — 30 TL / 40 ⭐", callback_data="serv_tr_go")],
        [InlineKeyboardButton("🇬🇧 İngiltere WhatsApp — 150 TL / 100 ⭐", callback_data="serv_uk_wp")],
        [InlineKeyboardButton("📞 Canlı Destek", url=f"https://t.me/{SUPPORT_USERNAME}")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 *ANKA VIP — SMS ONAY SERVİSİ*\n\n"
        "⚡ Güvenli ve Hızlı Numara Tedariği\n"
        "Aşağıdaki menüden dilediğiniz ülke ve platformu seçerek ödeme yöntemine geçebilirsiniz."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("serv_"):
        service_key = data.replace("serv_", "")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])
        
        context.user_data["selected_service"] = service_key

        text = (
            f"🛒 *Seçilen Paket: {service_info['name']}*\n\n"
            "👇 Lütfen ödemeyi yapmak istediğiniz yöntemi seçin:"
        )
        keyboard = [
            [InlineKeyboardButton(f"⭐ Telegram Yıldızı ile Al ({service_info['price_stars']} Yıldız)", callback_data=f"star_{service_key}")],
            [InlineKeyboardButton(f"💳 IBAN / Havale ile Al ({service_info['price_tl']} TL)", callback_data=f"iban_{service_key}")],
            [InlineKeyboardButton("⬅️ Geri", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("iban_"):
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
            "2️⃣ Ödeme yaptıktan sonra banka dekontunun ekran görüntüsünü bu sohbete gönderin."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Geri", callback_data=f"serv_{service_key}")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("star_"):
        service_key = data.replace("star_", "")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])
        context.user_data["selected_service"] = service_key

        title = f"SMS Onay: {service_info['name']}"
        description = f"{service_info['name']} için anında numara ve SMS aktivasyon hizmeti."
        payload = f"sms_pay_{service_key}"
        currency = "XTR"
        prices = [LabeledPrice("SMS Onay Hizmeti", service_info["price_stars"])]

        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency=currency,
            prices=prices,
            start_parameter="sms-sub"
        )

    elif data == "home":
        text = (
            "💎 *ANKA VIP — SMS ONAY SERVİSİ*\n\n"
            "⚡ Güvenli ve Hızlı Numara Tedariği\n"
            "Aşağıdaki menüden almak istediğiniz ülke ve platformu seçebilirsiniz."
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("sms_pay_"):
        await query.answer(ok=True)

# Gelişmiş Tekrar Deneme Mekanizması (NO_NUMBERS hatasını aşmak için)
def fetch_real_number_with_retry(service_code, country_code):
    params = {
        "api_key": SMS_API_KEY,
        "action": "getNumber",
        "service": service_code,
        "country": country_code
    }
    
    last_response = ""
    # 5 kez deneme yaparak stok yakalama şansını maksimuma çıkarıyoruz
    for attempt in range(5):
        try:
            response = requests.get(SMS_API_URL, params=params, timeout=15)
            last_response = response.text.strip()
            logging.info(f"API Yanıtı (Deneme {attempt+1}): {last_response}")
            
            if "ACCESS_NUMBER" in last_response:
                parts = last_response.split(":")
                activation_id = parts[1] if len(parts) > 1 else "Bilinmiyor"
                phone_number = parts[2] if len(parts) > 2 else last_response
                return phone_number, f"Kod Bekleniyor (ID: {activation_id})"
            
            # Eğer NO_NUMBERS veya NO_BALANCE dönerse 3 saniye bekleyip tekrar denesin
            time.sleep(3)
        except Exception as e:
            last_response = str(e)
            logging.error(f"API İstek Hatası: {last_response}")
            time.sleep(3)
            
    return None, last_response

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if payment.invoice_payload.startswith("sms_pay_"):
        service_key = payment.invoice_payload.replace("sms_pay_", "")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])

        assigned_number, sms_status = fetch_real_number_with_retry(service_info["code"], service_info["country"])

        if assigned_number:
            text = (
                "⭐ *YILDIZ ÖDEMESİ BAŞARILI & NUMARA ÇEKİLDİ!*\n\n"
                f"📦 Servis: *{service_info['name']}*\n"
                f"📱 *Numara:* `{assigned_number}`\n"
                f"💬 *Detay:* `{sms_status}`\n\n"
                f"⚠️ Destek & Sorun Bildirimi İçin: @{SUPPORT_USERNAME}"
            )
            keyboard = [[InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]]
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = (
                "⚠️ *Anlık yoğunluk nedeniyle numara tedarik edilemedi!*\n\n"
                f"API Yanıtı: `{sms_status}`\n"
                f"Lütfen hemen canlı destekten numaranızı isteyin:\n"
                f"İletişim / Destek: @{SUPPORT_USERNAME}"
            )
            keyboard = [
                [InlineKeyboardButton("📞 Canlı Destek ile Bağlan", url=f"https://t.me/{SUPPORT_USERNAME}")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
            ]
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        service_key = context.user_data.get("selected_service", "tr_wp")
        service_info = SERVICES.get(service_key, SERVICES["tr_wp"])

        assigned_number, sms_status = fetch_real_number_with_retry(service_info["code"], service_info["country"])

        if assigned_number:
            text = (
                f"✅ *Dekont Onaylandı & Numara Çekildi!*\n\n"
                f"📦 Servis: *{service_info['name']}*\n"
                f"📱 *Numara:* `{assigned_number}`\n"
                f"💬 *Detay:* `{sms_status}`\n\n"
                f"⚠️ Destek & Sorun Bildirimi İçin: @{SUPPORT_USERNAME}"
            )
            keyboard = [[InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]]
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            text = (
                "⚠️ *Anlık yoğunluk nedeniyle alternatif havuzda da numara kalmadı!*\n\n"
                f"API Yanıtı: `{sms_status}`\n"
                f"Lütfen hemen canlı destekten numaranızı isteyin:\n"
                f"İletişim / Destek: @{SUPPORT_USERNAME}"
            )
            keyboard = [
                [InlineKeyboardButton("📞 Canlı Destek ile Bağlan", url=f"https://t.me/{SUPPORT_USERNAME}")],
                [InlineKeyboardButton("🏠 Ana Menü", callback_data="home")]
            ]
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("📸 Lütfen geçerli bir dekont görseli veya dosyası gönderin.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    
    print("ANKA VIP SMS BOT Aktif!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
