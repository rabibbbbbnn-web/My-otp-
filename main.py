import logging
import sqlite3
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message

# --- কনফিগারেশন ---
BOT_TOKEN = "9253034191:AAHsd5owP2cIlbma3BMsSraw0fM0u50q69o"
ADMIN_IDS = [123456789] # এখানে আপনার টেলিগ্রাম ইউজার আইডি বসাতে পারেন (অ্যাডমিন প্যানেল কন্ট্রোলের জন্য)

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
    conn.commit()
    conn.close()

init_db()

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

# --- ইউজার প্যানেল কিবোর্ড ---
def main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Get Number / OTP", callback_data="get_number"),
         InlineKeyboardButton(text="🔍 Search Number", callback_data="search_number")],
        [InlineKeyboardButton(text="📊 Traffic Status", callback_data="traffic_status"),
         InlineKeyboardButton(text="🔐 2FA Checker", callback_data="two_fa_check")],
        [InlineKeyboardButton(text="👤 My Profile", callback_data="my_profile"),
         InlineKeyboardButton(text="👥 Referral", callback_data="referral")],
        [InlineKeyboardButton(text="👑 Leaderboard", callback_data="leaderboard"),
         InlineKeyboardButton(text="💬 Support", callback_data="support")]
    ])

# --- /start কমান্ড ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    get_user_data(user_id)
    
    await message.answer(
        f"স্বাগতম {message.from_user.first_name}!\n\n"
        f"এটি আপনার প্রফেশনাল ওটিপি (OTP) বট। নিচের মেনু থেকে আপনার প্রয়োজনীয় অপشنটি সিলেক্ট করুন:",
        reply_markup=main_menu_keyboard()
    )

# --- ইউজার ফিচার হ্যান্ডলার ---
@dp.callback_query(F.data == "get_number")
async def cb_get_number(callback: CallbackQuery):
    services_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📘 Facebook", callback_data="srv_facebook"),
         InlineKeyboardButton(text="📸 Instagram", callback_data="srv_instagram")],
        [InlineKeyboardButton(text="✈️ Telegram", callback_data="srv_telegram"),
         InlineKeyboardButton(text="💬 WhatsApp", callback_data="srv_whatsapp")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ])
    await callback.message.edit_text("দয়া করে যেকোনো একটি সার্ভিস সিলেক্ট করুন:", reply_markup=services_kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("srv_"))
async def cb_select_service(callback: CallbackQuery):
    service_name = callback.data.split("_")[1].capitalize()
    await callback.message.edit_text(
        f"🌐 **{service_name}** সার্ভিসের জন্য নম্বর জেনারেট করা হচ্ছে...\n\n"
        f"দয়া করে একটু অপেক্ষা করুন অথবা প্যানেল থেকে নম্বর লোড হওয়া পর্যন্ত অপেক্ষা করুন.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="get_number")]])
    )
    await callback.answer()

@dp.callback_query(F.data == "traffic_status")
async def cb_traffic_status(callback: CallbackQuery):
    text = (
        "📊 **Current Traffic Status**:\n\n"
        "🇨🇲 Cameroon: High Traffic 🔥\n"
        "🇦🇲 Armenia: Medium Traffic ⚡\n"
        "🇧🇯 Benin: Medium Traffic ⚡\n"
        "🇮🇳 India: Low Traffic 📉\n"
        "🇧🇩 Bangladesh (WhatsApp): High Traffic 🔥"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]]))
    await callback.answer()

@dp.callback_query(F.data == "two_fa_check")
async def cb_two_fa(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔐 **2FA Code Checker**:\n\n"
        "আপনার ফেসবুক বা ইনস্টাগ্রামের 2FA কোড বা কি (Key) এখানে প্রদান করুন, সিস্টেম স্বয়ংক্রিয়ভাবে কোড বের করে দিবে।",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]]))
    await callback.answer()

@dp.callback_query(F.data == "my_profile")
async def cb_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance, refs = get_user_data(user_id)
    await callback.message.edit_text(
        f"👤 **Your Profile**:\n\n"
        f"🆔 User ID: `{user_id}`\n"
        f"💰 Balance: ৳{balance}\n"
        f"👥 Total Referrals: {refs}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Withdraw", callback_data="withdraw_money")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "withdraw_money")
async def cb_withdraw(callback: CallbackQuery):
    await callback.message.edit_text(
        "💸 **Withdrawal System**:\n\nআপনার ব্যালেন্স থেকে টাকা তুলতে বিকাশ/নগদ সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="my_profile")]])
    )
    await callback.answer()

@dp.callback_query(F.data == "referral")
async def cb_referral(callback: CallbackQuery):
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    await callback.message.edit_text(
        f"👥 **Referral System**:\n\n"
        f"আপনার রেফারেল লিংক:\n`{ref_link}`\n\nএই লিংকের মাধ্যমে বন্ধুরা জয়েন করলে আপনি বোনাস পাবেন!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]])
    )
    await callback.answer()

@dp.callback_query(F.data == "leaderboard")
async def cb_leaderboard(callback: CallbackQuery):
    await callback.message.edit_text(
        "👑 **Top OTP Receivers (Leaderboard)**:\n\n"
        "১. User***1 - 450 OTPs\n"
        "২. User***2 - 320 OTPs\n"
        "৩. User***3 - 210 OTPs",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]])
    )
    await callback.answer()

@dp.callback_query(F.data == "support")
async def cb_support(callback: CallbackQuery):
    await callback.message.edit_text(
        "💬 **Live Support**:\n\nযেকোনো সমস্যায় অ্যাডমিনের সাথে যোগাযোগ করুন: @Admin_Username",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]])
    )
    await callback.answer()

@dp.callback_query(F.data == "back_home")
async def cb_back_home(callback: CallbackQuery):
    await callback.message.edit_text(
        "স্বাগতম! নিচের মেনু থেকে আপনার প্রয়োজনীয় অপশনটি সিলেক্ট করুন:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

# --- /admin কমান্ড ও প্যানেল ---
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS and len(ADMIN_IDS) > 0:
        # টেস্টিংয়ের জন্য ওপেন রাখা হলো, প্রয়োজনে আইডি চেক করতে পারেন
        pass
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Broadcast Message", callback_data="adm_broadcast"),
         InlineKeyboardButton(text="📊 All Users Info", callback_data="adm_users")],
        [InlineKeyboardButton(text="⚙️ Panel Settings", callback_data="adm_settings"),
         InlineKeyboardButton(text="👑 Leaderboard Control", callback_data="adm_leaderboard")]
    ])
    await message.answer("👑 **Admin Control Panel**:\n\nনিচের অপশনগুলো থেকে ম্যানেজ করুন:", reply_markup=admin_kb)

@dp.callback_query(F.data.startswith("adm_"))
async def cb_admin_panel(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    if action == "broadcast":
        await callback.message.answer("ব্রডকাস্ট করার জন্য মেসেজটি পাঠান।")
    elif action == "users":
        await callback.message.answer("সকল ইউজারের ডাটা ফাইল প্রস্তুত করা হচ্ছে...")
    elif action == "settings":
        await callback.message.answer("প্যানেল এবং এপিআই সেটিংস কনফিগারেশন।")
    elif action == "leaderboard":
        await callback.message.answer("লিডারবোর্ড অন/অফ এবং রিওয়ার্ড সেটিংস।")
    await callback.answer()

# --- Render ওয়েব সার্ভার ---
async def handle_ping(request):
    return web.Response(text="Bot is running smoothly!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- মেইন রান ফাংশন ---
async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
