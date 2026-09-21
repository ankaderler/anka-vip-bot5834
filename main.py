import os
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Yapılandırma Bilgileri (Yeni Token Güncellendi)
TOKEN = "8966819189:AAENmHdrI8XxNexWFsaAqyfHZn7kxi0N-CQ"
API_KEY = "osms_47d104feae77186b529f51f0104c5b04abd54947a5a6d2ae"
TARGET_NAME = "Resul Sakal"
IBAN = "TR62 0006 2000 5000 0006 8107 73"

bot = telebot.TeleBot(TOKEN)

# Ülke ve Servis Kodları Sözlüğü (Onaylasms uyumlu)
SERVICES = {
    "tr_wa": {"country": "0", "service": "wa", "name": "🇹🇷 Türkiye - WhatsApp", "price": "150 TL"},
    "tr_tg": {"country": "0", "service": "tg", "name": "🇹🇷 Türkiye - Telegram", "price": "150 TL"},
    "us_wa": {"country": "18", "service": "wa", "name": "🇺🇸 Amerika - WhatsApp", "price": "100 TL"},
    "uk_wa": {"country": "2", "service": "wa", "name": "🇬🇧 İngiltere - WhatsApp", "price": "120 TL"}
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup(row_width=1)
    for key, data in SERVICES.items():
        markup.add(InlineKeyboardButton(f"{data['name']} ({data['price']})", callback_data=key))
    
    bot.send_message(
        message.chat.id, 
        "⭐ **ANKA VIP SERVICES** ⭐\n\n"
        "Seçkin numara onay sistemine hoş geldiniz.\n"
        "Lütfen almak istediğiniz ülke ve servisi aşağıdan seçiniz:", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data_key = call.data
    bot.answer_callback_query(call.id)
    
    if data_key not in SERVICES:
        bot.send_message(call.message.chat.id, "Geçersiz seçim.")
        return
        
    selected = SERVICES[data_key]
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Ödemeyi Yaptım / Dekont Gönder", callback_data=f"pay_{data_key}"))
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"💎 **Seçilen Ürün:** {selected['name']}\n"
             f"💰 **Tutar:** {selected['price']}\n\n"
             f"📌 **Ödeme Bildirimi:**\n"
             f"Alıcı: **{TARGET_NAME}**\n"
             f"IBAN: `{IBAN}`\n\n"
             f"Lütfen yukarıdaki IBAN'a ödemeyi yaptıktan sonra dekontu gönderin veya alttaki butona basın.",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def process_payment(call):
    data_key = call.data.split("_", 1)[1]
    bot.answer_callback_query(call.id, "Ödeme doğrulanıyor ve numara talep ediliyor...")
    
    if data_key not in SERVICES:
        return
        
    s_info = SERVICES[data_key]
    
    try:
        url = f"https://onaylasms.com.tr/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service={s_info['service']}&country={s_info['country']}"
        response = requests.get(url, timeout=15)
        res_text = response.text.strip()
        
        if "ACCESS_NUMBER" in res_text:
            parts = res_text.split(":")
            activation_id = parts[1]
            phone_number = parts[2]
            bot.send_message(
                call.message.chat.id,
                f"🎉 **Ödeme Onaylandı & Numara Alındı!**\n\n"
                f"🌍 **Hizmet:** {s_info['name']}\n"
                f"📞 **Numara:** `+{phone_number}`\n"
                f"🆔 **İşlem ID:** `{activation_id}`",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(
                call.message.chat.id,
                f"⚠️ Numara temin edilemedi. Sağlayıcı yanıtı: `{res_text}`",
                parse_Markdown="Markdown"
            )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ API Bağlantı Hatası: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    text = message.text.strip()
    if TARGET_NAME.lower() in text.lower() or "dekont" in text.lower() or "ödeme" in text.lower():
        bot.reply_to(message, "Dekontunuz algılandı. Lütfen menüden ürün seçimi yaparak işlem yapınız veya /start komutunu kullanın.")
    else:
        bot.reply_to(message, "ANKA VIP SERVICES botunu başlatmak için /start komutunu gönderin.")

if __name__ == "__main__":
    bot.remove_webhook()
    bot.infinity_polling()
