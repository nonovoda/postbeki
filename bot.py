import os
import logging
import aiosqlite
from datetime import datetime, timedelta
import asyncio

from quart import Quart, request, jsonify
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Запись логов в файл
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')

if not TELEGRAM_WEBHOOK_URL:
    logger.error("Переменная окружения TELEGRAM_WEBHOOK_URL не задана!")
    exit(1)

# Инициализация Quart и Telegram-бота
app = Quart(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Инициализация базы данных
async def init_db():
    async with aiosqlite.connect("conversions.db") as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pp_name TEXT,
                offer_id TEXT,
                conversion_date TEXT,
                revenue REAL,
                currency TEXT,
                status TEXT
            )
        ''')
        await conn.commit()

# Асинхронное сохранение данных в базу
async def save_conversion(data):
    async with aiosqlite.connect("conversions.db") as conn:
        await conn.execute('''
            INSERT INTO conversions (pp_name, offer_id, conversion_date, revenue, currency, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('pp_name', 'N/A'),
            data.get('offer_id', 'N/A'),
            data.get('conversion_date', 'N/A'),
            data.get('revenue', 0),
            data.get('currency', 'N/A'),
            data.get('status', 'N/A')
        ))
        await conn.commit()

# Улучшенный Webhook с проверкой результата
async def set_telegram_webhook():
    full_url = TELEGRAM_WEBHOOK_URL.rstrip('/') + '/telegram'
    response = await bot.set_webhook(url=full_url)
    if response:
        logger.info(f"Webhook для Telegram установлен: {full_url}")
    else:
        logger.error("Ошибка установки Webhook!")
        exit(1)

# Эндпоинт для постбеков
@app.route('/webhook', methods=['POST'])
async def webhook():
    try:
        data = await request.get_json()
        logger.info(f"Получены данные: {data}")  # Лог перед обработкой

        if not data:
            logger.error("Данные запроса отсутствуют.")
            return jsonify({"error": "Bad Request: No data"}), 400

        await save_conversion(data)  # Сохранение в БД
        await send_telegram_message_async(data)  # Отправка в Telegram
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        logger.error(f"Ошибка при обработке постбека: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# Асинхронная функция для отправки сообщений в Telegram
async def send_telegram_message_async(data):
    try:
        message = (
            f"📌 Оффер: {data.get('offer_id', 'N/A')}\n"
            f"⚙️ Статус: {data.get('status', 'N/A')}\n"
            f"🤑 Выплата: {data.get('revenue', 'N/A')} {data.get('currency', 'N/A')}\n"
            f"⏰ Время: {data.get('conversion_date', 'N/A')}"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка при отправке в Telegram: {e}")

# Запуск приложения
async def main():
    await init_db()
    await set_telegram_webhook()
    port = int(os.getenv('PORT', 8080))
    await app.run_task(host='0.0.0.0', port=port)

if __name__ == '__main__':
    asyncio.run(main())

