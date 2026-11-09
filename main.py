import logging
import sqlite3
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# আপনার বটের টোকেন এবং ভলটেক্স এপিআই কনফিগারেশন
BOT_TOKEN = "825304139:AAHsD5owP2cIlIma3BMSRaw0FMUo5Oq69o"  # Render-এ এনভায়রনমেন্ট ভ্যারিয়েবলেও সেট করা আছে
VOLTEX_API_URL = "https://api.voltex.uz/v1/"  # উদাহরণস্বরূপ ভলটেক্স এপিআই লিংক (আপনার প্রয়োজন অনুযায়ী পরিবর্তন করে নিতে পারেন)
VOLTEX_API_KEY = "YOUR_VOLTEX_API_KEY"       # আপনার ভলটেক্স এপিআই কি এখানে দিন

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

# --- স্টেটমেশিন (FSM) ওপি নেওয়ার জন্য ---
class OrderOTP(StatesGroup):
    waiting_for_service = State()

# --- স্টার্ট কমান্ড ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    get_user_balance(user_id) # ইউজার ডেটাবেসে না থাকলে যুক্ত করবে
    
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

# --- মূল রান ফাংশন ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
