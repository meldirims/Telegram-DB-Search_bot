import sqlite3
import re
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


  #location for DataBase
DB_PATHS = [
    r"D:\TestFolder\DataBase.db",
    r"D:\TestFolder\DataBase.db"
]

#جایگزینی یوزرنیم چنل جوین اجباری
CHANNEL_USERNAME = "channel ID without @"

def fix_encoding(s):
    try:
        return s.encode('latin1').decode('windows-1256')
    except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
        return s if s else ""

def search_in_db(query: str):
    for db_path in DB_PATHS:
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            sql = """
            SELECT FULL_NAME, NATIONAL_CODE, BIRTH_DATE, MOBILE, CARD_NO
            FROM bank_data
            WHERE NATIONAL_CODE = ? OR MOBILE = ?
            LIMIT 1
            """
            cursor.execute(sql, (query, query))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "FULL_NAME": fix_encoding(row["FULL_NAME"]),
                    "NATIONAL_CODE": fix_encoding(row["NATIONAL_CODE"]),
                    "BIRTH_DATE": fix_encoding(row["BIRTH_DATE"]),
                    "MOBILE": fix_encoding(row["MOBILE"]),
                    "CARD_NO": fix_encoding(row["CARD_NO"])
                }
        except Exception as e:
            print(f"❌ Database error in {db_path}: {e}", flush=True)

    return None

async def is_user_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=update.effective_user.id)
        print(f"[DEBUG] User status: {member.status}", flush=True)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"[ERROR] Checking membership failed: {e}", flush=True)
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🔍 در این ربات می‌تونی با ارسال یکی از موارد زیر، داده‌ها رو جست‌وجو کنی:\n\n"
        "📱  شماره تلفن همراه\n"
        "مثال: 09123456789\n\n"
        "‏🆔 کد ملی (۱۰ رقمی)\n"
        "مثال: 1234567890"
    )
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    user_id = update.effective_user.id
    print(f"MSG_FROM:{user_id}:{query}", flush=True)  # This line for GUI log

    if not await is_user_member(update, context):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join ********* Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]
        ])
        await update.message.reply_text(
            "❗ You must join our channel to use the bot.",
            reply_markup=keyboard
        )
        return

    if not re.fullmatch(r"\d{8,11}", query):
        await update.message.reply_text("❌ لطفاً یک کد ملی یا شماره تلفن همراه معتبر وارد کنید.")
        return

    start_time = time.perf_counter()
    result = search_in_db(query)
    elapsed_time = time.perf_counter() - start_time

    if result:
        msg = (
            
        "🪪 <b>اطلاعات فردی:</b>\n\n"
        f"🆔 <b>کد ملی:</b>\n<code>{result['NATIONAL_CODE']}</code>\n——————\n"
        f"👤 <b>نام:</b> {result['FULL_NAME']}\n——————\n"
        f"📅 <b>تاریخ تولد:</b>\n<code>{result['BIRTH_DATE']}</code>\n——————\n"
        f"☎️ <b>شماره تلفن:</b>\n<code>{result['MOBILE']}</code>\n——————\n"
        f"💳 <b>شماره کارت:</b>\n<code>{result['CARD_NO']}</code>\n——————\n"
        f"⏳ <b>زمان پردازش:</b> <code>{elapsed_time:.5f} ثانیه</code>"
    
        )
        await update.message.reply_html(msg)
    else:
        await update.message.reply_text("❌ اطلاعاتی یافت نشد.\n\nاز درست وارد کردن شماره اطمینان حاصل فرمایید.\nبدون +98\n\n📱 شماره تلفن همراه\nمثال: 09123456789\n\n‏🆔  کد ملی (۱۰ رقمی)\nمثال: 1234567890")


if __name__ == "__main__":
    TOKEN = "BotToken"  # <-- جایگزین کن با توکن ربات خودت

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is running...", flush=True)
    app.run_polling()
