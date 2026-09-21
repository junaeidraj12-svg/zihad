import telebot
import requests
import sqlite3
import threading
import time
import pyotp

TOKEN = '8844874492:AAFKe2tLG-8ywBS1wJB065TeceVuZknIHBY'
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
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": message.chat.id,
            "text": "Please contact the admin for any issues.",
            "reply_markup": {"inline_keyboard": inline_keyboard}
        }
        requests.post(url, json=payload)

    elif text == '💰 Balance':
        check_balance(message)

    elif text == '💵 Withdraw':
        withdraw_money(message)

    elif text == '⚙️ Admin Panel' and is_admin(user_id):
        bot.send_message(message.chat.id, "⚙️ **Admin Control Panel:**", reply_markup=get_admin_markup(), parse_mode='Markdown')

    elif user_states.get(user_id) == 'waiting_for_2fa_key':
        key = text.strip().replace(" ", "")
        try:
            totp = pyotp.TOTP(key)
            current_code = totp.now()
            bot.send_message(
                message.chat.id, 
                f"✅ **2FA Code Generated Successfully!**\n\n🔑 Key: `{key}`\n\n⚡ Live Code: `{current_code}`", 
                parse_mode='Markdown'
            )
        except Exception as e:
            bot.send_message(
                message.chat.id, 
                "❌ Invalid 2FA secret key provided! Please check and try again with a valid key."
            )
        del user_states[user_id]

