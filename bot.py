
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from datetime import datetime

TOKEN = "8750643424:AAEobsm2dbY0ioFcMcnzWIviFTEG3n3odxI"
OWNER_ID = 6119485226
BOT_USERNAME = "@CashFlowTeams_bot"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================
# KEYBOARDS
# =========================

user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="🦣 Мамонты")],
        [KeyboardButton(text="🎁 Рефералка")],
        [KeyboardButton(text="📅 Дней в тиме"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="💸 Вывод")],
        [KeyboardButton(text="📞 Вызвать админа")]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="➕ Выдать деньги")],
        [KeyboardButton(text="➕ Выдать мамонта")],
        [KeyboardButton(text="📋 Заявки на вывод")],
        [KeyboardButton(text="⬅ Назад")]
    ],
    resize_keyboard=True
)

# =========================
# DATABASE
# =========================

async def init_db():
    async with aiosqlite.connect("team.db") as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT,
        join_date TEXT,
        money INTEGER,
        mammoths INTEGER,
        referrer INTEGER
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS withdrawals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount INTEGER,
        status TEXT
        )
        """)

        await db.commit()

# =========================
# ROLE
# =========================

async def get_role(user_id):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT role FROM users WHERE user_id=?",
            (user_id,)
        )

        data = await cursor.fetchone()

        if data:
            return data[0]

        return None

# =========================
# START + REFERRAL
# =========================

@dp.message(Command("start"))
async def start(message: types.Message):

    args = message.text.split()
    referrer = None

    if len(args) > 1:
        try:
            referrer = int(args[1])
        except:
            referrer = None

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        user = await cursor.fetchone()

        if not user:

            role = "worker"

            if message.from_user.id == OWNER_ID:
                role = "owner"

            await db.execute(
                "INSERT INTO users VALUES(?,?,?,?,?,?,?)",
                (
                    message.from_user.id,
                    message.from_user.username,
                    role,
                    datetime.now().isoformat(),
                    0,
                    0,
                    referrer
                )
            )

            if referrer:
                await db.execute(
                    "UPDATE users SET money = money + 5 WHERE user_id=?",
                    (referrer,)
                )

            await db.commit()

    await message.answer("🔥 Добро пожаловать в тим-бот", reply_markup=user_kb)

# =========================
# PROFILE
# =========================

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT money,mammoths,join_date FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        data = await cursor.fetchone()

    if not data:
        return

    join = datetime.fromisoformat(data[2])
    days = (datetime.now() - join).days

    await message.answer(
f"""
👤 Профиль

💰 Баланс: ${data[0]}
🦣 Мамонты: {data[1]}
📅 Дней в тиме: {days}
"""
    )

# =========================
# BALANCE
# =========================

@dp.message(F.text == "💰 Баланс")
async def balance(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT money FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        data = await cursor.fetchone()

    await message.answer(f"💰 Ваш баланс: ${data[0]}")

# =========================
# MAMMOTHS
# =========================

@dp.message(F.text == "🦣 Мамонты")
async def mammoths(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT mammoths FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        data = await cursor.fetchone()

    await message.answer(f"🦣 Мамонтов: {data[0]}")

# =========================
# REFERRAL
# =========================

@dp.message(F.text == "🎁 Рефералка")
async def ref(message: types.Message):

    link = f"https://t.me/{BOT_USERNAME}?start={message.from_user.id}"

    await message.answer(
f"""
🎁 Твоя реферальная ссылка

{link}

💸 За каждого реферала: $5
"""
    )

# =========================
# TOP
# =========================

@dp.message(F.text == "🏆 Топ")
async def top(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT username,money FROM users ORDER BY money DESC LIMIT 10"
        )

        top = await cursor.fetchall()

    text = "🏆 ТОП ВОРКЕРОВ\n\n"

    for i, user in enumerate(top, 1):

        name = user[0] if user[0] else "Без ника"

        text += f"{i}. {name} — ${user[1]}\n"

    await message.answer(text)

# =========================
# DAYS IN TEAM
# =========================

@dp.message(F.text == "📅 Дней в тиме")
async def days(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT join_date FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        data = await cursor.fetchone()

    join = datetime.fromisoformat(data[0])
    days = (datetime.now() - join).days

    await message.answer(f"📅 Вы в тиме: {days} дней")

# =========================
# WITHDRAW
# =========================

@dp.message(F.text == "💸 Вывод")
async def withdraw(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT money FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        money = await cursor.fetchone()

        if money[0] < 10:
            await message.answer("❌ Минимальный вывод $10")
            return

        await db.execute(
            "INSERT INTO withdrawals(user_id,amount,status) VALUES(?,?,?)",
            (message.from_user.id, money[0], "pending")
        )

        await db.execute(
            "UPDATE users SET money=0 WHERE user_id=?",
            (message.from_user.id,)
        )

        await db.commit()

    await message.answer("✅ Заявка на вывод отправлена")

# =========================
# CALL ADMIN
# =========================

@dp.message(F.text == "📞 Вызвать админа")
async def call_admin(message: types.Message):

    await bot.send_message(
        OWNER_ID,
f"""
📞 Вызов админа

User: @{message.from_user.username}
ID: {message.from_user.id}
"""
    )

    await message.answer("✅ Админ уведомлен")

# =========================
# ADMIN PANEL
# =========================

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):

    role = await get_role(message.from_user.id)

    if role not in ["admin","owner"]:
        return

    await message.answer("⚙ Админ панель", reply_markup=admin_kb)

# =========================
# STATS
# =========================

@dp.message(F.text == "📊 Статистика")
async def stats(message: types.Message):

    role = await get_role(message.from_user.id)

    if role not in ["admin","owner"]:
        return

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT COUNT(*),SUM(money),SUM(mammoths) FROM users"
        )

        data = await cursor.fetchone()

    users = data[0]
    money = data[1] or 0
    mammoths = data[2] or 0

    await message.answer(
f"""
📊 Статистика

👥 Пользователей: {users}
💰 Денег в системе: ${money}
🦣 Мамонтов: {mammoths}
"""
    )

# =========================
# SET ADMIN
# =========================

@dp.message(Command("setadmin"))
async def set_admin(message: types.Message):

    if message.from_user.id != OWNER_ID:
        return

    args = message.text.split()

    if len(args) < 2:
        await message.answer("Использование: /setadmin user_id")
        return

    uid = int(args[1])

    async with aiosqlite.connect("team.db") as db:

        await db.execute(
            "UPDATE users SET role='admin' WHERE user_id=?",
            (uid,)
        )

        await db.commit()

    await message.answer("✅ Админ назначен")

# =========================
# BACK
# =========================

@dp.message(F.text == "⬅ Назад")
async def back(message: types.Message):
    await message.answer("Главное меню", reply_markup=user_kb)

# =========================
# RUN
# =========================

async def main():

    await init_db()

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

