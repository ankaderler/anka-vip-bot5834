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
        [InlineKeyboardButton("📱 Numara / Hizmet Seç", callback_data="get_number")],
        [InlineKeyboardButton("💳 Ödeme Bildir / Dekont Gönder", callback_data="buy")],
        [InlineKeyboardButton("📖 Nasıl Kullanılır?", callback_data="how")],
        [InlineKeyboardButton("📞 Destek", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *SMS ONAY VE NUMARA BOTU*\n\n"
        "⚡ Hızlı ve otomatik SMS onay hizmeti.\n"
        "💰 Önce IBAN'a ödeme yapın, ardından numaranızı seçip kodunuzu alın.\n\n"
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
            "3️⃣ Dekont onaylandıktan sonra seçtiğiniz servis için numaranız otomatik verilecektir."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "get_number":
        text = (
            "📱 *HİZMET SEÇİMİ*\n\n"
            "Lütfen numara almak istediğiniz platformu seçin:"
        )
        keyboard = [
            [InlineKeyboardButton("🔵 Telegram", callback_data="svc_telegram"), InlineKeyboardButton("🟣 WhatsApp", callback_data="svc_whatsapp")],
            [InlineKeyboardButton("🟡 Google / Gmail", callback_data="svc_google"), InlineKeyboardButton("⚫ Twitter / X", callback_data="svc_twitter")],
            [InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("svc_"):
        service_code = query.data.replace("svc_", "")
        context.user_data["selected_service"] = service_code
        
        text = (
            f"✅ Seçilen Servis: *{service_code.upper()}*\n\n"
            "Şimdi ödemeyi yapıp dekontunuzu bota gönderin. Dekont onaylandığı an sistem bu servis için stoktan numara çekecektir."
        )
        keyboard = [
            [InlineKeyboardButton("💳 Ödeme Bildir / Dekont Gönder", callback_data="buy")],
            [InlineKeyboardButton("⬅️ Ana Menü", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "how":
        text = (
            "📖 *NASIL KULLANILIR?*\n\n"
            "1️⃣ *Numara / Hizmet Seç* menüsünden platformu seçin.\n"
            "2️⃣ IBAN'a ödemeyi yapıp dekontu bota atın.\n"
            "3️⃣ Bot onay verince API üzerinden numaranız ve kodunuz gelecektir."
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
        selected_service = context.user_data.get("selected_service", "telegram")
        
        await update.message.reply_text(
            "🎉 *Dekont Başarıyla Alındı ve Onaylandı!*\n\n"
            f"📱 `{selected_service.upper()`} servisi için havuzdan numara talep ediliyor...",
            parse_mode="Markdown"
        )
        
        try:
            # OnaylaSMS API formatına uygun istek
            api_url = f"{SMS_API_URL}?api_key={SMS_API_KEY}&action=getNumber&service={selected_service}"
            resp = requests.get(api_url, timeout=10)
            data_text = resp.text
            
            await update.message.reply_text(
                f"✅ *İşlem Sonucu / API Yanıtı:*\n\n"
                f"`{data_text}`\n\n"
                "*(Eğer API'den numara dönmezse, servis adının sistemdeki kısa kod karşılığını kontrol edebiliriz.)*",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ API bağlantı hatası oluştu: {e}")
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
