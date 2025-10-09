#!/usr/bin/env python3
"""
Простой тест бота для проверки деплоя
"""
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🎉 Тест успешен! Бот работает на Railway!\n"
        f"Ваш ID: {update.effective_user.id}\n"
        f"Время: {update.message.date}"
    )

def main():
    """Запуск бота"""
    # Получаем токен
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден!")
        return
    
    logger.info("Запускаем тестовый бот...")
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    
    # Запускаем бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
