from quart import Quart, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import logging
import sqlite3
from datetime import datetime
import asyncio

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка конфигурации из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Токен Telegram-бота
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')  # Chat ID для отправки сообщений

# Инициализация Quart и Telegram бота
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
    """
    Формирует и отправляет сообщение в Telegram.
    """
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
    """
    Обрабатывает GET и POST запросы.
    """
    try:
        if request.method == 'POST':
            data = await request.json  # Данные из POST-запроса
        else:
            data = request.args  # Данные из GET-запроса

        # Логирование данных запроса
        logger.info(f"Получены данные: {data}")

        if data is None:
            logger.error("Данные запроса отсутствуют или равны None.")
            return 'Bad Request: Данные отсутствуют', 400

        # Формируем данные для отправки в Telegram
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

        # Сохраняем конверсию в базу данных
        save_conversion(message_data)

        # Логирование сформированных данных
        logger.info(f"Сформированные данные для Telegram: {message_data}")

        # Запускаем асинхронную задачу
        await send_telegram_message_async(message_data)
        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        return 'Internal Server Error', 500

# Эндпоинт для favicon.ico
@app.route('/favicon.ico')
async def favicon():
    return '', 204  # Возвращаем пустой ответ

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

# Функция для запуска бота
async def run_bot():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    await application.run_polling()

# Запуск Quart-сервера и бота
async def main():
    init_db()  # Инициализация базы данных

    # Запуск бота в фоновом режиме
    bot_task = asyncio.create_task(run_bot())

    # Запуск Quart-сервера
    port = int(os.getenv('PORT', 5000))  # Используем порт из переменной окружения или 5000 по умолчанию
    await app.run_task(host='0.0.0.0', port=port)

# Запуск приложения
if __name__ == '__main__':
    asyncio.run(main())
