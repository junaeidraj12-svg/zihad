from flask import Flask, request
import telebot
import requests
import sqlite3
import threading
import time
import pyotp
import os

# --- Flask Server & Bot Setup ---
app = Flask('')

# --- Bot Configurations ---
TOKEN = '8844874492:AAF8p7MpT1GN7gm5j-Lj8aJ3LiV4G1SCz_Q'
CURRENT_API_KEY = 'MURAD_B50401966BD9C7C5EB70411D'
ADMIN_ID = 8693017594
OTP_GROUP_LINK = 'https://t.me/Zihavxnogna'
OTP_GROUP_ID = -1004499937801
BOT_USERNAME = 'NemberXOTPBot'
API_BASE_URL = 'https://2eee7.com/@Access/@Bot/2eee7/@public/api/'

WITHDRAW_LIMIT = 0.10
REFERRAL_BONUS = 10.0
OTP_REWARD = 0.0025  
SUB_ADMINS = []
SUPPORT_ADMIN_USERNAME = 'Zihad88990'
METHOD_CHANNEL_LINK = 'https://t.me/vwmwonskw'

CURRENT_BUTTON_STYLE = "success"

bot = telebot.TeleBot(TOKEN)
user_states = {}
active_otp_threads = {}

service_status = {
    "Facebook": True,
    "Instagram": True,
    "Whatsapp": True,
    "Imo": True,
    "Tik tok": True,
    "Binance": True
}

# --- Database Setup ---
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance REAL DEFAULT 0.0,
        referred_by INTEGER,
        referral_count INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0
    )
''')

try:
    cursor.execute('ALTER TABLE users ADD COLUMN referred_by INTEGER')
except:
    pass

try:
    cursor.execute('ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0')
except:
    pass

cursor.execute('''
    CREATE TABLE IF NOT EXISTS services_countries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        service_name TEXT,
        country_data TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS withdrawals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        pay_id TEXT,
        status TEXT DEFAULT 'pending'
    )
