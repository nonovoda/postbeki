import os
import logging
import sqlite3
from datetime import datetime
from quart import Quart, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import uvicorn

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    logger.error("Токен бота или Chat ID не найдены в переменных окружения!")
    exit(1)

# Инициализация Quart и Telegram бота
app = Quart(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Инициализация базы данных
def init_db():
    with sqlite3.connect('conversions.db') as conn:
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

# Сохранение конверсии в базу данных
def save_conversion(data):
    with sqlite3.connect('conversions.db') as conn:
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

# Эндпоинт для обработки GET и POST запросов
@app.route('/webhook', methods=['GET', 'POST'])
async def webhook():
    try:
        data = await request.get_json() if request.method == 'POST' else request.args
        logger.info(f"Получены данные: {data}")
        if not data:
            return 'Bad Request: Данные отсутствуют', 400
        await asyncio.to_thread(save_conversion, data)
        await send_telegram_message_async(data)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        return 'Internal Server Error', 500

# Запуск приложения
if __name__ == "__main__":
    init_db()
    asyncio.create_task(send_telegram_message_async({}))  # Запуск Telegram-бота
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
