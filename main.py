import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# কনফিগারেশন
BOT_TOKEN = "825304139:AAHsD5owP2cIlIma3BMSRaw0FMUo5Oq69o"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ডেটাবেস সেটআপ ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user_balance(user_id: int) -> float:
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0.0))
        conn.commit()
        conn.close()
        return 0.0

# --- স্টার্ট কমান্ড ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    get_user_balance(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Get OTP", callback_data="get_otp")],
        [InlineKeyboardButton(text="💰 Balance", callback_data="check_balance")]
    ])
    
    await message.answer(
        f"স্বাগতম MD!\n\nএটি আপনার ওটিপি (OTP) বট। এখান থেকে আপনি খুব সহজেই বিভিন্ন সার্ভিসের জন্য নম্বর নিতে পারবেন।",
        reply_markup=keyboard
    )

# --- ব্যালেন্স চেক কমান্ড ---
@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"আপনার বর্তমান ব্যালেন্স: ৳{balance}")

# --- বাটন কলব্যাক হ্যান্ডলার ---
@dp.callback_query(F.data == "check_balance")
async def callback_balance(callback: types.CallbackQuery):
    balance = get_user_balance(callback.from_user.id)
    await callback.message.answer(f"আপনার বর্তমান ব্যালেন্স: ৳{balance}")
    await callback.answer()

@dp.callback_query(F.data == "get_otp")
async def callback_get_otp(callback: types.CallbackQuery):
    await callback.message.answer("দয়া করে যে সার্ভিসের ওটিপি নিতে চান তার নাম লিখুন (যেমন: Telegram, WhatsApp ইত্যাদি):")
    await callback.answer()

# --- Render পোর্টের চাহিদা মেটাতে ওয়েব সার্ভার ---
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render নিজে থেকে যে পোর্ট অ্যাসাইন করবে, সেটি ব্যবহার করবে অথবা ডিফল্ট ৮০০০ ব্যবহার করবে
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- মূল রান ফাংশন ---
async def main():
    # ওয়েব সার্ভার এবং টেলিগ্রাম পোলিং একসাথে চালু করা হলো
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
