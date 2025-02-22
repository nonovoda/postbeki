import os
import logging
import sqlite3
import asyncio
from datetime import datetime
from quart import Quart, request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Проверяем, задан ли токен
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не установлен!")

# Инициализация Telegram-бота и Quart
app = Quart(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# 📌 Инициализация базы данных
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

# 📌 Сохранение конверсии в базу данных
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

# 📌 Отправка сообщения в Telegram
async def send_telegram_message_async(data):
    try:
        message = (
            f"<b>🔔 Новая конверсия!</b>\n\n"
            f"📌 <b>Партнёрская программа:</b> <i>{data.get('pp_name', 'N/A')}</i>\n"
            f"📌 <b>Оффер:</b> <i>{data.get('offer_id', 'N/A')}</i>\n"
            f"🆔 <b>ID конверсии:</b> <i>{data.get('id', 'N/A')}</i>\n"
            f"🤑 <b>Выплата:</b> <i>{data.get('revenue', 'N/A')} {data.get('currency', 'N/A')}</i>\n"
            f"⏰ <b>Время конверсии:</b> <i>{data.get('conversion_date', 'N/A')}</i>"
        )
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
        logger.info("✅ Сообщение отправлено в Telegram.")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения в Telegram: {e}")

# 📌 Обработка webhook-запросов
@app.route('/webhook', methods=['POST'])
async def webhook():
    try:
        data = await request.json
        if not data:
            return "Bad Request: Нет данных", 400

        logger.info(f"📩 Получены данные: {data}")
        save_conversion(data)
        await send_telegram_message_async(data)

        return "OK", 200
    except Exception as e:
        logger.error(f"❌ Ошибка обработки запроса: {e}")
        return "Internal Server Error", 500

# 📌 Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для уведомлений о конверсиях.\nИспользуй /help для списка команд.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = (
        "📋 <b>Список команд:</b>\n"
        "/start - Начать работу\n"
        "/help - Показать список команд\n"
    )
    await update.message.reply_text(commands, parse_mode='HTML')

# 📌 Запуск Telegram-бота
async def run_bot():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 🛠️ Удаляем вебхук перед запуском polling
    await application.bot.delete_webhook(drop_pending_updates=True)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    logger.info("🚀 Telegram-бот запущен!")
    await application.run_polling()

# 📌 Запуск Quart-сервера и Telegram-бота
async def main():
    init_db()  # Инициализация БД
    bot_task = asyncio.create_task(run_bot())  # Запуск бота
    port = int(os.getenv('PORT', 5000))
    await app.run_task(host='0.0.0.0', port=port)  # Запуск сервера

if __name__ == '__main__':
    asyncio.run(main())

# Запуск приложения
if __name__ == '__main__':
    asyncio.run(main())
