import telebot
import requests
from deep_translator import GoogleTranslator

TOKEN = '8535450457:AAFK-85dZ1Ryoabxi-vv2Ku6ZtEVymnSGoM'
WEATHER_API_KEY = 'a3a26201652c8ba68bf778e269944388'

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Menga biror shahar nomini yuboring, men ob-havosini aytaman")

@bot.message_handler(func=lambda message: True)
def weather_info(message):
    city = message.text
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=uz"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        translated = GoogleTranslator(source='en', target='uz').translate(desc)
        bot.reply_to(message, f"{city}da hozir {temp}°C, {translated}")
    else:
        bot.reply_to(message, "Bu shahar topilmadi. Iltimos, qaytadan urinib ko‘ring.")

bot.polling()