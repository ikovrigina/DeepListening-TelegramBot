#!/usr/bin/env python3
"""
Simple Deep Listening Bot - MVP версия

Функциональность:
- Утреннее напоминание в 8:00
- 1 минута прослушивания
- Вопрос "Что ты услышал?"
- Сохранение ответа (текст или аудио)
"""

import os
import logging
import asyncio
from datetime import datetime, time, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
import requests
import json

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleListeningBot:
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
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("listen", self.start_listening))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        
        # Callback кнопки
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Голосовые сообщения
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Регистрируем пользователя
        await self.register_user(user.id, user.username, user.first_name)
        
        welcome_text = """
🎧 Добро пожаловать в Deep Listening Bot!

Я помогу вам развить практику осознанного слушания.

🌅 Каждое утро в 8:00 я буду напоминать вам:
• Послушать мир вокруг 1 минуту
• Поделиться тем, что вы услышали

Готовы начать прямо сейчас?
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Начать практику", callback_data="start_practice")],
            [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")],
            [InlineKeyboardButton("ℹ️ Как это работает", callback_data="how_it_works")]
        ])
        
        await update.message.reply_text(welcome_text, reply_markup=keyboard)
    
    async def register_user(self, user_id: int, username: str, first_name: str):
        """Регистрируем нового пользователя"""
        user_data = {
            'telegram_user_id': user_id,
            'username': username,
            'first_name': first_name,
            'morning_reminder_enabled': True,
            'morning_time': '08:00:00',
            'timezone': 'UTC'
        }
        
        # Используем upsert для избежания дублирования
        api_url = f"{self.supabase_url}/rest/v1/listening_users"
        headers = {**self.headers, 'Prefer': 'resolution=merge-duplicates'}
        
        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(user_data))
            if response.status_code in [200, 201]:
                logger.info(f"Пользователь {user_id} зарегистрирован")
            else:
                logger.error(f"Ошибка регистрации пользователя: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя: {e}")
    
    async def start_listening(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начинаем сессию прослушивания"""
        user_id = update.effective_user.id
        
        # Создаем новую сессию
        session_id = await self.create_listening_session(user_id)
        if session_id:
            context.user_data['current_session'] = session_id
            
            text = """
🎧 Начинаем практику глубокого слушания!

📍 Найдите удобное место
👂 Закройте глаза или сосредоточьтесь
⏰ Слушайте звуки вокруг вас ровно 1 минуту

Я напомню, когда время выйдет.
Нажмите "Готов", когда будете готовы начать.
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Готов начать", callback_data="ready_to_listen")]
            ])
            
            await update.message.reply_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")
    
    async def create_listening_session(self, user_id: int) -> Optional[str]:
        """Создаем новую сессию прослушивания"""
        session_data = {
            'user_id': user_id,
            'session_date': datetime.now().date().isoformat(),
            'session_time': datetime.now().time().isoformat(),
            'status': 'started'
        }
        
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions"
        headers = {**self.headers, 'Prefer': 'return=representation'}
        
        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(session_data))
            if response.status_code in [200, 201]:
                result = response.json()
                if result and len(result) > 0:
                    return result[0]['id']
            else:
                logger.error(f"Ошибка создания сессии: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Ошибка при создании сессии: {e}")
        
        return None
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_practice":
            await self.start_listening_from_callback(query, context)
        elif query.data == "ready_to_listen":
            await self.start_timer(query, context)
        elif query.data == "show_stats":
            await self.show_stats_from_callback(query, context)
        elif query.data == "how_it_works":
            await self.show_how_it_works(query, context)
    
    async def start_listening_from_callback(self, query, context):
        """Начинаем прослушивание из callback"""
        user_id = query.from_user.id
        
        # Создаем новую сессию
        session_id = await self.create_listening_session(user_id)
        if session_id:
            context.user_data['current_session'] = session_id
            
            text = """
🎧 Начинаем практику глубокого слушания!

📍 Найдите удобное место
👂 Закройте глаза или сосредоточьтесь  
⏰ Слушайте звуки вокруг вас ровно 1 минуту

