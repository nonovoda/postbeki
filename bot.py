import os
import logging
import sqlite3
from datetime import datetime, timedelta
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
                currency TEXT,
                status TEXT
            )
        ''')
        conn.commit()

# Получение статистики за определённый период
def get_statistics(start_date, end_date):
    with sqlite3.connect("conversions.db") as conn:
        cursor = conn.cursor()
        query = '''
            SELECT 
                COUNT(*) AS total, 
                SUM(revenue) AS total_revenue, 
                SUM(CASE WHEN status = "approved" THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN status = "pending" THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = "rejected" THEN 1 ELSE 0 END) AS rejected
            FROM conversions
            WHERE conversion_date BETWEEN ? AND ?
        '''
        cursor.execute(query, (start_date, end_date))
        result = cursor.fetchone()
        return result

# Форматирование статистики для отправки в Telegram
def format_stats_message(stats_data, title):
    if not stats_data or stats_data[0] is None:
        return f"📊 {title}:

Нет данных за выбранный период."

    message = (
        f"📊 <b>{title}</b>\n"
        f"✅ Утверждено: <b>{stats_data[2]}</b>\n"
        f"⏳ В ожидании: <b>{stats_data[3]}</b>\n"
        f"❌ Отклонено: <b>{stats_data[4]}</b>\n"
        f"💰 Общая выплата: <b>{stats_data[1] if stats_data[1] else 0} $</b>"
    )
    return message

# Команды Telegram для отображения статистики
async def stats_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%Y-%m-%d')
    stats_data = await asyncio.to_thread(get_statistics, today, today)
    message = format_stats_message(stats_data, "Статистика за сегодня")
    await update.message.reply_text(message, parse_mode="HTML")

async def stats_week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    stats_data = await asyncio.to_thread(get_statistics, start_week, today)
    message = format_stats_message(stats_data, "Статистика за неделю")
    await update.message.reply_text(message, parse_mode="HTML")

async def stats_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_day_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    stats_data = await asyncio.to_thread(get_statistics, first_day_of_month, today)
    message = format_stats_message(stats_data, "Статистика за месяц")
    await update.message.reply_text(message, parse_mode="HTML")

# Запуск Telegram-бота
async def run_bot():
    logger.info("Запуск Telegram бота...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("stats_today", stats_today))
    application.add_handler(CommandHandler("stats_week", stats_week))
    application.add_handler(CommandHandler("stats_month", stats_month))
    await application.run_polling()

# Запуск приложения
if __name__ == "__main__":
    init_db()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run_bot())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
