import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logger.error("Токен бота не найден в переменных окружения!")
    exit(1)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для уведомлений о конверсиях.\n"
        "Используй /help для списка команд."
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = (
        "📋 Список доступных команд:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список команд\n"
        "/stats_today - Получить статистику за сегодня\n"
        "/stats_month - Получить статистику за месяц"
    )
    await update.message.reply_text(commands)

# Команда /stats_today
async def stats_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        stats_data = get_statistics(start_date=today)
        message = format_stats_message(stats_data, "Статистика за сегодня")
        await update.message.reply_text(message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка при получении статистики за сегодня: {e}")
        await update.message.reply_text("Произошла ошибка при получении статистики.")

# Команда /stats_month
async def stats_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_day_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    try:
        stats_data = get_statistics(start_date=first_day_of_month)
        message = format_stats_message(stats_data, "Статистика за месяц")
        await update.message.reply_text(message, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка при получении статистики за месяц: {e}")
        await update.message.reply_text("Произошла ошибка при получении статистики.")

# Функция для получения статистики
def get_statistics(start_date=None, end_date=None, offer_id=None, pp_name=None):
    try:
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
    except sqlite3.Error as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")
        return None

# Форматирование сообщения со статистикой
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

# Запуск бота
if __name__ == '__main__':
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats_today", stats_today))
    application.add_handler(CommandHandler("stats_month", stats_month))
    application.run_polling()
