# ====================================================
# بوت إسلامي - Google Colab
# !pip install python-telegram-bot pytz requests nest_asyncio
# ====================================================

import logging
import sqlite3
import random
import requests
import pytz
import asyncio
import nest_asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

nest_asyncio.apply()

# ================== 1. الإعدادات ==================
TOKEN        = "8677540047:AAHLWREiPpQayhDhdFbwwNht4YmQRWgGFzs"
CHANNEL_URL  = "https://t.me/Al_Jalab_2220"
CHANNEL_NAME = "عِــلْـــمٌ يُـنْـتَـفَـعُ بِــهْ"
TIMEZONE     = pytz.timezone('Asia/Jerusalem')
CITY         = "Jerusalem"
COUNTRY      = "Palestine"
BUKHARI_COUNT = 7563  # عدد أحاديث البخاري في الـ API

def watermark_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📢 {CHANNEL_NAME}", url=CHANNEL_URL)]
    ])

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================== 2. قاعدة البيانات ==================
def init_db():
    conn   = sqlite3.connect('islamic_bot.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY)')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_quotes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            quote   TEXT UNIQUE,
            sent_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_hadiths (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            hadith_num INTEGER UNIQUE,
            sent_at    TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_ayahs (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            ayah_num INTEGER UNIQUE,
            sent_at  TEXT
        )
    ''')
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# ================== 3. أقوال الشيوخ ==================
LOCAL_QUOTES = [
    'قال شيخ الإسلام ابن تيمية رحمه الله: ما يصنع أعدائي بي؟ أنا جنتي وبستاني في صدري، إن كانوا يريدون نفيي فنفيي خلوة، وإن قتلوني فقتلي شهادة.',
    'قال ابن القيم رحمه الله: في القلب شعثٌ لا يلمّه إلا الإقبال على الله، وغربةٌ لا يُزيلها إلا الأنس به، وحزنٌ لا يُذهبه إلا السرور بمعرفته.',
    'قال الشيخ عبد العزيز الطريفي حفظه الله: الحق لا يضعف بموت أصحابه، بل بضعف التمسك به.',
    'قال الشيخ سليمان العلوان حفظه الله: من أعظم أسباب الثبات لزوم القرآن تلاوةً وتدبراً وعملاً.',
    'قال الشيخ نائل مصران تقبّله الله: الطريق إلى الله يُقطع بالقلوب لا بالأقدام.',
    'قال ابن تيمية رحمه الله: من أراد السعادة الأبدية فليلزم عتبة العبودية.',
    'قال ابن الجوزي رحمه الله: اغتنم في الفراغ فضل ركوعٍ، فعسى أن يأتي شغلٌ أو مرض.',
    'قال الإمام أحمد رحمه الله: ما كتبتُ حديثاً إلا وعملتُ به، حتى مررتُ بحديث الحجامة فأعطيتُ الحجّام درهماً.',
    'قال الشيخ ابن عثيمين رحمه الله: إذا أحببتَ أن تعرف قدرك عند الله فانظر فيما أقامك.',
    'قال الشيخ ابن باز رحمه الله: الصبر والعلم والإيمان أُسس النصر، فمن فقدها فقد طريق الفلاح.',
    'قال ابن القيم رحمه الله: الدنيا مزرعة الآخرة، فمن زرع فيها خيراً حصد في الآخرة سروراً، ومن زرع شراً حصد ندماً.',
    'قال الحسن البصري رحمه الله: ابن آدم، كيف تطيب نفسك بالحياة وأنت تعلم أنك ميت؟',
    'قال ابن القيم رحمه الله: الذكر للقلب كالماء للسمكة، فما حال السمكة إذا فارقت الماء؟',
    'قال الشيخ ابن عثيمين رحمه الله: من أراد عزّ الدنيا والآخرة فليلزم طاعة الله.',
    'قال ابن تيمية رحمه الله: العبادة هي الغاية المحبوبة لله والمرضية له التي خلق الخلق لها.',
    'قال ابن القيم رحمه الله: كلما ازداد العبد معرفةً بربه ازداد خوفاً منه ورجاءً فيه.',
    'قال الشيخ ابن باز رحمه الله: من أعظم أسباب السعادة الإكثار من ذكر الله في كل وقت.',
    'قال الإمام الشافعي رحمه الله: من أراد الدنيا فعليه بالعلم، ومن أراد الآخرة فعليه بالعلم.',
    'قال الإمام مالك رحمه الله: لا يصلح آخر هذه الأمة إلا بما صلح به أولها.',
    'قال الحسن البصري رحمه الله: من عرف ربه أحبّه، ومن عرف الدنيا زهد فيها.',
    'قال ابن القيم رحمه الله: أعظم الناس عقوبةً في الآخرة أعظمهم منزلةً في الدنيا مع تفريطه في طاعة الله.',
    'قال الإمام الشافعي رحمه الله: العلم ما نفع، ليس العلم ما حُفظ.',
    'قال ابن تيمية رحمه الله: التوكل على الله مع الأخذ بالأسباب من تمام الإيمان.',
    'قال ابن الجوزي رحمه الله: رأيت العلم يدعو إلى العمل، فإن أجاب وإلا ارتحل.',
]

def get_non_repeated_quote():
    cursor.execute('SELECT quote FROM sent_quotes')
    sent = {row[0] for row in cursor.fetchall()}
    available = [q for q in LOCAL_QUOTES if q not in sent]
    if not available:
        cursor.execute('DELETE FROM sent_quotes')
        conn.commit()
        available = LOCAL_QUOTES
    chosen = random.choice(available)
    cursor.execute(
        'INSERT OR IGNORE INTO sent_quotes (quote, sent_at) VALUES (?, ?)',
        (chosen, datetime.now(TIMEZONE).isoformat())
    )
    conn.commit()
    return f"📌 *{chosen}*"

# ================== 4. أحاديث البخاري من GitHub API ==================
def get_non_repeated_hadith_online() -> str:
    """
    تجلب حديثاً عشوائياً من صحيح البخاري عبر GitHub CDN API
    7563 حديث — لا تكرار حتى تنتهي الدورة كاملة
    """
    cursor.execute('SELECT hadith_num FROM sent_hadiths')
    sent_nums = {row[0] for row in cursor.fetchall()}

    if len(sent_nums) >= BUKHARI_COUNT:
        cursor.execute('DELETE FROM sent_hadiths')
        conn.commit()
        sent_nums = set()

    for _ in range(25):
        num = random.randint(1, BUKHARI_COUNT)
        if num in sent_nums:
            continue
        try:
            url = f"https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari/{num}.min.json"
            res = requests.get(url, timeout=15)
            if res.status_code != 200:
                continue
            data = res.json()
            hadiths = data.get('hadith', [])
            if not hadiths:
                continue
            text = hadiths[0].get('text', '').strip()
            if not text or len(text) < 20:
                continue

            cursor.execute(
                'INSERT OR IGNORE INTO sent_hadiths (hadith_num, sent_at) VALUES (?, ?)',
                (num, datetime.now(TIMEZONE).isoformat())
            )
            conn.commit()

            return (
                f"📜 *حديث من صحيح البخاري*\n\n"
                f"{text}\n\n"
                f"_📚 صحيح البخاري — رقم {num}_"
            )
        except Exception as e:
            logging.warning(f"فشل جلب الحديث رقم {num}: {e}")

    # fallback لو انقطع الإنترنت
    return (
        "📜 *حديث من صحيح البخاري*\n\n"
        "قال رسول الله ﷺ: «إنما الأعمال بالنيات، وإنما لكل امرئٍ ما نوى»\n\n"
        "_📚 صحيح البخاري_"
    )

# ================== 5. آية قرآنية مع تفسير ==================
def get_non_repeated_ayah() -> str:
    """
    تجلب آية عشوائية مع تفسيرها الميسر — 6236 آية بدون تكرار
    """
    cursor.execute('SELECT ayah_num FROM sent_ayahs')
    sent_nums = {row[0] for row in cursor.fetchall()}

    if len(sent_nums) >= 6236:
        cursor.execute('DELETE FROM sent_ayahs')
        conn.commit()
        sent_nums = set()

    for _ in range(25):
        num = random.randint(1, 6236)
        if num in sent_nums:
            continue
        try:
            ayah_res   = requests.get(f'https://api.alquran.cloud/v1/ayah/{num}/ar.alafasy', timeout=15)
            tafsir_res = requests.get(f'https://api.alquran.cloud/v1/ayah/{num}/ar.muyassar', timeout=15)

            if ayah_res.status_code != 200 or tafsir_res.status_code != 200:
                continue

            ayah_data   = ayah_res.json().get('data', {})
            tafsir_data = tafsir_res.json().get('data', {})
            ayah_text   = ayah_data.get('text', '').strip()
            tafsir_text = tafsir_data.get('text', '').strip()
            surah_name  = ayah_data.get('surah', {}).get('name', '')
            ayah_num_in_surah = ayah_data.get('numberInSurah', '')

            if not ayah_text or not tafsir_text:
                continue

            cursor.execute(
                'INSERT OR IGNORE INTO sent_ayahs (ayah_num, sent_at) VALUES (?, ?)',
                (num, datetime.now(TIMEZONE).isoformat())
            )
            conn.commit()

            return (
                f"📖 *{surah_name} — الآية {ayah_num_in_surah}*\n\n"
                f"﴿{ayah_text}﴾\n\n"
                f"💡 *التفسير الميسر:*\n{tafsir_text}"
            )
        except Exception as e:
            logging.warning(f"فشل جلب الآية رقم {num}: {e}")

    return (
        "📖 *من كتاب الله*\n\n"
        "﴿إِنَّ مَعَ الْعُسْرِ يُسْرًا﴾\n\n"
        "💡 *التفسير:* إن مع الشدة فرجاً ومخرجاً وتيسيراً."
    )

# ================== 6. أوقات الصلاة ==================
prayer_times: dict = {}

def update_prayers():
    global prayer_times
    try:
        url = f"https://api.aladhan.com/v1/timingsByCity?city={CITY}&country={COUNTRY}&method=5"
        res = requests.get(url, timeout=20)
        if res.status_code == 200:
            prayer_times = res.json()['data']['timings']
            logging.info("تم تحديث أوقات الصلاة.")
    except Exception as e:
        logging.error(f"خطأ في أوقات الصلاة: {e}")

async def broadcast(context, text: str, keyboard=None):
    cursor.execute('SELECT group_id FROM groups')
    for row in cursor.fetchall():
        try:
            await context.bot.send_message(
                chat_id=row[0],
                text=text,
                parse_mode='Markdown',
                reply_markup=keyboard or watermark_keyboard(),
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"فشل الإرسال للمجموعة {row[0]}: {e}")

async def adhan_reminder(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE).strftime('%H:%M')
    if now == '00:01':
        update_prayers()
    prayers = {
        'Fajr': 'الفجر', 'Dhuhr': 'الظهر',
        'Asr': 'العصر', 'Maghrib': 'المغرب', 'Isha': 'العشاء',
    }
    for eng, ara in prayers.items():
        if prayer_times.get(eng) == now:
            msg = (
                f"🕌 *حان الآن موعد أذان {ara}*\n"
                f"بتوقيت القدس المحتلة\n\n"
                f"قال ﷺ: «أرحنا بها يا بلال»"
            )
            await broadcast(context, msg)

# ================== 7. المعالجات ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🌿 *أهلاً بك في بوت علم ينتفع به*\n\n'
        'أرسل *تفعيل* لتفعيل البث التلقائي في مجموعتك',
        parse_mode='Markdown',
        reply_markup=watermark_keyboard()
    )

async def activate_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute('INSERT OR IGNORE INTO groups VALUES (?)', (update.effective_chat.id,))
    conn.commit()
    await update.message.reply_text(
        '✅ *تم تفعيل البث التلقائي بنجاح*\n\n'
        'ستصلكم:\n'
        '🕌 تنبيهات أوقات الصلاة\n'
        '📌 قول من أقوال الشيوخ كل ساعة\n'
        '✨ تذكير بالصلاة على النبي ﷺ كل ساعة\n'
        '📜 حديث من صحيح البخاري كل 6 ساعات\n'
        '📖 آية قرآنية مع تفسيرها كل 4 ساعات',
        parse_mode='Markdown',
        reply_markup=watermark_keyboard()
    )

# ================== 8. البث التلقائي ==================
async def scheduled_quote(context: ContextTypes.DEFAULT_TYPE):
    await broadcast(context, get_non_repeated_quote())

async def hourly_salawat(context: ContextTypes.DEFAULT_TYPE):
    msg = (
        '✨ *تذكير بالصلاة على النبي ﷺ*\n\n'
        '﴿إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ ۚ '
        'يَا أَيُّهَا الَّذِينَ آمَنُوا صَلُّوا عَلَيْهِ وَسَلِّمُوا تَسْلِيمًا﴾\n\n'
        '*اللهم صلِّ وسلِّم وبارك على نبينا محمد ﷺ*'
    )
    await broadcast(context, msg)

async def scheduled_hadith(context: ContextTypes.DEFAULT_TYPE):
    text = get_non_repeated_hadith_online()
    await broadcast(context, text)

async def scheduled_ayah(context: ContextTypes.DEFAULT_TYPE):
    text = get_non_repeated_ayah()
    await broadcast(context, text)

async def keep_alive(context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"keep-alive — {datetime.now(TIMEZONE).strftime('%H:%M:%S')}")

# ================== 9. التشغيل ==================
def main():
    update_prayers()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Regex('^تفعيل$'), activate_group))

    jq = app.job_queue
    jq.run_repeating(adhan_reminder,   interval=60,    first=10)
    jq.run_repeating(scheduled_quote,  interval=3600,  first=60)
    jq.run_repeating(hourly_salawat,   interval=3600,  first=120)
    jq.run_repeating(scheduled_hadith, interval=21600, first=180)
    jq.run_repeating(scheduled_ayah,   interval=14400, first=240)
    jq.run_repeating(keep_alive,       interval=300,   first=300)

    print('🚀 البوت يعمل الآن...')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    ))

if __name__ == '__main__':
    main()