''')
conn.commit()

def register_user(user_id, username, referred_by=None):
    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    exists = cursor.fetchone()
    if not exists:
        cursor.execute('INSERT INTO users (user_id, username, referred_by) VALUES (?, ?, ?)', (user_id, username, referred_by))
        conn.commit()
        if referred_by and referred_by != user_id:
            cursor.execute('UPDATE users SET referral_count = referral_count + 1, balance = balance + ? WHERE user_id = ?', (REFERRAL_BONUS, referred_by))
            conn.commit()

def is_admin(user_id):
    return user_id == ADMIN_ID or user_id in SUB_ADMINS

def get_admin_markup():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("👥 Total Users", callback_data="admin_users"),
        telebot.types.InlineKeyboardButton("📊 Live Traffic", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("⚙️ Manage Services", callback_data="admin_manage_serv"),
        telebot.types.InlineKeyboardButton("🌐 Manage Countries", callback_data="admin_manage_countries"),
        telebot.types.InlineKeyboardButton("🔑 API Settings", callback_data="admin_api_settings"),
        telebot.types.InlineKeyboardButton("🎁 Change OTP Reward", callback_data="admin_change_otp_reward"),
        telebot.types.InlineKeyboardButton("⏳ Pending Payments", callback_data="admin_pending_payments"),
        telebot.types.InlineKeyboardButton("📩 Support Messages", callback_data="admin_support_msgs"),
        telebot.types.InlineKeyboardButton("📢 Change Method Channel", callback_data="admin_change_method"),
        telebot.types.InlineKeyboardButton("🆘 Change Support ID", callback_data="admin_change_support"),
        telebot.types.InlineKeyboardButton("💵 Change Withdraw Limit", callback_data="admin_change_withdraw"),
        telebot.types.InlineKeyboardButton("🎁 Change Referral Bonus", callback_data="admin_change_ref_bonus"),
        telebot.types.InlineKeyboardButton("🎨 Change Button Style", callback_data="admin_change_btn_style"),
        telebot.types.InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast"),
        telebot.types.InlineKeyboardButton("➕ Add User Balance", callback_data="admin_add_bal"),
        telebot.types.InlineKeyboardButton("➖ Deduct User Balance", callback_data="admin_cut_bal"),
        telebot.types.InlineKeyboardButton("🚫 Ban User", callback_data="admin_ban_user"),
        telebot.types.InlineKeyboardButton("✅ Unban User", callback_data="admin_unban_user"),
        telebot.types.InlineKeyboardButton("➕ Add Sub-Admin", callback_data="admin_add_subadmin")
    )
    return markup

def set_bot_commands():
    commands = [
        telebot.types.BotCommand("start", "Start the bot"),
        telebot.types.BotCommand("balance", "Check your balance"),
        telebot.types.BotCommand("withdraw", "Withdraw your earnings"),
        telebot.types.BotCommand("referral", "Get your referral link"),
        telebot.types.BotCommand("cancel", "Cancel operation")
    ]
    bot.set_my_commands(commands)

set_bot_commands()

@app.route('/')
def home():
    return "I am alive!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "No Username"
    
    args = message.text.split()
    referred_by = None
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id != user_id:
                referred_by = ref_id
        except ValueError:
            pass

    register_user(user_id, username, referred_by)

    cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    if res and res[0] == 1:
        bot.send_message(message.chat.id, "❌ Sorry, you are banned from using this bot.")
        return

    keyboard_rows = [
        [
            {"text": "📱 Get Number", "style": "success"},
            {"text": "🔐 Get2FA", "style": "success"}
        ],
        [
            {"text": "💰 Balance", "style": "primary"},
            {"text": "💵 Withdraw", "style": "primary"}
        ],
        [
            {"text": "🎁 Refer", "style": "success"},
            {"text": "📢 Method Channel", "style": "primary"}
        ],
        [
            {"text": "🆘 Help & Support", "style": "success"}
        ]
    ]

    if is_admin(user_id):
        keyboard_rows.append([{"text": "⚙️ Admin Panel", "style": "success"}])

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": message.chat.id,
        "text": f"Welcome to the OTP Bot!\nOfficial Group: {OTP_GROUP_LINK}",
        "reply_markup": {
            "keyboard": keyboard_rows,
            "resize_keyboard": True
        },
        "disable_web_page_preview": True
    }
    requests.post(url, json=payload)

@bot.message_handler(commands=['balance'])
def check_balance(message):
    user_id = message.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    bal = res[0] if res else 0.0
    bot.send_message(message.chat.id, f"💰 **Your Balance:** `${bal:.4f}`", parse_mode='Markdown')

@bot.message_handler(commands=['referral'])
def referral_link_command(message):
    user_id = message.from_user.id
    cursor.execute('SELECT referral_count FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    ref_count = res[0] if res else 0
    
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    
    text = (
        f"👥 **Referral Program**\n\n"
        f"Invite your friends and earn `${REFERRAL_BONUS}` for each referral!\n\n"
        f"🔗 **Your Referral Link:**\n`{ref_link}`\n\n"
        f"📊 **Total Referred:** `{ref_count} Users`"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

@bot.message_handler(commands=['withdraw'])
def withdraw_money(message):
    user_id = message.from_user.id
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    res = cursor.fetchone()
    bal = res[0] if res else 0.0
    
    if bal < WITHDRAW_LIMIT:
        bot.send_message(message.chat.id, f"❌ Insufficient balance. Minimum withdrawal is ${WITHDRAW_LIMIT}.")
    else:
        user_states[user_id] = {'state': 'waiting_for_pay_id', 'balance': bal}
        bot.send_message(message.chat.id, f"💰 Your balance: `${bal:.4f}`\n\nPlease send your Binance Pay ID:")

@bot.message_handler(commands=['cancel'])
def cancel_operation(message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        bot.send_message(message.chat.id, "❌ Operation cancelled.")
    else:
        bot.send_message(message.chat.id, "⚠️ No active process found.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    text = message.text
    user_id = message.from_user.id

    if user_id in user_states:
        state_data = user_states[user_id]
        if isinstance(state_data, dict):
            state = state_data.get('state')
            if state == 'waiting_for_pay_id':
                pay_id = text.strip()
                user_states[user_id] = {'state': 'waiting_for_amount', 'pay_id': pay_id, 'balance': state_data['balance']}
                
                inline_keyboard = [
                    [{"text": "💰 Full Balance", "callback_data": "wd_full", "style": "primary"}],
                    [{"text": "✏️ Custom Amount", "callback_data": "wd_custom", "style": "success"}]
                ]
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                payload = {
                    "chat_id": message.chat.id,
                    "text": f"🏦 Method: Binance\n📱 Pay ID: `{pay_id}`\n\nSelect amount:",
                    "reply_markup": {"inline_keyboard": inline_keyboard},
                    "parse_mode": "Markdown"
                }
                requests.post(url, json=payload)
                return
            elif state == 'waiting_for_custom_amount':
                try:
                    amount = float(text.strip())
                    bal = state_data['balance']
                    pay_id = state_data['pay_id']
                    if amount > bal or amount <= 0:
                        bot.send_message(message.chat.id, "❌ Invalid amount. Try again:")
                        return
                    
                    cursor.execute('INSERT INTO withdrawals (user_id, amount, pay_id) VALUES (?, ?, ?)', (user_id, amount, pay_id))
                    conn.commit()
                    wd_id = cursor.lastrowid
                    del user_states[user_id]
                    
                    bot.send_message(message.chat.id, "✅ Your withdrawal request has been sent to the admin successfully!")
                    
                    admin_inline = [
                        [
                            {"text": "✅ Approve", "callback_data": f"wd_app_{wd_id}", "style": "success"},
                            {"text": "❌ Cancel", "callback_data": f"wd_can_{wd_id}", "style": "danger"}
                        ]
                    ]
                    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                    payload = {
                        "chat_id": ADMIN_ID,
                        "text": f"🔔 **New Withdraw Request!**\n\n👤 User ID: `{user_id}`\n🏦 Method: Binance\n📱 Pay ID: `{pay_id}`\n💰 Amount: `${amount:.4f}`",
                        "reply_markup": {"inline_keyboard": admin_inline},
                        "parse_mode": "Markdown"
                    }
                    requests.post(url, json=payload)
                except ValueError:
                    bot.send_message(message.chat.id, "❌ Please enter a valid number:")
                return

    if is_admin(user_id) and user_id in user_states and isinstance(user_states[user_id], str):
        state = user_states[user_id]
        if state == 'waiting_for_api':
            global CURRENT_API_KEY
            CURRENT_API_KEY = text.strip()
            del user_states[user_id]
            bot.send_message(message.chat.id, "✅ API Key updated successfully!")
            return
        elif state == 'waiting_for_otp_reward':
            try:
                global OTP_REWARD
                OTP_REWARD = float(text.strip())
                del user_states[user_id]
                bot.send_message(message.chat.id, f"✅ OTP reward updated to `${OTP_REWARD}` successfully!")
            except ValueError:
                bot.send_message(message.chat.id, "❌ Please enter a valid number.")
            return
        elif state == 'waiting_for_method_channel':
            global METHOD_CHANNEL_LINK
            METHOD_CHANNEL_LINK = text.strip()
            del user_states[user_id]
            bot.send_message(message.chat.id, "✅ Method channel link updated successfully!")
            return
        elif state == 'waiting_for_support_id':
            global SUPPORT_ADMIN_USERNAME
            SUPPORT_ADMIN_USERNAME = text.strip().replace("@", "")
            del user_states[user_id]
            bot.send_message(message.chat.id, f"✅ Support ID updated to @{SUPPORT_ADMIN_USERNAME} successfully!")
            return
        elif state == 'waiting_for_withdraw_limit':
            try:
                global WITHDRAW_LIMIT
                WITHDRAW_LIMIT = float(text.strip())
                del user_states[user_id]
                bot.send_message(message.chat.id, f"✅ Withdraw limit updated to ${WITHDRAW_LIMIT} successfully!")
            except ValueError:
                bot.send_message(message.chat.id, "❌ Please enter a valid number.")
            return
        elif state == 'waiting_for_ref_bonus':
            try:
                global REFERRAL_BONUS
                REFERRAL_BONUS = float(text.strip())
                del user_states[user_id]
                bot.send_message(message.chat.id, f"✅ Referral bonus updated successfully!")
            except ValueError:
                bot.send_message(message.chat.id, "❌ Please enter a valid number.")
            return
        elif state == 'waiting_for_btn_style':
            global CURRENT_BUTTON_STYLE
            val = text.strip().lower()
            if val in ["success", "primary", "danger"]:
                CURRENT_BUTTON_STYLE = val
                del user_states[user_id]
                bot.send_message(message.chat.id, f"✅ Default inline button style updated to `{CURRENT_BUTTON_STYLE}` successfully!", parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, "❌ Invalid style! Send either: `success`, `primary`, or `danger`", parse_mode='Markdown')
            return
        elif state.startswith('adding_country_'):
            service_name = state.replace('adding_country_', '')
            if '|' in text:
                cursor.execute('INSERT INTO services_countries (service_name, country_data) VALUES (?, ?)', (service_name, text))
                conn.commit()
                del user_states[user_id]
                bot.send_message(message.chat.id, f"✅ Country added for **{service_name}**!", parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, "❌ Correct format: `Country | Range | Flag | Shortcode`", parse_mode='Markdown')
            return
        elif state == 'waiting_for_broadcast':
            del user_states[user_id]
            cursor.execute('SELECT user_id FROM users')
            users = cursor.fetchall()
            for u in users:
                try:
                    bot.send_message(u[0], f"📢 **Announcement:**\n\n{text}", parse_mode='Markdown')
                except:
                    pass
            bot.send_message(message.chat.id, "✅ Broadcast completed.")
            return
        elif state == 'waiting_for_add_bal':
            try:
                parts = text.split()
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (float(parts[1]), int(parts[0])))
                conn.commit()
                del user_states[user_id]
                bot.send_message(message.chat.id, "✅ Balance added successfully.")
            except:
                bot.send_message(message.chat.id, "❌ Wrong format. Send: `ID Amount`")
            return
        elif state == 'waiting_for_cut_bal':
            try:
                parts = text.split()
                cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (float(parts[1]), int(parts[0])))
                conn.commit()
                del user_states[user_id]
                bot.send_message(message.chat.id, "✅ Balance deducted successfully.")
            except:
                bot.send_message(message.chat.id, "❌ Wrong format.")
            return
        elif state == 'waiting_for_ban':
            try:
                cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (int(text.strip()),))
                conn.commit()
                del user_states[user_id]
                bot.send_message(message.chat.id, "✅ User banned successfully.")
            except:
                bot.send_message(message.chat.id, "❌ Invalid ID.")
            return
        elif state == 'waiting_for_unban':
            try:
                cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (int(text.strip()),))
                conn.commit()
                del user_states[user_id]
                bot.send_message(message.chat.id, "✅ User unbanned successfully.")
            except:
                bot.send_message(message.chat.id, "❌ Invalid ID.")
            return
        elif state == 'waiting_for_subadmin':
            try:
                SUB_ADMINS.append(int(text.strip()))
                del user_states[user_id]
                bot.send_message(message.chat.id, "✅ Sub-admin added successfully.")
            except:
                bot.send_message(message.chat.id, "❌ Invalid ID.")
            return

    if text == '📱 Get Number':
        services = ["Facebook", "Instagram", "Whatsapp", "Imo", "Tik tok", "Binance"]
        inline_keyboard = []
        for s in services:
            if service_status.get(s, True):
                btn_style = "primary" if s in ["Facebook", "Binance"] else "success"
                inline_keyboard.append([{"text": s, "callback_data": f"user_serv_{s}", "style": btn_style}])
        
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": message.chat.id,
            "text": "Select a service: ⬇️",
            "reply_markup": {"inline_keyboard": inline_keyboard}
        }
        requests.post(url, json=payload)

    elif text == '🔐 Get2FA':
        user_states[user_id] = 'waiting_for_2fa_key'
        bot.send_message(message.chat.id, "🔐 Please provide your 2FA secret key:")

    elif text == '🎁 Refer':
        referral_link_command(message)

    elif text == '📢 Method Channel':
        inline_keyboard = [[{"text": "📢 Method Channel", "url": METHOD_CHANNEL_LINK, "style": CURRENT_BUTTON_STYLE}]]
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": message.chat.id,
            "text": "⏳⏳ Click The Button Below To Watch The Method Video ⏳⏳",
            "reply_markup": {"inline_keyboard": inline_keyboard}
        }
        requests.post(url, json=payload)

    elif text == '🆘 Help & Support':
        inline_keyboard = [[{"text": "Support", "url": f"https://t.me/{SUPPORT_ADMIN_USERNAME}", "style": CURRENT_BUTTON_STYLE}]]
        url = f"https://api.telegram.org/bot{TOKEN}/sendMes