import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
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
[KeyboardButton(text="💰 Заработок"),KeyboardButton(text="🦣 Мамонты")],
[KeyboardButton(text="📅 Дней в тиме"),KeyboardButton(text="🏆 Топ")],
[KeyboardButton(text="📞 Вызвать админа")]
],
resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
keyboard=[
[KeyboardButton(text="➕ Добавить деньги")],
[KeyboardButton(text="➖ Снять деньги")],
[KeyboardButton(text="➕ Добавить мамонта")],
[KeyboardButton(text="👥 Воркеры")],
[KeyboardButton(text="📊 Статистика")]
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
# РЕГИСТРАЦИЯ
# =================

@dp.message(commands=["start"])
async def start(message: types.Message):

async with aiosqlite.connect("team.db") as db:

cursor=await db.execute(
"SELECT * FROM users WHERE user_id=?",
(message.from_user.id,)
)

user=await cursor.fetchone()

if not user:

role="worker"

if message.from_user.id==OWNER_ID:
role="owner"

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

await message.answer("🔥 Добро пожаловать",reply_markup=user_kb)

# =================
# РОЛЬ
# =================

async def get_role(user_id):

async with aiosqlite.connect("team.db") as db:

cursor=await db.execute(
"SELECT role FROM users WHERE user_id=?",
(user_id,)
)

data=await cursor.fetchone()

return data[0]

# =================
# ПРОФИЛЬ
# =================

@dp.message(lambda m: m.text=="👤 Профиль")
async def profile(message: types.Message):

async with aiosqlite.connect("team.db") as db:

cursor=await db.execute(
"SELECT money,mammoths,join_date FROM users WHERE user_id=?",
(message.from_user.id,)
)

data=await cursor.fetchone()

join=datetime.fromisoformat(data[2])

days=(datetime.now()-join).days

await message.answer(f"""
👤 Профиль

💰 Деньги: ${data[0]}
🦣 Мамонты: {data[1]}
📅 Дней в тиме: {days}
""")

# =================
# ТОП
# =================

@dp.message(lambda m: m.text=="🏆 Топ")
async def top(message: types.Message):

async with aiosqlite.connect("team.db") as db:

cursor=await db.execute(
"SELECT username,money FROM users ORDER BY money DESC LIMIT 10"
)

top=await cursor.fetchall()

text="🏆 ТОП воркеров\n\n"

for i,user in enumerate(top,1):

text+=f"{i}. @{user[0]} — ${user[1]}\n"

await message.answer(text)

# =================
# ДОБАВИТЬ ДЕНЬГИ
# =================

@dp.message(commands=["addmoney"])
async def add_money(message: types.Message):

role=await get_role(message.from_user.id)

if role not in ["admin","owner"]:
return

args=message.text.split()

uid=int(args[1])
amount=int(args[2])

async with aiosqlite.connect("team.db") as db:

await db.execute(
"UPDATE users SET money=money+? WHERE user_id=?",
(amount,uid)
)

await db.execute(
"INSERT INTO logs(user_id,action,amount,date) VALUES(?,?,?,?)",
(uid,"add_money",amount,datetime.now().isoformat())
)

await db.commit()

await message.answer("💰 Деньги добавлены")

# =================
# МАМОНТ
# =================

@dp.message(commands=["addmammoth"])
async def add_mammoth(message: types.Message):

role=await get_role(message.from_user.id)

if role not in ["admin","owner"]:
return

args=message.text.split()

uid=int(args[1])

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

@dp.message(lambda m: m.text=="📊 Статистика")
async def stats(message: types.Message):

role=await get_role(message.from_user.id)

if role not in ["admin","owner"]:
return

async with aiosqlite.connect("team.db") as db:

cursor=await db.execute(
"SELECT SUM(money),SUM(mammoths) FROM users"
)

data=await cursor.fetchone()

cursor=await db.execute(
"SELECT COUNT(*) FROM users"
)

users=await cursor.fetchone()

await message.answer(f"""
📊 Статистика команды

👥 Воркеров: {users[0]}
💰 Общий заработок: ${data[0]}
🦣 Мамонтов: {data[1]}
""")

# =================
# ЗАПУСК
# =================

async def main():

await init_db()

print("BOT STARTED")

await dp.start_polling(bot)

asyncio.run(main())
