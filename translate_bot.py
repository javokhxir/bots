import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import langid
from deep_translator import GoogleTranslator


bot = telebot.TeleBot("7370843035:AAEIN0YozZwj7qc9a22SzGJYeAuQ7ArZE7Q")

user_data = {}

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Salom, Hush kelibsiz Javokhirning Translator botiga!")
    lang(message)

@bot.message_handler(commands=["lang"])
def lang(message):    
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("Ingliz", callback_data="en")
    btn2 = InlineKeyboardButton("Xitoy", callback_data="zh")
    btn3 = InlineKeyboardButton("Ispan", callback_data="es")
    btn4 = InlineKeyboardButton("Arab", callback_data="ar")
    btn5 = InlineKeyboardButton("Hind", callback_data="hi")
    btn6 = InlineKeyboardButton("Fransuz", callback_data="fr")
    btn7 = InlineKeyboardButton("Rus", callback_data="ru")
    btn8 = InlineKeyboardButton("Nemis", callback_data="de")
    btn9 = InlineKeyboardButton("Yapon", callback_data="ja")
    btn10 = InlineKeyboardButton("Uzbek", callback_data="uz")
    
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10)
    
    bot.send_message(message.chat.id, "Qaysi tilga tarjima qilish kerak:", reply_markup=markup)
    bot.send_message(message.chat.id, "Tarjima tilini o'zgartirish uchun /lang bosing!")

@bot.callback_query_handler(func=lambda call: True)
def get_lang(call):
    bot.send_message(call.message.chat.id, "Til tanlandi Matnni yuboring!")
    user_data[call.message.chat.id] = call.data

@bot.message_handler(func=lambda message: True)
def send_text(message):
    user_id = message.chat.id
    if user_id not in user_data:
        bot.send_message(user_id, "Iltimos tarjima qilinadigan tilni tanlang!")
    else:
        try:
            translated = GoogleTranslator(target=user_data[user_id]).translate(message.text)
            
            bot.send_message(user_id, f"Tarjimasi:\n{translated}")
        except Exception as e:
            bot.send_message(user_id, f"Xatolik yuz berdi: {e}")

bot.polling()