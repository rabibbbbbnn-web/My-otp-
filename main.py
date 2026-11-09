import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- কনফিগারেশন ---
BOT_TOKEN = "9253034191:AAHsd5owP2cIlbma3BMsSraw0fM0u50q69o"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ডাটাবেস সেটআপ ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            referrals INTEGER DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('api_key', 'YOUR_API_KEY_HERE')")
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('bot_status', 'active')")
    conn.commit()
    conn.close()

init_db()

def get_db_setting(key, default=""):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_db_setting(key, value):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user_data(user_id: int):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, referrals FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row
    else:
        cursor.execute("INSERT INTO users (user_id, balance, referrals) VALUES (?, ?, ?)", (user_id, 0.0, 0))
        conn.commit()
        conn.close()
        return (0.0, 0)

# --- মূল রিপ্লাই কিবোর্ড (নিচে স্থায়ী বাটন) ---
def main_reply_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Get Number"), KeyboardButton(text="📊 Live Traffic")],
            [KeyboardButton(text="👤 Wallet"), KeyboardButton(text="👥 Refer & Earn")],
            [KeyboardButton(text="🔐 Get 2FA")]
        ],
        resize_keyboard=True,
        persistent=True
    )

# --- /start কমান্ড ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    get_user_data(user_id)
    await message.answer(
        f"স্বাগতম {message.from_user.first_name}!\n"
        f"এটি আপনার প্রফেশনাল ওটিপি (OTP) বট। নিচের বাটনগুলো ব্যবহার করে সেবা গ্রহণ করুন:",
        reply_markup=main_reply_keyboard()
    )

# --- প্যানেল থেকে নাম্বার আনার ফাংশন ---
async def fetch_number_from_panel(service_name):
    api_key = get_db_setting("api_key")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        return "⚠️ ত্রুটি: অ্যাডমিন প্যানেল থেকে কোনো বৈধ API Key সেট করা হয়নি।"
    
    url = f"https://api.voltex.uz/v1/number?api_key={api_key}&service={service_name}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    phone = data.get("number", "N/A")
                    order_id = data.get("id", "N/A")
                    return f"✅ **{service_name} Number Generated:**\n📞 Number: `{phone}`\n🆔 Order ID: `{order_id}`\n⏳ Waiting for SMS..."
                else:
                    return f"❌ প্যানেল থেকে নাম্বার আনতে ব্যর্থ (Error: {response.status})"
    except Exception as e:
        return f"🚨 API কানেকশনে সমস্যা হয়েছে: {str(e)}"

# --- প্রধান বাটন হ্যান্ডলার ---
@dp.message(F.text == "📥 Get Number")
async def btn_get_number(message: types.Message):
    services_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📘 Facebook", callback_data="srv_facebook"),
         InlineKeyboardButton(text="📸 Instagram", callback_data="srv_instagram")],
        [InlineKeyboardButton(text="✈️ Telegram", callback_data="srv_telegram"),
         InlineKeyboardButton(text="💬 WhatsApp", callback_data="srv_whatsapp")]
    ])
    await message.reply("দয়া করে কাঙ্ক্ষিত সার্ভিসটি সিলেক্ট করুন:", reply_markup=services_kb)

@dp.callback_query(F.data.startswith("srv_"))
async def cb_select_service(callback: types.CallbackQuery):
    service = callback.data.split("_")[1].lower()
    await callback.message.edit_text("🔄 প্যানেল থেকে নাম্বার রিকোয়েস্ট পাঠানো হচ্ছে...")
    result_message = await fetch_number_from_panel(service)
    await callback.message.edit_text(result_message, parse_mode="Markdown")
    await callback.answer()

@dp.message(F.text == "📊 Live Traffic")
async def btn_live_traffic(message: types.Message):
    traffic_text = (
        "🟢 **Live Traffic Status**:\n\n"
        "• 🇧🇩 Bangladesh: High Load 🔥\n"
        "• 🇮🇳 India: Normal ⚡\n"
        "• 🇵🇰 Pakistan: High Load 🔥\n"
        "• 🇺🇸 USA: Available 🟢"
    )
    await message.reply(traffic_text, parse_mode="Markdown")

@dp.message(F.text == "👤 Wallet")
async def btn_wallet(message: types.Message):
    balance, _ = get_user_data(message.from_user.id)
    wallet_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Deposit", callback_data="dep_money"),
         InlineKeyboardButton(text="💳 Withdraw", callback_data="wdr_money")]
    ])
    await message.reply(f"💼 **Your Wallet**:\n\n💰 বর্তমান ব্যালেন্স: ৳{balance}", reply_markup=wallet_kb, parse_mode="Markdown")

@dp.message(F.text == "👥 Refer & Earn")
async def btn_refer(message: types.Message):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.reply(f"🔗 **Referral System**:\n\nআপনার রেফারেল লিংক:\n`{ref_link}`\nপ্রতি রেফারে ১০ টাকা বোনাস পান!", parse_mode="Markdown")

@dp.message(F.text == "🔐 Get 2FA")
async def btn_2fa(message: types.Message):
    await message.reply("দয়া করে আপনার ফেসবুক বা ইনস্টাগ্রামের 2FA কি (Key) প্রদান করুন:")

# --- অ্যাডমিন প্যানেল ও এপিআই সেটআপ ---
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    current_key = get_db_setting("api_key")
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Set API Key", callback_data="adm_set_api")],
        [InlineKeyboardButton(text="📊 Check API Status", callback_data="adm_check_api")]
    ])
    await message.reply(f"👑 **Admin Panel**\n\nবর্তমান API Key: `{current_key}`", reply_markup=admin_kb, parse_mode="Markdown")

@dp.callback_query(F.data == "adm_set_api")
async def cb_set_api(callback: types.CallbackQuery):
    await callback.message.edit_text("দয়া করে আপনার নতুন API Key টি এইমাত্র চ্যাটে লিখে পাঠান:")
    await callback.answer()

@dp.callback_query(F.data == "adm_check_api")
async def cb_check_api(callback: types.CallbackQuery):
    current_key = get_db_setting("api_key")
    if current_key == "YOUR_API_KEY_HERE" or not current_key:
        await callback.message.answer("⚠️ কোনো সঠিক API সেট করা নেই।")
    else:
        await callback.message.answer(f"✅ API Key সক্রিয় আছে: `{current_key[:10]}...`", parse_mode="Markdown")
    await callback.answer()

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_inputs(message: types.Message):
    if len(message.text) > 15 and " " not in message.text:
        set_db_setting("api_key", message.text.strip())
        await message.reply(f"✅ সফলভাবে নতুন API Key সেভ করা হয়েছে:\n`{message.text.strip()}`", parse_mode="Markdown")

# --- Render ওয়েব সার্ভার ---
async def handle_ping(request):
    return web.Response(text="Bot is running successfully!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- মেইন রান ফাংশন ---
async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
