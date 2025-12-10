
import os
import asyncio
import sqlite3
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = ("8585551282:AAEE5P85TiMIr586hdKM3JrKDxNuGUT_Srk")
ADMIN_ID = 5933151058
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
import sqlite3
conn = sqlite3.connect("kino_final.db")
cur = conn.cursor()
# 🔹 Foydalanuvchilar jadvali - join_date qo'shildi
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    username TEXT,
    viewed INTEGER DEFAULT 0,
    join_date DATE DEFAULT (date('now'))
)
""")
# 🔹 Kinolar jadvali
cur.execute("""
CREATE TABLE IF NOT EXISTS films(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    file_id TEXT,
    code TEXT UNIQUE,
    views INTEGER DEFAULT 0
)
""")
# 🔹 Majburiy obuna kanallari jadvali
cur.execute("""
CREATE TABLE IF NOT EXISTS channels(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE,
    title TEXT,
    join_url TEXT
)
""")

# 🟢 YANGI JADVAL: Vaqtinchalik tasdiqlangan (request yuborgan) foydalanuvchilar
cur.execute("""
CREATE TABLE IF NOT EXISTS temp_approved_subs(
    user_id INTEGER,
    chat_id INTEGER,
    PRIMARY KEY (user_id, chat_id)
)
""")

conn.commit()


# --- KEYBOARDLAR ---
def admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Kino qo'shish")],
            [KeyboardButton(text="📂 Kinolar ro'yxati")],
            [KeyboardButton(text="🗑 Kino o‘chirish")],
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Majburiy obuna kanallari")],
            [KeyboardButton(text="📤 Barchaga xabar yuborish")]  # Yangi tugma qo'shildi
        ],
        resize_keyboard=True
    )
def user_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎞 Kino kodi yuborish")]],
        resize_keyboard=True
    )
def channel_manage_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Orqaga")]],
        resize_keyboard=True
    )
# --- HOLAT SAQLASH ---
state = {}
# --- 🟢 O'ZGARTIRILGAN MAJBURIY OBUNA TEKSHIRISH FUNKSIYASI ---
async def check_subscription(user_id):
    channels = cur.execute("SELECT chat_id, title, join_url FROM channels").fetchall()
    not_joined = []
    
    for chat_id, title, join_url in channels:
        is_joined = False
        
        # 1. Rasmiy a'zoligini tekshirish
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ["member", "restricted", "administrator", "creator"]:
                is_joined = True
        except Exception as e:
            # Agar bot user_id ni topa olmasa (u a'zo bo'lmasa) bu yerdan o'tadi
            pass

        # 2. Agar rasmiy a'zo bo'lmasa, vaqtinchalik tasdiqlanganlar (request yuborganlar) bazasini tekshirish
        if not is_joined:
            temp_approved = cur.execute("SELECT 1 FROM temp_approved_subs WHERE user_id = ? AND chat_id = ?", (user_id, chat_id,)).fetchone()
            if temp_approved:
                is_joined = True
        
        # Agar hali ham obuna bo'lmagan bo'lsa (va vaqtinchalik tasdiqlanmagan bo'lsa)
        if not is_joined:
            not_joined.append((title, join_url))
            
    return not_joined

def join_keyboard(not_joined):
    buttons = []
    for title, url in not_joined:
        buttons.append([InlineKeyboardButton(text=f"📢 {title} ga obuna bo‘lish", url=url)])
    buttons.append([InlineKeyboardButton(text="✅ Obuna bo‘ldim", callback_data="check_subs")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- CALLBACK: OBUNA TEKSHIRISH ---
@dp.callback_query(lambda c: c.data == "check_subs")
async def check_subs_again(callback: types.CallbackQuery):
    not_joined = await check_subscription(callback.from_user.id)
    if not_joined:
        kb = join_keyboard(not_joined)
        await callback.message.edit_text("❗ Siz hali ham quyidagi kanallarga obuna bo‘lmadingiz:", reply_markup=kb)
    else:
        await callback.message.edit_text("✅ Rahmat! Endi kodni yuborishingiz mumkin.")
        await bot.send_message(callback.from_user.id, "🎟 Endi kino kodini yuboring:", reply_markup=user_kb())
# --- 🟢 O'ZGARTIRILGAN JOIN REQUEST HANDLER ---
@dp.chat_join_request()
async def track_join_request(request: types.ChatJoinRequest):
    chat_id = request.chat.id
    user_id = request.from_user.id
    
    # Faqat bizning majburiy obuna ro'yxatimizdagi kanallar uchun amal qiladi
    exists = cur.execute("SELECT 1 FROM channels WHERE chat_id = ?", (chat_id,)).fetchone()
    
    if exists:
        # request.approve() ni chaqirmaymiz!
        
        # Foydalanuvchini vaqtinchalik tasdiqlanganlar ro'yxatiga (bazaga) qo'shamiz
        cur.execute("INSERT OR IGNORE INTO temp_approved_subs(user_id, chat_id) VALUES(?, ?)", (user_id, chat_id,))
        conn.commit()
        
        logging.info(f"Join request received from {user_id} for channel {chat_id}. NOT approved, but temporarily recorded.")
        # Bu yerda requestni o'z holida qoldiramiz (Pending).
# --- ADMIN PANEL: MAJBURIY OBUNA ---
@dp.message(lambda m: m.text == "📢 Majburiy obuna kanallari" and m.from_user.id == ADMIN_ID)
async def manage_channels(msg: types.Message):
    rows = cur.execute("SELECT id, title, join_url FROM channels").fetchall()
    txt = "📢 Hozirgi kanallar:\n" + "\n".join([f"{r[0]}. {r[1]} - {r[2]}" for r in rows]) if rows else "📭 Hozircha kanal yo‘q."
    await msg.answer(txt + "\n\n➕ Yangi kanal qo‘shish uchun kanal/guruhdan biror xabarni forward qiling.\n❌ O‘chirish uchun /del ID yuboring (ID ro'yxatda ko'rsatilgan).", reply_markup=channel_manage_kb())
    state[msg.from_user.id] = {"step": "manage_channels"}
@dp.message(lambda m: state.get(m.from_user.id, {}).get("step") == "manage_channels" and m.from_user.id == ADMIN_ID)
async def add_or_delete_channel(msg: types.Message):
    text = msg.text.strip() if msg.text else None
    if text == "⬅️ Orqaga":
        state.pop(msg.from_user.id, None)
        await msg.answer("🔙 Orqaga qaytdingiz.", reply_markup=admin_kb())
        return
    if text and text.startswith("/del"):
        try:
            del_id = int(text.replace("/del", "").strip())
            cur.execute("DELETE FROM channels WHERE id = ?", (del_id,))
            conn.commit()
            await msg.answer(f"❌ Kanal o‘chirildi (ID: {del_id}).")
        except ValueError:
            await msg.answer("⚠️ /del ID formatida yuboring, ID raqam bo'lishi kerak.")
        return
    if msg.forward_from_chat:
        chat = msg.forward_from_chat
        chat_id = chat.id
        title = chat.title
        join_url = None
        if chat.username:
            join_url = f"https://t.me/{chat.username}"
        else:
            state[msg.from_user.id]["step"] = "invite_link"
            state[msg.from_user.id]["chat_id"] = chat_id
            state[msg.from_user.id]["title"] = title
            await msg.answer("⚠️ Bu private kanal/guruh. Endi invite linkini yuboring[](https://t.me/+...):")
            return
        cur.execute("INSERT OR IGNORE INTO channels(chat_id, title, join_url) VALUES(?, ?, ?)", (chat_id, title, join_url))
        conn.commit()
        await msg.answer(f"✅ Kanal qo‘shildi: {title} ({join_url})")
    else:
        await msg.answer("⚠️ Kanal/guruhdan xabar forward qiling yoki /del ID yuboring.")
@dp.message(lambda m: state.get(m.from_user.id, {}).get("step") == "invite_link" and m.from_user.id == ADMIN_ID)
async def get_invite_link(msg: types.Message):
    join_url = msg.text.strip()
    if not (join_url.startswith("https://t.me/+") or join_url.startswith("https://t.me/joinchat/")):
        await msg.answer("⚠️ Invite link https://t.me/+ yoki https://t.me/joinchat/ bilan boshlanishi kerak.")
        return
    chat_id = state[msg.from_user.id]["chat_id"]
    title = state[msg.from_user.id]["title"]
    cur.execute("INSERT OR IGNORE INTO channels(chat_id, title, join_url) VALUES(?, ?, ?)", (chat_id, title, join_url))
    conn.commit()
    state[msg.from_user.id]["step"] = "manage_channels"
    await msg.answer(f"✅ Kanal qo‘shildi: {title} ({join_url})")
# --- YANGI: BARCHAGA XABAR YUBORISH ---
@dp.message(lambda m: m.text == "📤 Barchaga xabar yuborish" and m.from_user.id == ADMIN_ID)
async def broadcast_start(msg: types.Message):
    state[msg.from_user.id] = {"step": "broadcast_text"}
    await msg.answer("📤 Barchaga yubormoqchi bo'lgan xabaringizni yuboring (matn, rasm, video yoki hujjat bo'lishi mumkin):\n\nYuborganingizdan keyin avtomatik barchaga jo'natiladi.", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="❌ Bekor qilish")]], resize_keyboard=True))
@dp.message(lambda m: state.get(m.from_user.id, {}).get("step") == "broadcast_text" and m.from_user.id == ADMIN_ID)
async def broadcast_process(msg: types.Message):
    text = msg.text.strip()
    if text == "❌ Bekor qilish":
        state.pop(msg.from_user.id, None)
        await msg.answer("❌ Bekor qilindi.", reply_markup=admin_kb())
        return
    state.pop(msg.from_user.id, None)
    # Barcha user_id larni olish
    users = cur.execute("SELECT user_id FROM users").fetchall()
    total = len(users)
    success_count = 0
    await msg.answer(f"📤 Xabar yuborilmoqda... Jami {total} ta foydalanuvchi.")
    for (user_id,) in users:
        try:
            if msg.text:
                await bot.send_message(user_id, text)
            elif msg.photo:
                await bot.send_photo(user_id, msg.photo[-1].file_id, caption=msg.caption or "")
            elif msg.video:
                await bot.send_video(user_id, msg.video.file_id, caption=msg.caption or "")
            elif msg.document:
                await bot.send_document(user_id, msg.document.file_id, caption=msg.caption or "")
            else:
                await bot.send_message(user_id, "📤 Xabar yuborildi!")
            success_count += 1
            await asyncio.sleep(0.05)  # Telegram limit: 30 msg/sek
        except Exception as e:
            logging.warning(f"Xabar yuborishda xato {user_id}: {e}")
    await msg.answer(f"✅ Xabar yuborildi! Muvaffaqiyatli: {success_count}/{total}")
    await bot.send_message(ADMIN_ID, f"📤 Broadcast tugadi: {success_count}/{total} ta xabar yuborildi.")
# --- ADMIN: STATISTIKA ---
@dp.message(lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
async def show_stats(msg: types.Message):
    users_count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    films_count = cur.execute("SELECT COUNT(*) FROM films").fetchone()[0]
    total_views = cur.execute("SELECT SUM(views) FROM films").fetchone()[0] or 0
    today_joins = cur.execute("SELECT COUNT(*) FROM users WHERE join_date = date('now')").fetchone()[0]
    blocked_count = cur.execute("SELECT COUNT(*) FROM users WHERE user_id < 0").fetchone()[0]  # Bloklanganlar (negative ID)
    await msg.answer(f"📊 <b>Statistika</b>\n\n"
                     f"👥 Foydalanuvchilar: <b>{users_count}</b>\n"
                     f"🆕 Bugun qo'shilganlar: <b>{today_joins}</b>\n"
                     f"🚫 Bloklanganlar: <b>{blocked_count}</b>\n"
                     f"🎬 Kinolar: <b>{films_count}</b>\n"
                     f"📺 Jami ko‘rilgan: <b>{total_views}</b> marta", parse_mode="HTML")
# --- ADMIN: KINO QO‘SHISH ---
@dp.message(lambda m: m.text == "🎬 Kino qo'shish" and m.from_user.id == ADMIN_ID)
async def add_movie_start(msg: types.Message):
    state[msg.from_user.id] = {"step": "title"}
    await msg.answer("🎬 Kino nomini yuboring:")
@dp.message(lambda m: state.get(m.from_user.id, {}).get("step") == "title" and m.from_user.id == ADMIN_ID)
async def get_movie_title(msg: types.Message):
    state[msg.from_user.id] = {"step": "video", "title": msg.text}
    await msg.answer("🎥 Endi kinoning videosini yuboring:")
@dp.message(lambda m: m.video and state.get(m.from_user.id, {}).get("step") == "video" and m.from_user.id == ADMIN_ID)
async def get_movie_video(msg: types.Message):
    state[msg.from_user.id]["file_id"] = msg.video.file_id
    state[msg.from_user.id]["step"] = "code"
    await msg.answer("📟 Endi kinoga kod kiriting:")
@dp.message(lambda m: state.get(m.from_user.id, {}).get("step") == "code" and m.from_user.id == ADMIN_ID)
async def get_movie_code(msg: types.Message):
    title = state[msg.from_user.id]["title"]
    file_id = state[msg.from_user.id]["file_id"]
    code = msg.text.strip()
    existing = cur.execute("SELECT 1 FROM films WHERE code = ?", (code,)).fetchone()
    if existing:
        await msg.answer("❌ Bu kod avvaldan mavjud, boshqa kod kiriting.")
        return
    cur.execute("INSERT INTO films(title, file_id, code) VALUES(?, ?, ?)", (title, file_id, code))
    conn.commit()
    state.pop(msg.from_user.id, None)
    await msg.answer(f"✅ Kino saqlandi!\n🎞 Nomi: {title}\n📟 Kodi: {code}", reply_markup=admin_kb())
# --- KINO O‘CHIRISH ---
@dp.message(lambda m: m.text == "🗑 Kino o‘chirish" and m.from_user.id == ADMIN_ID)
async def delete_movie_start(msg: types.Message):
    state[msg.from_user.id] = {"step": "delete"}
    await msg.answer("🗑 O‘chirmoqchi bo‘lgan kino kodini yuboring:")
@dp.message(lambda m: state.get(m.from_user.id, {}).get("step") == "delete" and m.from_user.id == ADMIN_ID)
async def delete_movie_process(msg: types.Message):
    code = msg.text.strip()
    row = cur.execute("SELECT title FROM films WHERE code = ?", (code,)).fetchone()
    if not row:
        await msg.answer("❌ Bunday kodli kino topilmadi.")
    else:
        cur.execute("DELETE FROM films WHERE code = ?", (code,))
        conn.commit()
        await msg.answer(f"✅ '{row[0]}' kodi {code} bo‘lgan kino o‘chirildi.", reply_markup=admin_kb())
    state.pop(msg.from_user.id, None)
# --- KINOLAR RO‘YXATI ---
@dp.message(lambda m: m.text == "📂 Kinolar ro'yxati" and m.from_user.id == ADMIN_ID)
async def show_list(msg: types.Message):
    rows = cur.execute("SELECT title, code, views FROM films ORDER BY id DESC").fetchall()
    if not rows:
        await msg.answer("🎞 Hozircha kinolar yo‘q.")
    else:
        txt = "\n".join([f"{r[1]} — {r[0]} ({r[2]} marta ko‘rilgan)" for r in rows])
        await msg.answer("🎬 Kinolar ro'yxati:\n" + txt)
# --- FOYDALANUVCHI TOMONI ---
@dp.message(lambda m: m.text == "🎞 Kino kodi yuborish")
async def ask_code(msg: types.Message):
    not_joined = await check_subscription(msg.from_user.id)
    if not_joined:
        kb = join_keyboard(not_joined)
        await msg.answer("📢 Iltimos, quyidagi kanallarga obuna bo‘ling:", reply_markup=kb)
        return
    await msg.answer("🎟 Kino kodini yuboring:")
@dp.message(lambda m: m.text)
async def send_movie(msg: types.Message):
    not_joined = await check_subscription(msg.from_user.id)
    if not_joined:
        kb = join_keyboard(not_joined)
        await msg.answer("📢 Iltimos, quyidagi kanallarga obuna bo‘ling:", reply_markup=kb)
        return
    # 🔹 foydalanuvchini bazaga yozish
    cur.execute("INSERT OR IGNORE INTO users(user_id, username, join_date) VALUES(?, ?, date('now'))", (msg.from_user.id, msg.from_user.username))
    conn.commit()
    code = msg.text.strip()
    row = cur.execute("SELECT title, file_id, views FROM films WHERE code = ?", (code,)).fetchone()
    if not row:
        await msg.answer("📛 Bunday kodli kino topilmadi.")
    else:
        title, file_id, views = row
        cur.execute("UPDATE films SET views = ? WHERE code = ?", (views + 1, code))
        conn.commit()
        await msg.answer_video(file_id, caption=f"🎬 {title}\n📟 Kod: {code}\n👁 {views + 1} marta ko‘rilgan")
# --- RUN ---
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())