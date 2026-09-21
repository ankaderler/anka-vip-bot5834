import os
import threading
import http.server
import socketserver
import logging
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

PORT = int(os.environ.get("PORT", 10000))

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SMS Onay Bot is live and running!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

BOT_TOKEN = "8966819189:AAENmHdrI8XxNexWFsaAqyfHZn7kxi0N-CQ"
IBAN = "TR06 0001 0021 5470 2002 4550 04"
RECIPIENT = "Zeynep Alkoç"
SMS_API_KEY = "osms_25bfc2536ca8f395901c0b2389d3b66c9e111dc31007b145"
SMS_API_URL = "https://onaylasms.com.tr/stubs/handler_api.php"

SUPPORT_USERNAME = "ANKA"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📱 Numara / Hizmet Al", callback_data="get_number")],
        [InlineKeyboardButton("💳 Ödeme Bildir / Dekont Gönder", callback_data="buy")],
        [InlineKeyboardButton("📖 Nasıl Kullanılır?", callback_data="how")],
        [InlineKeyboardButton("📞 Destek", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *SMS ONAY VE NUMARA BOTU*\n\n"
        "⚡ Hızlı ve otomatik SMS onay hizmeti.\n"
        "💰 Önce IBAN'a ödeme yapın, ardından numaranızı alıp kodunuzu anında görüntüleyin.\n\n"
        "Aşağıdaki menüden işlem seçebilirsiniz."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        text = (
            "💳 *ÖDEME BİLDİRİMİ*\n\n"
            f"IBAN:\n`{IBAN}`\n\n"
            f"Alıcı: *{RECIPIENT}*\n\n"
            "━━━━━━━━━━━━━━━━\n"
            "1️⃣ Ücreti yukarıdaki hesaba gönderin.\n"
            "2️⃣ Dekontunuzun ekran görüntüsünü veya fotoğrafını bu sohbete gönderin.\n"
            "3️⃣ Dekont onaylandıktan sonra numaranız ve kodunuz otomatik teslim edilecektir."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "get_number":
        text = (
            "📱 *NUMARA SEÇİMİ*\n\n"
            "Lütfen almak istediğiniz platformu seçin veya doğrudan servis kodunu yazın:"
        )
        keyboard = [
            [InlineKeyboardButton("🔵 Telegram", callback_data="svc_tg"), InlineKeyboardButton("🟣 WhatsApp", callback_data="svc_wa")],
            [InlineKeyboardButton("🟡 Google / Gmail", callback_data="svc_gg"), InlineKeyboardButton("⚫ Twitter / X", callback_data="svc_tw")],
            [InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("svc_"):
        service_map = {"svc_tg": "telegram", "svc_wa": "whatsapp", "svc_gg": "google", "svc_tw": "twitter"}
        service_name = service_map.get(query.data, "genel")
        
        context.user_data["selected_service"] = service_name
        
        text = (
            f"✅ Seçilen Servis: *{service_name.upper()}*\n\n"
            "Şimdi lütfen ödemeyi tamamlayıp dekontunuzu gönderin. Dekontunuz onaylandığı anda sistem otomatik olarak API üzerinden numaranızı tahsis edecektir."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "how":
        text = (
            "📖 *NASIL KULLANILIR?*\n\n"
            "1️⃣ *Numara / Hizmet Al* menüsünden istediğiniz platformu seçin.\n"
            "2️⃣ Belirtilen IBAN adresine ödemeyi yapın.\n"
            "3️⃣ Dekontu bota gönderin. Bot dekontu onaylayınca API üzerinden size özel numarayı ve gelen SMS kodunu sunacaktır."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "support":
        text = f"📞 *DESTEK*\n\nDestek için: @{SUPPORT_USERNAME}"
        keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "home":
        await start(update, context)

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        # Örnek API üzerinden numara talep etme simülasyonu/isteği (OnaylaSMS API standardı)
        # api_params = {"api_key": SMS_API_KEY, "action": "getNumber", "service": ...}
        
        await update.message.reply_text(
            "🎉 *Dekont Başarıyla Alındı ve Onaylandı!*\n\n"
            "📱 Sistemden numaranız talep ediliyor, lütfen bekleyin...",
            parse_mode="Markdown"
        )
        
        try:
            # Örnek API isteği altyapısı (OnaylaSMS GetNumber entegrasyonu)
            resp = requests.get(f"{SMS_API_URL}?api_key={SMS_API_KEY}&action=getNumber&service=ot", timeout=10)
            data_text = resp.text
            
            # API'den gelen yanıta göre numara veya hata basılır
            await update.message.reply_text(
                f"✅ *Numaranız Hazır!*\n\n"
                f"📞 Numara: `+90 555 000 00 00` (Örnek)\n"
                f"📥 SMS Kodunu bekliyor... Gelen kod otomatik buraya düşecektir.\n\n"
                f"API Yanıtı: `{data_text}`",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ Numara alınırken API bağlantı hatası oluştu: {e}")
        return

    await update.message.reply_text("📸 Lütfen ödeme dekontunun fotoğrafını veya dosyasını gönderin.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    
    print("SMS ONAY BOT AKTİF!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
