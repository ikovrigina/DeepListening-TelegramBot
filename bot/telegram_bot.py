#!/usr/bin/env python3
"""
DeepListening Telegram Bot

Телеграм-бот для сохранения сообщений в Supabase.
Автоматически сохраняет все текстовые сообщения в базу данных
и отвечает "Сохранил" на каждое сообщение.
"""

import os
import logging
import requests
import json
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        # Получаем переменные окружения
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not all([self.bot_token, self.supabase_url, self.supabase_key]):
            raise ValueError("Не все переменные окружения установлены!")
        
        # Настраиваем заголовки для Supabase API
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Создаем приложение бота
        self.application = Application.builder().token(self.bot_token).build()
        
        # Добавляем обработчики
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настраиваем обработчики сообщений"""
        # Обработчик всех текстовых сообщений
        message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        self.application.add_handler(message_handler)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатываем входящие сообщения"""
        try:
            message = update.message
            user = message.from_user
            
            # Подготавливаем данные для сохранения
            message_data = {
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'message_text': message.text,
                'message_id': message.message_id,
                'chat_id': message.chat_id,
                'created_at': datetime.now().isoformat()
            }
            
            # Сохраняем в Supabase через REST API
            api_url = f"{self.supabase_url}/rest/v1/telegram_messages"
            
            response = requests.post(
                api_url,
                headers=self.headers,
                data=json.dumps(message_data)
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Сообщение сохранено: {message.text[:50]}...")
                # Отправляем подтверждение
                await message.reply_text("Сохранил")
            else:
                logger.error(f"Ошибка сохранения: {response.status_code} - {response.text}")
                await message.reply_text("Ошибка при сохранении сообщения")
                
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
            await message.reply_text("Произошла ошибка при обработке сообщения")
    
    def run(self):
        """Запускаем бота"""
        logger.info("Запускаем телеграм-бота...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Главная функция"""
    try:
        bot = TelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == '__main__':
    main()
