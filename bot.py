
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from datetime import datetime

TOKEN = "8750643424:AAEobsm2dbY0ioFcMcnzWIviFTEG3n3odxI"
OWNER_ID = 6119485226

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =================
# КНОПКИ
# =================

user_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="💰 Заработок"), KeyboardButton(text="🦣 Мамонты")],
        [KeyboardButton(text="📅 Дней в тиме"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="📞 Вызвать админа")]
    ],
    resize_keyboard=True
)

# =================
# БАЗА ДАННЫХ
# =================

async def init_db():
    async with aiosqlite.connect("team.db") as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT,
        join_date TEXT,
        money INTEGER,
        mammoths INTEGER
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        amount INTEGER,
        date TEXT
        )
        """)

        await db.commit()

# =================
# СТАРТ
# =================

@dp.message(Command("start"))
async def start(message: types.Message):

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
                "INSERT INTO users VALUES(?,?,?,?,?,?)",
                (
                    message.from_user.id,
                    message.from_user.username,
                    role,
                    datetime.now().isoformat(),
                    0,
                    0
                )
            )

            await db.commit()

    await message.answer("🔥 Добро пожаловать", reply_markup=user_kb)

# =================
# РОЛЬ
# =================

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

# =================
# ПРОФИЛЬ
# =================

@dp.message(lambda m: m.text == "👤 Профиль")
async def profile(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT money,mammoths,join_date FROM users WHERE user_id=?",
            (message.from_user.id,)
        )

        data = await cursor.fetchone()

    if not data:
        await message.answer("Пользователь не найден")
        return

    join = datetime.fromisoformat(data[2])
    days = (datetime.now() - join).days

    await message.answer(f"""
👤 Профиль

💰 Деньги: ${data[0]}
🦣 Мамонты: {data[1]}
📅 Дней в тиме: {days}
""")

# =================
# ТОП
# =================

@dp.message(lambda m: m.text == "🏆 Топ")
async def top(message: types.Message):

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT username,money FROM users ORDER BY money DESC LIMIT 10"
        )

        top = await cursor.fetchall()

    text = "🏆 ТОП воркеров\n\n"

    for i, user in enumerate(top, 1):
        name = user[0] if user[0] else "Без ника"
        text += f"{i}. {name} — ${user[1]}\n"

    await message.answer(text)

# =================
# ДОБАВИТЬ ДЕНЬГИ
# =================

@dp.message(Command("addmoney"))
async def add_money(message: types.Message):

    role = await get_role(message.from_user.id)

    if role not in ["admin", "owner"]:
        return

    args = message.text.split()

    if len(args) < 3:
        await message.answer("Использование: /addmoney user_id сумма")
        return

    uid = int(args[1])
    amount = int(args[2])

    async with aiosqlite.connect("team.db") as db:

        await db.execute(
            "UPDATE users SET money=money+? WHERE user_id=?",
            (amount, uid)
        )

        await db.execute(
            "INSERT INTO logs(user_id,action,amount,date) VALUES(?,?,?,?)",
            (uid, "add_money", amount, datetime.now().isoformat())
        )

        await db.commit()

    await message.answer("💰 Деньги добавлены")

# =================
# ДОБАВИТЬ МАМОНТА
# =================

@dp.message(Command("addmammoth"))
async def add_mammoth(message: types.Message):

    role = await get_role(message.from_user.id)

    if role not in ["admin", "owner"]:
        return

    args = message.text.split()

    if len(args) < 2:
        await message.answer("Использование: /addmammoth user_id")
        return

    uid = int(args[1])

    async with aiosqlite.connect("team.db") as db:

        await db.execute(
            "UPDATE users SET mammoths=mammoths+1 WHERE user_id=?",
            (uid,)
        )

        await db.commit()

    await message.answer("🦣 Мамонт добавлен")

# =================
# СТАТИСТИКА
# =================

@dp.message(lambda m: m.text == "📊 Статистика")
async def stats(message: types.Message):

    role = await get_role(message.from_user.id)

    if role not in ["admin", "owner"]:
        return

    async with aiosqlite.connect("team.db") as db:

        cursor = await db.execute(
            "SELECT SUM(money),SUM(mammoths) FROM users"
        )

        data = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )

        users = await cursor.fetchone()

    money = data[0] or 0
    mammoths = data[1] or 0

    await message.answer(f"""
📊 Статистика команды

👥 Воркеров: {users[0]}
💰 Общий заработок: ${money}
🦣 Мамонтов: {mammoths}
""")

# =================
# ЗАПУСК
# =================

async def main():

    await init_db()

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
