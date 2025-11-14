from google import genai
import telebot

# AI API KEYNI KIRITING
AI_API_KEY="AIzaSyDVjZyZTA-rXB0cCJxV35gsmVTezY5hmhk"

# BOT TOKENNI KIRITING
BOT_TOKEN="8130505107:AAFXUc1Zsu1LpT-xxPPllnp2QE8WILf_Vxs"

client = genai.Client(api_key=AI_API_KEY)
bot = telebot.TeleBot(BOT_TOKEN)

# START BOSILGANDA
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.reply_to(message, "salom, Javohirning AI botiga hush kelibsiz!")


# HAR QANDAY MESSAGE KELGANDA
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=message.text
        )

        if response.text:
            text = response.text.strip()
        else:
            text = "Javob topilmadi."

        bot.reply_to(message, text)

    # XATOLIK YUZ BERGANDA
    except Exception as e:
        bot.reply_to(message, f"xatolik yuz berdi: {e}")

print("Bot ishlavotdi!")

# BOTNI ISHGA TUSHIRISH
bot.polling(none_stop=True)