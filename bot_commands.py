from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
from datetime import datetime
import os
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Токен Telegram-бота

# Функция для получения статистики
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

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Статистика за сегодня", callback_data='stats_today')],
        [InlineKeyboardButton("Статистика за месяц", callback_data='stats_month')],
        [InlineKeyboardButton("Отключить уведомления", callback_data='mute')],
        [InlineKeyboardButton("Включить уведомления", callback_data='unmute')],
        [InlineKeyboardButton("Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

# Обработка callback-запросов
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'stats_today':
        today = datetime.now().strftime('%Y-%m-%d')
        stats_data = get_statistics(start_date=today)
        message = format_stats_message(stats_data, "Статистика за сегодня")
    elif query.data == 'stats_month':
        first_day_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        stats_data = get_statistics(start_date=first_day_of_month)
        message = format_stats_message(stats_data, "Статистика за месяц")
    elif query.data == 'mute':
        message = "🔕 Уведомления отключены."
    elif query.data == 'unmute':
        message = "🔔 Уведомления включены."
    elif query.data == 'help':
        message = (
            "📋 Список команд:\n"
            "/start - Начать работу с ботом\n"
            "/stats - Получить статистику\n"
            "Используйте кнопки для быстрых действий."
        )

    await query.edit_message_text(text=message, parse_mode='HTML')

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
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()
