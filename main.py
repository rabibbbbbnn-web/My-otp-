import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, get_user, add_user, update_balance, get_setting
from voltex_api import get_sms_number, check_sms

# লোগিং সেটআপ
logging.basicConfig(level=logging.INFO)

# বট এবং ডিসপাচার ইনিশিয়ালাইজেশন
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    
    # ডেটাবেজে ইউজার যোগ করা
    add_user(user_id, username)
    
    welcome_text = (
        f"স্বাগতম {message.from_user.first_name}!\n\n"
        "এটি আপনার ওটিপি (OTP) বট। এখান থেকে আপনি খুব সহজেই বিভিন্ন সার্ভিসের জন্য নম্বর নিতে পারবেন।"
    )
    await message.answer(welcome_text)

@dp.message(Command("balance"))
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if user:
        balance = user[2] # balance field index
        await message.answer(f"আপনার বর্তমান ব্যালেন্স: ৳{balance}")
    else:
        await message.answer("আগে /start কমান্ডটি ব্যবহার করুন।")

async def main():
    # ডেটাবেজ টেবিল তৈরি
    init_db()
    print("বট চালু হচ্ছে...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
