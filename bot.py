import os
import logging
import sqlite3
from datetime import datetime
import asyncio

from quart import Quart, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')       # Токен Telegram-бота
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')           # Chat ID для отправки сообщений
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')     # Базовый URL приложения (например, https://your-app.up.railway.app)

if not TELEGRAM_WEBHOOK_URL:
    logger.error("Переменная окружения TELEGRAM_WEBHOOK_URL не задана!")
    exit(1)

# Инициализация Quart и Telegram-бота
app = Quart(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('conversions.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pp_name TEXT,
            offer_id TEXT,
            conversion_date TEXT,
            revenue REAL,
            currency TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Сохранение конверсии в базу данных
def save_conversion(data):
    conn = sqlite3.connect('conversions.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversions (pp_name, offer_id, conversion_date, revenue, currency)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('pp_name', 'N/A'),
        data.get('offer_id', 'N/A'),
        data.get('conversion_date', 'N/A'),
        data.get('revenue', 0),
        data.get('currency', 'N/A')
    ))
    conn.commit()
    conn.close()

# Асинхронная функция для отправки сообщения в Telegram
async def send_telegram_message_async(data):
    try:
        message = (
            f"<b>🔔 Новая конверсия!</b>\n\n"
            f"📌 <b>Партнёрская программа:</b> <i>{data.get('pp_name', 'N/A')}</i>\n"
            f"📌 <b>Оффер:</b> <i>{data.get('offer_id', 'N/A')}</i>\n"
            f"🆔 <b>ID конверсии:</b> <i>{data.get('id', 'N/A')}</i>\n"
            f"🛠 <b>Подход:</b> <i>{data.get('sub_id3', 'N/A')}</i>\n"
            f"📊 <b>Тип конверсии:</b> <i>{data.get('goal', 'N/A')}</i>\n"
            f"⚙️ <b>Статус конверсии:</b> <i>{data.get('status', 'N/A')}</i>\n"
            f"🤑 <b>Выплата:</b> <i>{data.get('revenue', 'N/A')} {data.get('currency', 'N/A')}</i>\n"
            f"🎯 <b>Кампания:</b> <i>{data.get('sub_id4', 'N/A')}</i>\n"
            f"🎯 <b>Адсет:</b> <i>{data.get('sub_id5', 'N/A')}</i>\n"
            f"⏰ <b>Время конверсии:</b> <i>{data.get('conversion_date', 'N/A')}</i>"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
        logger.info("Сообщение успешно отправлено в Telegram.")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")

# Эндпоинт для обработки постбеков от партнёрских программ
@app.route('/webhook', methods=['GET', 'POST'])
async def webhook():
    try:
        if request.method == 'POST':
            data = await request.json  # Данные из POST-запроса
        else:
            data = request.args  # Данные из GET-запроса

        logger.info(f"Получены данные постбека: {data}")
        if data is None:
            logger.error("Данные запроса отсутствуют или равны None.")
            return 'Bad Request: Данные отсутствуют', 400

        message_data = {
            'pp_name': data.get('pp_name', 'N/A'),
            'offer_id': data.get('offer_id', 'N/A'),
            'id': data.get('id', 'N/A'),
            'sub_id3': data.get('sub_id3', 'N/A'),
            'goal': data.get('goal', 'N/A'),
            'status': data.get('status', 'N/A'),
            'revenue': data.get('revenue', 'N/A'),
            'currency': data.get('currency', 'N/A'),
            'sub_id4': data.get('sub_id4', 'N/A'),
            'sub_id5': data.get('sub_id5', 'N/A'),
            'conversion_date': data.get('conversion_date', 'N/A')
        }

        save_conversion(message_data)
        logger.info(f"Сформированные данные для Telegram: {message_data}")
        await send_telegram_message_async(message_data)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка при обработке постбека: {e}")
        return 'Internal Server Error', 500

# Эндпоинт для обработки обновлений от Telegram (команды)
@app.route('/telegram', methods=['POST'])
async def telegram_webhook():
    try:
        update_json = await request.get_json()
        update = Update.de_json(update_json, bot)
        # Передаём обновление в telegram_app для обработки команд
        await telegram_app.process_update(update)
        return jsonify({"ok": True})
    except Exception as e:
        logger.error(f"Ошибка при обработке Telegram обновления: {e}")
        return jsonify({"ok": False}), 500

def get_statistics(start_date=None, end_date=None, offer_id=None, pp_name=None):
    conn = sqlite3.connect('conversions.db')
    cursor = conn.cursor()

    query = '''
        SELECT pp_name, offer_id, SUM(revenue), COUNT(*)
        FROM conversions
        WHERE 1=1
    '''
    params = []
    if start_date:
        query += ' AND conversion_date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND conversion_date <= ?'
        params.append(end_date)
    if offer_id:
        query += ' AND offer_id = ?'
        params.append(offer_id)
    if pp_name:
        query += ' AND pp_name = ?'
        params.append(pp_name)
    query += ' GROUP BY pp_name, offer_id'
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

def format_stats_message(stats_data, title):
    if not stats_data:
        return f"📊 {title}:\n\nНет данных."
    message = f"📊 {title}:\n\n"
    for row in stats_data:
        pp_name, offer_id, total_revenue, total_conversions = row
        message += (
            f"📌 Партнёрская программа: <i>{pp_name}</i>\n"
            f"📌 Оффер: <i>{offer_id}</i>\n"
            f"🤑 Общая выплата: <i>{total_revenue}</i>\n"
            f"📊 Конверсий: <i>{total_conversions}</i>\n\n"
        )
    return message

# Обработчики команд Telegram
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для уведомлений о конверсиях.\n"
        "Используй /help для списка команд."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = (
        "📋 Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список команд\n"
        "/stats_today - Получить статистику за сегодня\n"
        "/stats_month - Получить статистику за месяц"
    )
    await update.message.reply_text(commands)

async def stats_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%Y-%m-%d')
    stats_data = get_statistics(start_date=today)
    message = format_stats_message(stats_data, "Статистика за сегодня")
    await update.message.reply_text(message, parse_mode='HTML')

async def stats_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_day_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    stats_data = get_statistics(start_date=first_day_of_month)
    message = format_stats_message(stats_data, "Статистика за месяц")
    await update.message.reply_text(message, parse_mode='HTML')

# Создаём и настраиваем telegram.ext Application для обработки команд
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start_command))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("stats_today", stats_today))
telegram_app.add_handler(CommandHandler("stats_month", stats_month))

# Функция для установки вебхука Telegram
async def set_telegram_webhook():
    full_url = TELEGRAM_WEBHOOK_URL.rstrip('/') + '/telegram'
    await bot.set_webhook(url=full_url)
    logger.info(f"Webhook для Telegram установлен: {full_url}")

# Основная функция запуска приложения
async def main():
    init_db()
    await set_telegram_webhook()
    # Инициализируем telegram_app перед получением обновлений
    await telegram_app.initialize()
    port = int(os.getenv('PORT', 8080))
    await app.run_task(host='0.0.0.0', port=port)

if __name__ == '__main__':
    asyncio.run(main())