Нажмите "Готов", когда будете готовы начать.
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Готов начать", callback_data="ready_to_listen")]
            ])
            
            await query.edit_message_text(text, reply_markup=keyboard)
    
    async def start_timer(self, query, context):
        """Запускаем таймер на 1 минуту"""
        text = """
🎧 Практика началась!

👂 Слушайте звуки вокруг вас...
⏰ Осталось: 1 минута

Сосредоточьтесь на том, что слышите прямо сейчас.
        """
        
        await query.edit_message_text(text)
        
        # Запускаем таймер на 60 секунд
        context.job_queue.run_once(
            self.timer_finished, 
            60, 
            chat_id=query.message.chat_id,
            user_id=query.from_user.id,
            data={'session_id': context.user_data.get('current_session')}
        )
    
    async def timer_finished(self, context: ContextTypes.DEFAULT_TYPE):
        """Таймер закончился - задаем вопрос"""
        chat_id = context.job.chat_id
        user_id = context.job.user_id
        
        text = """
⏰ Время вышло!

🤔 Что вы услышали?

Поделитесь своими впечатлениями:
• Напишите текстом
• Или запишите голосовое сообщение
        """
        
        # Сохраняем в контексте, что ждем ответ на вопрос
        if 'user_sessions' not in context.bot_data:
            context.bot_data['user_sessions'] = {}
        
        context.bot_data['user_sessions'][user_id] = {
            'session_id': context.job.data['session_id'],
            'waiting_for_answer': True
        }
        
        await context.bot.send_message(chat_id=chat_id, text=text)
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик голосовых сообщений"""
        user_id = update.effective_user.id
        
        # Проверяем, ждем ли мы ответ от этого пользователя
        if (context.bot_data.get('user_sessions', {}).get(user_id, {}).get('waiting_for_answer')):
            session_id = context.bot_data['user_sessions'][user_id]['session_id']
            voice_file_id = update.message.voice.file_id
            
            # Сохраняем голосовой ответ
            await self.save_voice_answer(session_id, voice_file_id)
            
            # Завершаем сессию
            await self.complete_session(session_id)
            
            # Убираем из ожидания
            context.bot_data['user_sessions'][user_id]['waiting_for_answer'] = False
            
            await update.message.reply_text(
                "🎙️ Спасибо за ваш ответ! Практика завершена.\n\n"
                "Увидимся завтра утром в 8:00! 🌅"
            )
        else:
            await update.message.reply_text(
                "Сначала начните практику командой /listen или нажмите 🎧 Начать практику"
            )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        user_id = update.effective_user.id
        
        # Проверяем, ждем ли мы ответ от этого пользователя
        if (context.bot_data.get('user_sessions', {}).get(user_id, {}).get('waiting_for_answer')):
            session_id = context.bot_data['user_sessions'][user_id]['session_id']
            text_answer = update.message.text
            
            # Сохраняем текстовый ответ
            await self.save_text_answer(session_id, text_answer)
            
            # Завершаем сессию
            await self.complete_session(session_id)
            
            # Убираем из ожидания
            context.bot_data['user_sessions'][user_id]['waiting_for_answer'] = False
            
            await update.message.reply_text(
                "📝 Спасибо за ваш ответ! Практика завершена.\n\n"
                "Увидимся завтра утром в 8:00! 🌅"
            )
        else:
            await update.message.reply_text(
                "Привет! Начните практику командой /listen или нажмите 🎧 Начать практику"
            )
    
    async def save_voice_answer(self, session_id: str, file_id: str):
        """Сохраняем голосовой ответ"""
        update_data = {
            'what_heard_audio_file_id': file_id,
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }
        
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions?id=eq.{session_id}"
        
        try:
            response = requests.patch(api_url, headers=self.headers, data=json.dumps(update_data))
            if response.status_code == 204:
                logger.info(f"Голосовой ответ сохранен для сессии {session_id}")
            else:
                logger.error(f"Ошибка сохранения голосового ответа: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении голосового ответа: {e}")
    
    async def save_text_answer(self, session_id: str, text: str):
        """Сохраняем текстовый ответ"""
        update_data = {
            'what_heard_text': text,
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }
        
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions?id=eq.{session_id}"
        
        try:
            response = requests.patch(api_url, headers=self.headers, data=json.dumps(update_data))
            if response.status_code == 204:
                logger.info(f"Текстовый ответ сохранен для сессии {session_id}")
            else:
                logger.error(f"Ошибка сохранения текстового ответа: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении текстового ответа: {e}")
    
    async def complete_session(self, session_id: str):
        """Завершаем сессию"""
        # Дополнительная логика завершения сессии, если нужна
        pass
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показываем статистику пользователя"""
        user_id = update.effective_user.id
        stats = await self.get_user_stats(user_id)
        
        text = f"""
📊 Ваша статистика практик:

🎧 Всего практик: {stats['total_sessions']}
✅ Завершенных: {stats['completed_sessions']}
📅 Последняя практика: {stats['last_session_date'] or 'Еще не было'}

🔥 Продолжайте практиковать каждый день!
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Начать практику", callback_data="start_practice")]
        ])
        
        await update.message.reply_text(text, reply_markup=keyboard)
    
    async def show_stats_from_callback(self, query, context):
        """Показываем статистику из callback"""
        user_id = query.from_user.id
        stats = await self.get_user_stats(user_id)
        
        text = f"""
