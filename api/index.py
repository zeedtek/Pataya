import telebot
from telebot import types
import requests
import json
import os
from flask import Flask, request
from datetime import datetime, timedelta

# إعدادات البروكسي
proxies = {
    'http': 'http://g98avle2nnibnw7-country-dz:jb234f4wt1159yn@rp.scrapegw.com:6060',
    'https': 'http://g98avle2nnibnw7-country-dz:jb234f4wt1159yn@rp.scrapegw.com:6060'
}

TOKEN = '7269311808:AAH-cyNdhw7twKXbql5NAYrfPs3s8K61x8k'
CHANNEL_USERNAME = 'zeedtek'
CHANNEL_LINK = f'https://t.me/{CHANNEL_USERNAME}'
ADMIN_ID = '5000510953'

bot = telebot.TeleBot(TOKEN, threaded=False)
data_file_path = 'djezzy_data.json'

app = Flask(__name__)

# ---------------------------------
# دوال تحميل وحفظ البيانات
# ---------------------------------

def load_user_data():
    if os.path.exists(data_file_path):
        with open(data_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_user_data(data):
    with open(data_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4)

def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ['member', 'creator', 'administrator']
    except:
        return False

def hide_phone_number(phone_number):
    return phone_number[:4] + '*******' + phone_number[-2:]

# ---------------------------------
# تعريف الأوامر
# ---------------------------------

@bot.message_handler(commands=['start'])
def handle_start(msg):
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    if not is_user_subscribed(user_id):
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("✅ اشترك الآن في القناة", url=CHANNEL_LINK)
        markup.add(btn)
        bot.send_photo(
            chat_id,
            photo='https://telegra.ph/file/cf4a0d3e021caa99e3ba7.jpg',
            caption=(
                "✳️ *مرحبًا بك في بوت Zeed Tek!*\n\n"
                "> قناة [Zeed Tek](https://t.me/zeedtek) تقدم لك:\n"
                "• خدمات انترنت مجانية.\n"
                "• عروض وهدايا حصرية لمستخدمي Djezzy.\n\n"
                "*اشترك أولاً في القناة لتبدأ!*"
            ),
            reply_markup=markup,
            parse_mode='Markdown'
        )
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎁 احصل على هديتك", callback_data='walkwingift'),
        types.InlineKeyboardButton("📱 إرسال رقم الهاتف", callback_data='send_number')
    )

    bot.send_message(
        chat_id,
        "✨ *مرحبًا بك من جديد!*\n\n"
        "• اضغط على الزر المناسب لبدء استخدام البوت.",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'send_number')
def handle_send_number(callback_query):
    chat_id = callback_query.message.chat.id
    bot.send_message(chat_id, '📱 أرسل رقم هاتفك Djezzy الذي يبدأ بـ 07:')
    bot.register_next_step_handler_by_chat_id(chat_id, handle_phone_number)

def send_otp(msisdn):
    url = 'https://apim.djezzy.dz/oauth2/registration'
    payload = f'msisdn={msisdn}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxies, verify=False)
        return response.status_code == 200
    except:
        return False

def handle_phone_number(msg):
    chat_id = msg.chat.id
    text = msg.text
    if text.startswith('07') and len(text) == 10:
        msisdn = '213' + text[1:]
        if send_otp(msisdn):
            bot.send_message(chat_id, '🔢 تم إرسال رمز OTP. أدخله الآن:')
            bot.register_next_step_handler_by_chat_id(chat_id, lambda msg: handle_otp(msg, msisdn))
        else:
            bot.send_message(chat_id, '⚠️ فشل إرسال رمز OTP.')
    else:
        bot.send_message(chat_id, '⚠️ أدخل رقمًا صحيحًا يبدأ بـ 07.')

def verify_otp(msisdn, otp):
    url = 'https://apim.djezzy.dz/oauth2/token'
    payload = f'otp={otp}&mobileNumber={msisdn}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxies, verify=False)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def handle_otp(msg, msisdn):
    chat_id = msg.chat.id
    otp = msg.text
    tokens = verify_otp(msisdn, otp)
    if tokens:
        user_data = load_user_data()
        user_data[str(chat_id)] = {
            'username': msg.from_user.username,
            'telegram_id': chat_id,
            'msisdn': msisdn,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'last_applied': None
        }
        save_user_data(user_data)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎁 استلام الهدية", callback_data='walkwingift'))
        bot.send_message(chat_id, '✅ تم التحقق بنجاح! اضغط على الزر لاستلام هديتك:', reply_markup=markup)
    else:
        bot.send_message(chat_id, '⚠️ رمز OTP غير صحيح.')

def apply_gift(chat_id, msisdn, access_token, username, name):
    user_data = load_user_data()
    last_applied = user_data.get(str(chat_id), {}).get('last_applied')
    if last_applied:
        last_applied_time = datetime.fromisoformat(last_applied)
        if datetime.now() - last_applied_time < timedelta(days=1):
            bot.send_message(chat_id, "⚠️ لا يمكنك استخدام الهدية الآن. الرجاء الانتظار 24 ساعة.")
            return False

    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product?include='
    payload = {
        "data": {
            "id": "TransferInternet2Go",
            "type": "products",
            "meta": {
                "services": {
                    "steps": 10000,
                    "code": "FAMILY4000",
                    "id": "WALKWIN"
                }
            }
        }
    }
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    try:
        response = requests.post(url, json=payload, headers=headers, proxies=proxies, verify=False)
        res_data = response.json()
        if "successfully done" in res_data.get('message', ''):
            hidden = hide_phone_number(msisdn)
            bot.send_message(chat_id, f"🎉 تم تفعيل الانترنت بنجاح!\n\n👤 الاسم: {name}\n🧑‍💻 المستخدم: @{username}\n📞 الرقم: {hidden}")
            user_data[str(chat_id)]['last_applied'] = datetime.now().isoformat()
            save_user_data(user_data)
            return True
        else:
            bot.send_message(chat_id, f"⚠️ خطأ: {res_data.get('message', 'غير معروف')}")
            return False
    except:
        bot.send_message(chat_id, "⚠️ حدث خطأ أثناء تفعيل الهدية.")
        return False

@bot.callback_query_handler(func=lambda call: call.data == 'walkwingift')
def handle_walkwingift(call):
    chat_id = call.message.chat.id
    user_data = load_user_data()
    if str(chat_id) in user_data:
        user = user_data[str(chat_id)]
        apply_gift(chat_id, user['msisdn'], user['access_token'], user['username'], call.from_user.first_name)

# ---------------------------------
# إعدادات Vercel
# ---------------------------------

@app.route('/api/index', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def home():
    return 'Bot Running!', 200

# لا تنس ضبط webhook خارجيا لمرة واحدة عبر طلب HTTP.
