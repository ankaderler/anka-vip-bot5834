import os
import threading
import http.server
import socketserver
import logging
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
        self.wfile.write(b"VIP Link Delivery Bot is live and running!")

def run_web_server():
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# BOT VE ÖDEME BİLGİLERİ
BOT_TOKEN = "8522565760:AAGHVItP1h7Wn_CS41IapWDIEVuDiNOQTNs"
IBAN = "TR62 0006 2000 5000 0006 8107 73"
RECIPIENT = "Resul Sakal"
PRICE_TL = "300 TL"
PRICE_STARS = 150  # Telegram Yıldız Miktarı

# TESLİM EDİLECEK VIP LİNKLER
VIP_LINKS = [
    "https://t.me/+Aqi4UqSzr4JjZmRk",
    "https://t.me/+H2z-xlyZ6zM0OTE0",
    "https://t.me/+p01bQp6XebkzMmI0",
    "https://t.me/+HqtuwLtoMkkwMWQ0",
    "https://t.me/+BcHhS86B9ocyMWQ0"
]

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("⭐ Telegram Yıldızı ile Satın Al (Anında)", callback_data="buy_with_stars")],
        [InlineKeyboardButton("💳 IBAN / Havale ile Satın Al (300 TL)", callback_data="buy_with_iban")],
        [InlineKeyboardButton("📖 Nasıl Satın Alınır?", callback_data="how_to_buy")],
        [InlineKeyboardButton("📞 Destek İletişim", url="https://t.me/SMSPATRONUM")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 *HOŞ GELDİNİZ — ELİT VIP ARŞİV*\n\n"
        "✨ Tamamen özel ve gizli içeriklerin bulunduğu VIP kanallarımıza dilediğiniz ödeme yöntemiyle anında erişim sağlayın.\n\n"
        "👇 Aşağıdaki menüden işlem yapabilirsiniz:"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "buy_with_stars":
        title = "Elit VIP Arşiv Erişimi"
        description = "5 Özel VIP Kanalına Sınırsız ve Anında Erişim Linkleri"
        payload = "vip_archive_payload"
        currency = "XTR"
        prices = [LabeledPrice("VIP Erişim", PRICE_STARS)]

        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency=currency,
            prices=prices,
            start_parameter="vip-sub"
        )

    elif data == "buy_with_iban":
        text = (
            f"💎 *VIP ÜYELİK ÖDEME EKRANI (IBAN)*\n\n"
            f"📦 Paket: *Elit VIP Sınırsız Erişim*\n"
            f"💰 Tutar: *{PRICE_TL}*\n\n"
            f"💳 *Banka Bilgileri (HAVALE / EFT / FAST)*\n"
            f"IBAN:\n`{IBAN}`\n\n"
            f"Alıcı Adı: *{RECIPIENT}*\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"1️⃣ Yukarıdaki IBAN adresine tam *{PRICE_TL}* gönderin.\n"
            "2️⃣ İşlem sonrası banka dekontunun ekran görüntüsünü veya PDF dosyasını doğrudan bu bota gönderin.\n"
            "3️⃣ Sistem dekontu algıladığı anda VIP linkleriniz anında otomatik olarak iletilecektir!"
        )
        keyboard = [
            [InlineKeyboardButton("⬅️ Ana Menüye Dön", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "how_to_buy":
        text = (
            "📖 *NASIL SATIN ALINIR? (REHBER)*\n\n"
            "Botumuz üzerinden VIP arşiv linklerine sahip olmak son derece kolaydır:\n\n"
            "⭐ **Telegram Yıldızı ile:** Butona tıkladığınızda açılan güvenli Telegram penceresinden yıldız göndererek **anında ve bekletmeden** linkleri alabilirsiniz.\n\n"
            "💳 **IBAN ile:** Belirtilen IBAN'a 300 TL havale yaptıktan sonra dekontu bota fotoğraf olarak atarsınız, onay sonrası linkleriniz verilir.\n\n"
            "⚠️ *Herhangi bir sorun yaşarsanız destek butonundan bize ulaşabilirsiniz.*"
        )
        keyboard = [
            [InlineKeyboardButton("⬅️ Ana Menüye Dön", callback_data="home")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "home":
        text = (
            "🔥 *HOŞ GELDİNİZ — ELİT VIP ARŞİV*\n\n"
            "✨ Tamamen özel ve gizli içeriklerin bulunduğu VIP kanallarımıza dilediğiniz ödeme yöntemiyle anında erişim sağlayın.\n\n"
            "👇 Aşağıdaki menüden işlem yapabilirsiniz:"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload == "vip_archive_payload":
        await query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    if payment.invoice_payload == "vip_archive_payload":
        links_text = "\n".join([f"🔗 {link}" for link in VIP_LINKS])
        text = (
            "⭐ *ÖDEMENİZ BAŞARIYLA ALINDI! (TELEGRAM STARS)*\n\n"
            "🎉 Tebrikler! VIP arşivlerimize anında erişim hakkı kazandınız. Özel davet linkleriniz:\n\n"
            f"{links_text}\n\n"
            "⚠️ *Bu linkler kişiye özeldir, lütfen başka kimseyle paylaşmayın.*"
        )
        keyboard = [
            [InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="home")]
        ]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def receipt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo or update.message.document:
        links_text = "\n".join([f"🔗 {link}" for link in VIP_LINKS])
        
        text = (
            "✅ *DEKONT ONAYLANDI! ÖDEMENİZ BAŞARIYLA ALINDI.*\n\n"
            "🎉 Tebrikler! VIP arşivlerimize erişim hakkı kazandınız. Aşağıdaki gizli davet linklerine tıklayarak kanallara hemen katılabilirsiniz:\n\n"
            f"{links_text}\n\n"
            "⚠️ *Bu linkler kişiye özeldir, lütfen başka kimseyle paylaşmayın.*"
        )
        keyboard = [
            [InlineKeyboardButton("🏠 Ana Menüye Dön", callback_data="home")]
        ]
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    await update.message.reply_text("📸 Lütfen geçerli bir dekont ekran görüntüsü veya dosyası gönderin.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receipt_handler))
    
    print("VIP IBAN ve Yıldız Ödeme Botu Tamamen Hazır!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
