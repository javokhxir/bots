import telebot
import qrcode
from io import BytesIO

# Bot tokeningizni shu yerga yozing
TOKEN = "8513444180:AAGHs0P-Lm9xNY6VoUoQaWUBZs9Rf0Bfvf0"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Salom! QR kod yaratish uchun menga biror matn yuboring.")

@bot.message_handler(func=lambda message: True)
def generate_qr(message):
    text = message.text
    
    # QR kod yaratish
    qr_img = qrcode.make(text)
    
    # QR kodni xotirada saqlash
    img_io = BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)

    # QR kodni foydalanuvchiga yuborish
    bot.send_photo(message.chat.id, img_io, caption="Mana sizning QR kodingiz!")

bot.polling()