def check_otp_background(chat_id, phone, serv_name, country_flag, country_full_name, short_code):
    for _ in range(60):
        try:
            url = f"{API_BASE_URL}success-otp-info"
            headers = {'X-API-Key': CURRENT_API_KEY}
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('meta', {}).get('code') == 200:
                    otps_list = res_json.get('data', {}).get('otps', [])
                    for item in otps_list:
                        api_number = item.get('number', '')
                        if phone in api_number or api_number in phone:
                            otp_code = item.get('otp')
                            
                            if otp_code:
                                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (OTP_REWARD, chat_id,))
                                conn.commit()
                                
                                cursor.execute('SELECT balance FROM users WHERE user_id = ?', (chat_id,))
                                new_bal = cursor.fetchone()[0]
                                
                                user_msg = (
                                    f"{country_flag} <code>{phone}</code>\n\n"
                                    f"🔑 <b>OTP :</b> <code>{otp_code}</code>\n"
                                    f"💰 <b>Earned:</b> +${OTP_REWARD:.4f}\n\n"
                                    f"💵 <b>Total Balance:</b> ${new_bal:.4f}"
                                )
                                
                                url_msg = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                                payload = {
                                    "chat_id": chat_id,
                                    "text": user_msg,
                                    "parse_mode": "HTML"
                                }
                                requests.post(url_msg, json=payload)
                                
                                masked_phone = phone[:4] + "XXXXX" + phone[-4:] if len(phone) > 8 else phone
                                
                                group_msg = (
                                    f"<b>{serv_name.upper()} | {country_flag} {short_code.upper()}</b>\n\n"
                                    f"📱 <code>{masked_phone}</code>\n\n"
                                    f"🔑 Code: <code>{otp_code}</code>\n\n"
                                    f"🌐 Language: English\n\n"
                                    f"📨 Message:\n"
                                    f"<code>&lt;#&gt; {otp_code} is your {serv_name} code</code>"
                                )
                                
                                group_inline = [[{"text": "Open Bot", "url": f"https://t.me/{BOT_USERNAME}", "style": "primary"}]]
                                group_payload = {
                                    "chat_id": OTP_GROUP_ID,
                                    "text": group_msg,
                                    "reply_markup": {"inline_keyboard": group_inline},
                                    "parse_mode": "HTML"
                                }
                                try:
                                    requests.post(url_msg, json=group_payload)
                                except Exception as g_err:
                                    print(f"Group Send Error: {g_err}")
                                    
                                return
            time.sleep(3)
        except Exception as e:
            print(f"OTP Check Error: {e}")
            time.sleep(3)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if data == "wd_full":
        if user_id in user_states and isinstance(user_states[user_id], dict):
            st = user_states[user_id]
            bal = st['balance']
            pay_id = st['pay_id']
            cursor.execute('INSERT INTO withdrawals (user_id, amount, pay_id) VALUES (?, ?, ?)', (user_id, bal, pay_id))
            conn.commit()
            wd_id = cursor.lastrowid
            del user_states[user_id]
            
            url_edit = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
            requests.post(url_edit, json={"chat_id": chat_id, "message_id": message_id, "text": "✅ Your full balance withdrawal request has been sent to the admin!"})
            
            admin_inline = [
                [
                    {"text": "✅ Approve", "callback_data": f"wd_app_{wd_id}", "style": "success"},
                    {"text": "❌ Cancel", "callback_data": f"wd_can_{wd_id}", "style": "danger"}
                ]
            ]
            url_send = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url_send, json={
                "chat_id": ADMIN_ID,
                "text": f"🔔 **New Withdraw Request!**\n\n👤 User ID: `{user_id}`\n🏦 Method: Binance\n📱 Pay ID: `{pay_id}`\n💰 Amount: `${bal:.4f}`",
                "reply_markup": {"inline_keyboard": admin_inline},
                "parse_mode": "Markdown"
            })
        return

    elif data == "wd_custom":
        if user_id in user_states and isinstance(user_states[user_id], dict):
            user_states[user_id]['state'] = 'waiting_for_custom_amount'
            url_edit = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
            requests.post(url_edit, json={"chat_id": chat_id, "message_id": message_id, "text": "✏️ Please enter the amount (USD) you want to withdraw:"})
        return

    elif data.startswith("wd_app_") or data.startswith("wd_can_"):
        if not is_admin(user_id):
            return
        wd_id = int(data.split("_")[2])
        action = data.split("_")[1]
        
        cursor.execute('SELECT user_id, amount FROM withdrawals WHERE id = ?', (wd_id,))
        row = cursor.fetchone()
        if row:
            u_id, amt = row[0], row[1]
            url_edit = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
            if action == 'app':
                cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amt, u_id))
                conn.commit()
                bot.answer_callback_query(call.id, "Approved successfully!")
                requests.post(url_edit, json={"chat_id": chat_id, "message_id": message_id, "text": "✅ Withdrawal request approved."})
                try:
                    bot.send_message(u_id, f"✅ Your withdrawal request has been approved! (${amt})")
                except:
                    pass
            else:
                bot.answer_callback_query(call.id, "Cancelled!")
                requests.post(url_edit, json={"chat_id": chat_id, "message_id": message_id, "text": "❌ Withdrawal request cancelled."})
                try:
                    bot.send_message(u_id, f"❌ Your withdrawal request has been cancelled.")
                except:
                    pass
        return

    if data.startswith("user_serv_"):
        serv_name = data.replace("user_serv_", "")
        cursor.execute('SELECT id, country_data FROM services_countries WHERE service_name = ?', (serv_name,))
        rows = cursor.fetchall()
        
        inline_keyboard = []
        if rows:
            for row in rows:
                row_id = row[0]
                parts = row[1].split('|')
                if len(parts) >= 3:
                    c_name = parts[0].strip()
                    c_flag = parts[2].strip()
                    inline_keyboard.append([{"text": f"{c_flag} {c_name}", "callback_data": f"get_num_{row_id}", "style": CURRENT_BUTTON_STYLE}])
        else:
            inline_keyboard.append([{"text": "⚠️ No countries available", "callback_data": "no_country", "style": "danger"}])

        inline_keyboard.append([{"text": "🔙 Back", "callback_data": "user_back_to_services", "style": "danger"}])
        
        url_edit = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"📁 Select country for **{serv_name}**:",
            "reply_markup": {"inline_keyboard": inline_keyboard},
            "parse_mode": "Markdown"
        }
        res = requests.post(url_edit, json=payload)
        if res.status_code != 200:
            url_send = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url_send, json={
                "chat_id": chat_id,
                "text": f"📁 Select country for **{serv_name}**:",
                "reply_markup": {"inline_keyboard": inline_keyboard},
                "parse_mode": "Markdown"
            })
        return

    elif data == "user_back_to_services":
        services = ["Facebook", "Instagram", "Whatsapp", "Imo", "Tik tok", "Binance"]
        inline_keyboard = []
        for s in services:
            if service_status.get(s, True):
                btn_style = "primary" if s in ["Facebook", "Binance"] else "success"
                inline_keyboard.append([{"text": s, "callback_data": f"user_serv_{s}", "style": btn_style}])
        
        url_edit = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
        requests.post(url_edit, json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": "Select a service: ⬇️",
            "reply_markup": {"inline_keyboard": inline_keyboard}
        })
        return

    elif data.startswith("get_num_"):
        try:
            row_id = data.replace("get_num_", "")
            if row_id == "new":
                return
            cursor.execute('SELECT service_name, country_data FROM services_countries WHERE id = ?', (row_id,))
            row = cursor.fetchone()
            
            if not row:
                bot.answer_callback_query(call.id, "Country data not found!", show_alert=True)
                return
                
            serv_name, country_data = row[0], row[1]
            parts = country_data.split('|')
            country_full_name = parts[0].strip() if len(parts) >= 1 else "Unknown"
            c_flag = parts[2].strip() if len(parts) >= 3 else "🌐"
            short_code = parts[3].strip() if len(parts) >= 4 else "XX"
            raw_range = parts[1].strip()
            range_val = raw_range.replace("+", "")
            
            api_url = f"{API_BASE_URL}getnum"
            headers = {'X-API-Key': CURRENT_API_KEY, 'Content-Type': 'application/json'}
            payload = {'range': range_val}
            
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get('meta', {}).get('code') == 200 and 'data' in res_json:
                    res_data = res_json['data']
                    phone = res_data.get('full_number') or res_data.get('no_plus_number')
                    
                    if phone:
                        bot.answer_callback_query(call.id, "New number assigned!")
                        
                        inline_keyboard = [
                            [
                                {"text": "Change", "callback_data": f"get_num_{row_id}", "style": "danger"},
                                {"text": "OTP Group", "url": OTP_GROUP_LINK, "style": "success"}
                            ],
                            [
                                {"text": "🔙 Back", "callback_data": "user_back_to_services", "style": CURRENT_BUTTON_STYLE}
                            ]
                        ]
                        
                        assigned_text = (
                            f"<b>{serv_name.upper()} - {country_full_name.upper()} {c_flag}</b>\n"
                            f"<b>NUMBER ASSIGNED!</b>\n\n"
                            f"📞 Number: <code>{phone}</code>\n"
                            f"🌍 Country: {country_full_name.upper()} {c_flag}\n\n"
                            f"⏳ WAITING FOR OTP...................."
                        )
                        
                        url_edit = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
                        requests.post(url_edit, json={
                            "chat_id": chat_id,
                            "message_id": message_id,
                            "text": assigned_text,
                            "parse_mode": "HTML",
                            "reply_markup": {"inline_keyboard": inline_keyboard}
                        })
                        
                        threading.Thread(target=check_otp_background, args=(chat_id, phone, serv_name, c_flag, country_full_name, short_code)).start()
                    else:
                        bot.answer_callback_query(call.id, "No numbers available right now!", show_alert=True)
                else:
                    bot.answer_callback_query(call.id, "Stock out!", show_alert=True)
        except Exception as e:
            print(f"API Error: {e}")
            bot.answer_callback_query(call.id, "API connection error.", show_alert=True)
        return

    elif data.startswith("admin_") or data.startswith("toggle_serv_") or data.startswith("country_") or data.startswith("del_c_id_") or data == "no_country" or data.startswith("app_wd_") or data.startswith("can_wd_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "⚠️ Unauthorized!", show_alert=True)
            return

        url_edit = f"https://api.telegram.org/bot{TOKEN}/editMessageText"

        if data == "admin_back":
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "⚙️ **Admin Control Panel:**",
                "reply_markup": get_admin_markup().to_json(),
                "parse_mode": "Markdown"
            })
            return
            
        elif data == "admin_users":
            cursor.execute('SELECT COUNT(*) FROM users')
            total = cursor.fetchone()[0]
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"👥 Total Users: `{total}`",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_stats":
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "📊 Server Online ✅",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_manage_serv":
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            for s, status in service_status.items():
                status_icon = "✅ ON" if status else "❌ OFF"
                markup.add(telebot.types.InlineKeyboardButton(f"{s}: {status_icon}", callback_data=f"toggle_serv_{s}"))
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "⚙️ **Service Management:**",
                "reply_markup": markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data.startswith("toggle_serv_"):
            s_name = data.replace("toggle_serv_", "")
            if s_name in service_status:
                service_status[s_name] = not service_status[s_name]
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            for s, status in service_status.items():
                status_icon = "✅ ON" if status else "❌ OFF"
                markup.add(telebot.types.InlineKeyboardButton(f"{s}: {status_icon}", callback_data=f"toggle_serv_{s}"))
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "⚙️ **Service Management:**",
                "reply_markup": markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_manage_countries":
            markup = telebot.types.InlineKeyboardMarkup(row_width=2)
            services = ["Facebook", "Instagram", "Tik tok", "Whatsapp", "Imo", "Binance"]
            for s in services:
                markup.add(
                    telebot.types.InlineKeyboardButton(f"{s}", callback_data=f"ignore_{s}"),
                    telebot.types.InlineKeyboardButton("➕ Add", callback_data=f"country_add_{s}"),
                    telebot.types.InlineKeyboardButton("📋 List", callback_data=f"country_list_{s}"),
                    telebot.types.InlineKeyboardButton("🗑 Delete", callback_data=f"country_del_menu_{s}")
                )
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "🌐 **Country Management:**",
                "reply_markup": markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data.startswith("country_add_"):
            s_name = data.replace("country_add_", "")
            user_states[user_id] = f'adding_country_{s_name}'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"🌐 Add country for **{s_name}**:\n`Country | Range | Flag | Shortcode`",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data.startswith("country_list_"):
            s_name = data.replace("country_list_", "")
            cursor.execute('SELECT id, country_data FROM services_countries WHERE service_name = ?', (s_name,))
            rows = cursor.fetchall()
            text_res = f"📋 **Countries for {s_name}:**\n\n"
            for r in rows:
                text_res += f"ID: `{r[0]}` | Data: `{r[1]}`\n"
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text_res,
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })

        elif data.startswith("country_del_menu_"):
            s_name = data.replace("country_del_menu_", "")
            cursor.execute('SELECT id, country_data FROM services_countries WHERE service_name = ?', (s_name,))
            rows = cursor.fetchall()
            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            for r in rows:
                markup.add(telebot.types.InlineKeyboardButton(f"🗑 Delete: {r[1]}", callback_data=f"del_c_id_{r[0]}"))
            markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_manage_countries"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "🗑 Click to delete:",
                "reply_markup": markup.to_json(),
                "parse_mode": "Markdown"
            })

        elif data.startswith("del_c_id_"):
            c_id = data.replace("del_c_id_", "")
            cursor.execute('DELETE FROM services_countries WHERE id = ?', (c_id,))
            conn.commit()
            bot.answer_callback_query(call.id, "Deleted successfully!")
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "✅ Deleted successfully!",
                "reply_markup": back_markup.to_json()
            })

        elif data == "admin_api_settings":
            user_states[user_id] = 'waiting_for_api'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"🔑 Current API Key: `{CURRENT_API_KEY}`\n\nSend new API key:",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_change_otp_reward":
            user_states[user_id] = 'waiting_for_otp_reward'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"🎁 Current Reward: `${OTP_REWARD}`\n\nSend new amount:",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })

        elif data == "admin_change_btn_style":
            user_states[user_id] = 'waiting_for_btn_style'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"🎨 Current Button Style: `{CURRENT_BUTTON_STYLE}`\n\nSend new style name (`success`, `primary`, or `danger`):",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })

        elif data == "admin_pending_payments":
            cursor.execute('SELECT id, user_id, amount, pay_id FROM withdrawals WHERE status = "pending"')
            rows = cursor.fetchall()
            if not rows:
                bot.answer_callback_query(call.id, "No pending payments!", show_alert=True)
                return
            for r in rows:
                w_id, u_id, amt, p_id = r[0], r[1], r[2], r[3]
                inline_keyboard = [
                    [
                        {"text": "✅ Approve", "callback_data": f"app_wd_{w_id}", "style": "success"},
                        {"text": "❌ Cancel", "callback_data": f"can_wd_{w_id}", "style": "danger"}
                    ]
                ]
                url_send = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                requests.post(url_send, json={
                    "chat_id": chat_id,
                    "text": f"📌 **Pending Withdraw:**\n\n👤 User ID: `{u_id}`\n🏦 Pay ID: `{p_id}`\n💰 Amount: `${amt:.4f}`",
                    "reply_markup": {"inline_keyboard": inline_keyboard},
                    "parse_mode": "Markdown"
                })
            bot.answer_callback_query(call.id, "Pending list loaded.")

        elif data.startswith("app_wd_") or data.startswith("can_wd_"):
            w_id = int(data.split("_")[2])
            action = data.split("_")[1]
            cursor.execute('SELECT user_id, amount FROM withdrawals WHERE id = ?', (w_id,))
            row = cursor.fetchone()
            if row:
                u_id, amt = row[0], row[1]
                if action == 'app':
                    cursor.execute('UPDATE users SET balance = balance - ? WHERE user_id = ?', (amt, u_id))
                    cursor.execute('UPDATE withdrawals SET status = "approved" WHERE id = ?', (w_id,))
                    conn.commit()
                    requests.post(url_edit, json={"chat_id": chat_id, "message_id": message_id, "text": "✅ Withdrawal approved!"})
                    try:
                        bot.send_message(u_id, f"✅ Your withdrawal request has been approved! (${amt})")
                    except:
                        pass
                else:
                    cursor.execute('UPDATE withdrawals SET status = "cancelled" WHERE id = ?', (w_id,))
                    conn.commit()
                    requests.post(url_edit, json={"chat_id": chat_id, "message_id": message_id, "text": "❌ Withdrawal cancelled!"})
                    try:
                        bot.send_message(u_id, f"❌ Your withdrawal request has been cancelled.")
                    except:
                        pass
            return
            
        elif data == "admin_change_method":
            user_states[user_id] = 'waiting_for_method_channel'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"📢 Current Channel: `{METHOD_CHANNEL_LINK}`\n\nSend new link:",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })

        elif data == "admin_change_support":
            user_states[user_id] = 'waiting_for_support_id'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"🆘 Current Support ID: `@{SUPPORT_ADMIN_USERNAME}`\n\nSend new username:",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_change_withdraw":
            user_states[user_id] = 'waiting_for_withdraw_limit'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"💵 Current Limit: `${WITHDRAW_LIMIT}`\n\nSend new limit:",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_change_ref_bonus":
            user_states[user_id] = 'waiting_for_ref_bonus'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"🎁 Current Ref Bonus: `{REFERRAL_BONUS}`\n\nSend new bonus:",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_broadcast":
            user_states[user_id] = 'waiting_for_broadcast'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "📢 Send your broadcast message:",
                "reply_markup": back_markup.to_json()
            })
            
        elif data == "admin_add_bal":
            user_states[user_id] = 'waiting_for_add_bal'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "➕ Send: `User_ID Amount`",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_cut_bal":
            user_states[user_id] = 'waiting_for_cut_bal'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "➖ Send: `User_ID Amount`",
                "reply_markup": back_markup.to_json(),
                "parse_mode": "Markdown"
            })
            
        elif data == "admin_ban_user":
            user_states[user_id] = 'waiting_for_ban'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "🚫 Send user ID to ban:",
                "reply_markup": back_markup.to_json()
            })
            
        elif data == "admin_unban_user":
            user_states[user_id] = 'waiting_for_unban'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "✅ Send user_id to unban:",
                "reply_markup": back_markup.to_json()
            })
            
        elif data == "admin_add_subadmin":
            user_states[user_id] = 'waiting_for_subadmin'
            back_markup = telebot.types.InlineKeyboardMarkup()
            back_markup.add(telebot.types.InlineKeyboardButton("🔙 Back", callback_data="admin_back"))
            requests.post(url_edit, json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": "➕ Send user ID for sub-admin:",
                "reply_markup": back_markup.to_json()
            })

print("Bot is running successfully...")
bot.infinity_polling()