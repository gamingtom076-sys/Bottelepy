import telebot
from telebot import types

TOKEN = "PASTE_YOUR_TOKEN"
ADMIN_ID = 6525785749

bot = telebot.TeleBot(TOKEN)

# ===== DATA =====
data = {
    "price": "150",
    "button": "TASHANWIN GAME",
    "qr": None,
    "account": "ID: demo\nPASS: 1234\nLINK: example.com",
    "reject_msg": "❌ Sir apne payment nahi kiya"
}

users = set()
blocked = set()
pending = {}
msg_map = {}

# ===== USER KEYBOARD =====
def user_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(data["button"], "💬 Chat with Admin")
    return kb

# ===== ADMIN KEYBOARD =====
def admin_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Set QR Code", "📥 Set Account Credentials")
    kb.row("💰 Set Price", "📝 Pending UTRs")
    kb.row("✏️ Set Button Name", "📢 Broadcast")
    kb.row("🚫 Block User", "✅ Unblock User")
    kb.row("👥 Users", "🚷 Blocked Users")
    return kb

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    if msg.chat.id in blocked:
        return

    users.add(msg.chat.id)
    name = msg.from_user.first_name

    text = f"""👋 Welcome {name}!

📢 We provide demo accounts for Tashan Game.

💡 How it works:
1️⃣ Click '{data['button']}'
2️⃣ Pay ₹{data['price']}
3️⃣ Submit 12-digit UTR
4️⃣ Get approved & receive login"""

    if msg.chat.id == ADMIN_ID:
        bot.send_message(msg.chat.id, "👑 Admin Panel", reply_markup=admin_kb())
    else:
        bot.send_message(msg.chat.id, text, reply_markup=user_kb())

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def main(msg):
    chat = msg.chat.id

    if chat in blocked:
        return

    # ===== USER =====
    if chat != ADMIN_ID:

        if msg.text == data["button"]:
            if data["qr"]:
                bot.send_photo(chat, data["qr"],
                               caption=f"💰 Price: ₹{data['price']}\n📤 Pay & send UTR\n\n🔢 Now send your 12-digit UTR:")
                bot.register_next_step_handler(msg, get_utr)
            else:
                bot.send_message(chat, "QR not set")

        elif msg.text == "💬 Chat with Admin":
            bot.send_message(chat, "📝 Send your message for Admin:")
            bot.register_next_step_handler(msg, forward_admin)

        return

    # ===== ADMIN =====
    if msg.text == "➕ Set QR Code":
        m = bot.send_message(chat, "Send QR Image")
        bot.register_next_step_handler(m, set_qr)

    elif msg.text == "📥 Set Account Credentials":
        m = bot.send_message(chat, "Send account details")
        bot.register_next_step_handler(m, set_account)

    elif msg.text == "💰 Set Price":
        m = bot.send_message(chat, "Send price")
        bot.register_next_step_handler(m, set_price)

    elif msg.text == "✏️ Set Button Name":
        m = bot.send_message(chat, "Send button name")
        bot.register_next_step_handler(m, set_button)

    elif msg.text == "📢 Broadcast":
        m = bot.send_message(chat, "Send broadcast message")
        bot.register_next_step_handler(m, broadcast)

    elif msg.text == "📝 Pending UTRs":
        show_pending(chat)

    elif msg.text == "🚫 Block User":
        m = bot.send_message(chat, "Send user ID")
        bot.register_next_step_handler(m, block_user)

    elif msg.text == "✅ Unblock User":
        m = bot.send_message(chat, "Send user ID")
        bot.register_next_step_handler(m, unblock_user)

    elif msg.text == "👥 Users":
        bot.send_message(chat, f"Total Users: {len(users)}")

    elif msg.text == "🚷 Blocked Users":
        bot.send_message(chat, f"Blocked: {len(blocked)}")

# ===== CHAT SYSTEM =====
def forward_admin(msg):
    f = bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
    msg_map[f.message_id] = msg.chat.id
    bot.send_message(msg.chat.id, "✅ Message sent to Admin")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.reply_to_message)
def reply_admin(msg):
    mid = msg.reply_to_message.message_id
    if mid in msg_map:
        uid = msg_map[mid]
        bot.send_message(uid, f"💬 Admin: {msg.text}")

# ===== UTR =====
def get_utr(msg):
    chat = msg.chat.id
    utr = msg.text

    if not utr.isdigit() or len(utr) != 12:
        bot.send_message(chat, "❌ Invalid UTR")
        return

    pending[chat] = utr

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"ok_{chat}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"no_{chat}")
    )

    bot.send_message(ADMIN_ID, f"User: {chat}\nUTR: {utr}", reply_markup=kb)
    bot.send_message(chat, "⏳ Waiting for approval")

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    uid = int(call.data.split("_")[1])

    if call.data.startswith("ok"):
        bot.send_message(uid, f"✅ Approved\n\n{data['account']}")
        bot.edit_message_text("Approved", call.message.chat.id, call.message.message_id)

    elif call.data.startswith("no"):
        bot.send_message(uid, data["reject_msg"])
        bot.edit_message_text("Rejected", call.message.chat.id, call.message.message_id)

# ===== ADMIN FUNCTIONS =====
def set_qr(msg):
    if msg.photo:
        data["qr"] = msg.photo[-1].file_id
        bot.send_message(msg.chat.id, "QR set")

def set_account(msg):
    data["account"] = msg.text
    bot.send_message(msg.chat.id, "Account saved")

def set_price(msg):
    data["price"] = msg.text
    bot.send_message(msg.chat.id, "Price updated")

def set_button(msg):
    data["button"] = msg.text
    bot.send_message(msg.chat.id, "Button updated")

def broadcast(msg):
    for u in users:
        try:
            bot.send_message(u, msg.text)
        except:
            pass
    bot.send_message(msg.chat.id, "Broadcast done")

def show_pending(chat):
    if not pending:
        bot.send_message(chat, "No pending")
    else:
        txt = "\n".join([f"{k}:{v}" for k,v in pending.items()])
        bot.send_message(chat, txt)

def block_user(msg):
    blocked.add(int(msg.text))
    bot.send_message(msg.chat.id, "User blocked")

def unblock_user(msg):
    blocked.discard(int(msg.text))
    bot.send_message(msg.chat.id, "User unblocked")

# ===== RUN =====
print("Bot Running...")
bot.infinity_polling()