📊 Ваша статистика практик:

🎧 Всего практик: {stats['total_sessions']}
✅ Завершенных: {stats['completed_sessions']}
📅 Последняя практика: {stats['last_session_date'] or 'Еще не было'}

🔥 Продолжайте практиковать каждый день!
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Начать практику", callback_data="start_practice")]
        ])
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def show_how_it_works(self, query, context):
        """Показываем как работает бот"""
        text = """
ℹ️ Как работает Deep Listening Bot:

🌅 **Утреннее напоминание**
Каждый день в 8:00 утра я пришлю вам напоминание

🎧 **1 минута слушания**  
Найдите удобное место и слушайте звуки вокруг

🤔 **Поделитесь опытом**
Расскажите, что услышали - текстом или голосом

📊 **Отслеживайте прогресс**
Смотрите статистику ваших практик

Это простая, но мощная практика осознанности! 🧘‍♀️
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Попробовать сейчас", callback_data="start_practice")]
        ])
        
        await query.edit_message_text(text, reply_markup=keyboard)
    
    async def get_user_stats(self, user_id: int) -> dict:
        """Получаем статистику пользователя"""
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions?user_id=eq.{user_id}&select=*"
        
        try:
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                sessions = response.json()
                
                total_sessions = len(sessions)
                completed_sessions = len([s for s in sessions if s['status'] == 'completed'])
                
                last_session_date = None
                if sessions:
                    # Сортируем по дате и берем последнюю
                    sessions.sort(key=lambda x: x['created_at'], reverse=True)
                    last_session_date = sessions[0]['session_date']
                
                return {
                    'total_sessions': total_sessions,
                    'completed_sessions': completed_sessions,
                    'last_session_date': last_session_date
                }
            else:
                logger.error(f"Ошибка получения статистики: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при получении статистики: {e}")
        
        return {
            'total_sessions': 0,
            'completed_sessions': 0,
            'last_session_date': None
        }
    
    async def send_morning_reminders(self):
        """Отправляем утренние напоминания (будет вызываться по расписанию)"""
        # Получаем всех пользователей с включенными напоминаниями
        api_url = f"{self.supabase_url}/rest/v1/listening_users?morning_reminder_enabled=eq.true&select=telegram_user_id,first_name"
        
        try:
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                users = response.json()
                
                for user in users:
                    user_id = user['telegram_user_id']
                    first_name = user['first_name'] or 'друг'
                    
                    text = f"""
🌅 Доброе утро, {first_name}!

Время для утренней практики глубокого слушания.

🎧 Всего 1 минута - послушайте мир вокруг вас
🤔 Поделитесь тем, что услышали

Готовы начать день осознанно?
                    """
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎧 Начать практику", callback_data="start_practice")],
                        [InlineKeyboardButton("⏰ Напомнить позже", callback_data="remind_later")]
                    ])
                    
                    try:
                        await self.application.bot.send_message(
                            chat_id=user_id,
                            text=text,
                            reply_markup=keyboard
                        )
                        logger.info(f"Утреннее напоминание отправлено пользователю {user_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания пользователю {user_id}: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке утренних напоминаний: {e}")
    
    def run(self):
        """Запускаем бота"""
        logger.info("Запускаем Simple Deep Listening Bot...")
        
        # Планируем утренние напоминания на 8:00 каждый день
        # (В продакшене это должно быть настроено через cron или планировщик задач)
        
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Главная функция"""
    try:
        bot = SimpleListeningBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == '__main__':
    main()
