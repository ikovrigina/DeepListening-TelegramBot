#!/usr/bin/env python3
"""
Simple Deep Listening Bot - MVP версия

Функциональность:
- Постоянная практика слушания (в любое время)
- Пользователь контролирует время записи
- Вопрос "Что ты услышал?"
- Непрерывный цикл: после ответа можно начать новую практику
- Сохранение ответа (текст или аудио)
"""

import os
import logging
import asyncio
import io
from datetime import datetime, time, timedelta
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv
from openai import OpenAI
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
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not all([self.bot_token, self.supabase_url, self.supabase_key]):
            raise ValueError("Не все переменные окружения установлены!")

        # OpenAI клиент (не обязателен для запуска, но логируем отсутствие)
        self.openai_client: OpenAI | None = None
        if self.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.openai_api_key
            try:
                self.openai_client = OpenAI()
            except Exception as e:
                logger.error(f"Не удалось инициализировать OpenAI: {e}")
        
        # Настраиваем заголовки для Supabase API
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Создаем приложение бота с JobQueue
        self.application = Application.builder().token(self.bot_token).build()
        
        # Инициализируем JobQueue для таймеров
        from telegram.ext import JobQueue
        if not self.application.job_queue:
            self.application.job_queue = JobQueue()
            self.application.job_queue.set_application(self.application)
        
        # Добавляем обработчики
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настраиваем обработчики сообщений"""
        # Команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("listen", self.start_listening))
        self.application.add_handler(CommandHandler("stats", self.show_stats))
        self.application.add_handler(CommandHandler("library", self.show_library))
        
        # Callback кнопки
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Голосовые сообщения
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        
        # Фотографии
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        
        # Текстовые сообщения
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Регистрируем пользователя
        await self.register_user(user.id, user.username, user.first_name)
        
        welcome_text = """
🎧 Добро пожаловать в Deep Listening Bot!

Приглашаю тебя начать твою практику слушания прямо сейчас.

Я помогу тебе развить практику осознанного слушания.

Готов начать прямо сейчас?
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Что ты слышишь теперь?", callback_data="start_practice")],
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
📱 Нажми и зафиксируй кнопку записи голосового сообщения
👂 Расслабься, сделай 3 глубоких вдоха и прикрой глаза
⏰ Слушай все звуки вокруг столько, сколько захочется
            """
            
            msg = await update.message.reply_text(text)
            
            # Создаем фейковый query для start_timer
            class FakeQuery:
                def __init__(self, message, user):
                    self.message = message
                    self.from_user = user
            
            fake_query = FakeQuery(msg, update.effective_user)
            await self.start_timer(fake_query, context)
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
        try:
            await query.answer()
        except Exception:
            pass
        
        if query.data == "start_practice":
            await self.start_listening_from_callback(query, context)
        elif query.data == "show_stats":
            await self.show_stats_from_callback(query, context)
        elif query.data == "how_it_works":
            await self.show_how_it_works(query, context)
        elif query.data.startswith("lib:play:"):
            await self.library_play_audio(query, context)
        elif query.data.startswith("lib:page:"):
            await self.show_library_from_callback(query, context)
    
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
📱 Нажми и зафиксируй кнопку записи голосового сообщения
👂 Расслабься, сделай 3 глубоких вдоха и прикрой глаза
⏰ Слушай все звуки вокруг столько, сколько захочется
            """
            
            await query.edit_message_text(text)
            
            # Сразу запускаем таймер
            await self.start_timer(query, context)
    
    async def start_timer(self, query, context):
        """Начинаем практику с пользовательским контролем времени"""
        timer_msg = await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="🎧 Практика идет...\n\n"
                 "👂 Слушай звуки вокруг ...\n"
                 "⏰ Время: 00:00"
        )
        
        # Отмечаем, что пользователь должен записывать
        if 'user_sessions' not in context.bot_data:
            context.bot_data['user_sessions'] = {}
        
        user_id = query.from_user.id
        if user_id not in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id] = {}
        
        context.bot_data['user_sessions'][user_id].update({
            'should_be_recording': True,
            'session_id': context.user_data.get('current_session'),
            'start_time': datetime.now(),
            'timer_message_id': timer_msg.message_id,
            'instruction_message_id': None
        })
        
        # Запускаем визуальный таймер (обновляется каждые 15 секунд)
        context.job_queue.run_repeating(
            self.update_visual_timer,
            interval=15,
            first=15,
            chat_id=query.message.chat_id,
            user_id=query.from_user.id,
            data={'session_id': context.user_data.get('current_session')},
            name=f"timer_{user_id}"
        )
    
    async def update_visual_timer(self, context: ContextTypes.DEFAULT_TYPE):
        """Обновляем визуальный таймер каждые 15 секунд"""
        chat_id = context.job.chat_id
        user_id = context.job.user_id
        
        user_session = context.bot_data.get('user_sessions', {}).get(user_id, {})
        
        # Если пользователь больше не записывает, останавливаем таймер
        if not user_session.get('should_be_recording'):
            context.job.schedule_removal()
            return
            
        start_time = user_session.get('start_time')
        if not start_time:
            return
            
        # Вычисляем прошедшее время
        elapsed = datetime.now() - start_time
        minutes = int(elapsed.total_seconds() // 60)
        seconds = int(elapsed.total_seconds() % 60)
        
        # Обновляем сообщение с таймером
        timer_message_id = user_session.get('timer_message_id')
        if timer_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=timer_message_id,
                    text=f"🎧 Практика идет...\n\n"
                         f"👂 Слушай звуки вокруг ...\n"
                         f"⏰ Время: {minutes:02d}:{seconds:02d}"
                )
            except Exception as e:
                # Если не удалось обновить сообщение, продолжаем
                pass

    async def recording_finished(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Пользователь закончил запись - переходим к вопросу"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Останавливаем таймер
        current_jobs = context.job_queue.get_jobs_by_name(f"timer_{user_id}")
        for job in current_jobs:
            job.schedule_removal()
        
        # Обновляем финальное время
        user_session = context.bot_data.get('user_sessions', {}).get(user_id, {})
        start_time = user_session.get('start_time')
        if start_time:
            elapsed = datetime.now() - start_time
            minutes = int(elapsed.total_seconds() // 60)
            seconds = int(elapsed.total_seconds() % 60)
            
            # Обновляем сообщение с финальным временем
            timer_message_id = user_session.get('timer_message_id')
            if timer_message_id:
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=timer_message_id,
                        text=f"✅ Практика завершена!\n\n"
                             f"👂 Ты слушал: {minutes:02d}:{seconds:02d}\n"
                             f"🎙️ Аудио получено!"
                    )
                except Exception:
                    pass
        
        # Убираем инструкцию
        instruction_message_id = user_session.get('instruction_message_id')
        if instruction_message_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=instruction_message_id)
            except Exception:
                pass
        
        # Переходим к вопросу
        await asyncio.sleep(1)  # Небольшая пауза для плавности
        
        text = """
🤔 Что ты услышал?

Опиши звуки, которые заметил во время практики:

📝 Напиши текстом
🎙️ Или запиши голосовое сообщение
Приложи фотографию, если хочешь
        """
        
        await context.bot.send_message(chat_id=chat_id, text=text)
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик голосовых сообщений"""
        user_id = update.effective_user.id
        file_id = update.message.voice.file_id
        duration = update.message.voice.duration
        
        user_session = context.bot_data.get('user_sessions', {}).get(user_id, {})
        
        # Проверяем, что именно мы ждем от пользователя
        if user_session.get('should_be_recording') and not user_session.get('waiting_for_answer'):
            # Это аудио окружения во время практики - пользователь закончил слушать
            session_id = user_session['session_id']
            message_id = update.message.message_id
            await self.save_environment_audio(session_id, file_id, duration, message_id)
            
            # Отмечаем, что получили аудио окружения и практика закончена
            context.bot_data['user_sessions'][user_id].update({
                'received_environment_audio': True,
                'should_be_recording': False,
                'waiting_for_answer': True
            })
            
            # Вызываем метод завершения записи
            await self.recording_finished(update, context)
            
        elif user_session.get('waiting_for_answer'):
            # Сохраняем голосовую рефлексию
            session_id = user_session['session_id']
            
            # Транскрибируем аудио
            transcription = await self.transcribe_audio(file_id)
            
            # Сохраняем голосовой ответ с транскрипцией
            await self.save_voice_answer_with_transcription(session_id, file_id, transcription)
            
            # Завершаем сессию
            await self.complete_session(session_id)
            
            # Убираем из ожидания
            context.bot_data['user_sessions'][user_id]['waiting_for_answer'] = False
            
            # Показываем кнопки для следующего действия (без "Мои записи")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 Что ты слышишь теперь?", callback_data="start_practice")],
                [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")],
                [InlineKeyboardButton("ℹ️ Как это работает", callback_data="how_it_works")]
            ])
            
            await update.message.reply_text(
                "🎙️ Спасибо за то, что ты поделился!",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                "Сначала начни практику командой /listen или нажми 🎧 Что ты слышишь теперь?"
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
            
            # Показываем кнопки для следующего действия (без "Мои записи")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 Что ты слышишь теперь?", callback_data="start_practice")],
                [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")],
                [InlineKeyboardButton("ℹ️ Как это работает", callback_data="how_it_works")]
            ])
            
            await update.message.reply_text(
                "📝 Спасибо за то, что ты поделился!",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                "Привет! Начни практику командой /listen или нажми 🎧 Что ты слышишь теперь?"
            )
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик фотографий"""
        user_id = update.effective_user.id
        
        # Проверяем, ждем ли мы ответ от этого пользователя
        if (context.bot_data.get('user_sessions', {}).get(user_id, {}).get('waiting_for_answer')):
            session_id = context.bot_data['user_sessions'][user_id]['session_id']
            
            # Получаем file_id самой большой версии фото
            photo = update.message.photo[-1]
            photo_file_id = photo.file_id
            
            # Получаем подпись к фото, если есть
            caption = update.message.caption or ""
            
            # Сохраняем фото и подпись
            await self.save_photo_answer(session_id, photo_file_id, caption)
            
            # Завершаем сессию
            await self.complete_session(session_id)
            
            # Убираем из ожидания
            context.bot_data['user_sessions'][user_id]['waiting_for_answer'] = False
            
            # Показываем кнопки для следующего действия (без "Мои записи")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎧 Что ты слышишь теперь?", callback_data="start_practice")],
                [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")],
                [InlineKeyboardButton("ℹ️ Как это работает", callback_data="how_it_works")]
            ])
            
            await update.message.reply_text(
                "📸 Спасибо за то, что ты поделился!",
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                "Привет! Начни практику командой /listen или нажми 🎧 Что ты слышишь теперь?"
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
    
    async def save_voice_answer_with_transcription(self, session_id: str, file_id: str, transcription: str):
        """Сохраняем голосовой ответ и текст в существующие поля сессии."""
        # Пишем только в гарантированно существующие поля
        update_data = {
            'what_heard_text': transcription,
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }
        
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions?id=eq.{session_id}"
        
        try:
            response = requests.patch(api_url, headers=self.headers, data=json.dumps(update_data))
            if response.status_code == 204:
                logger.info(f"Текст транскрипции сохранен для сессии {session_id}")

                # Также сохраняем метаданные аудио-ответа отдельно
                await self.save_audio_metadata(session_id, file_id, 'reflection')
            else:
                logger.error(f"Ошибка сохранения транскрипции: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении транскрипции: {e}")
    
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
    
    async def save_photo_answer(self, session_id: str, photo_file_id: str, caption: str):
        """Сохраняем фото с подписью"""
        update_data = {
            'photo_file_id': photo_file_id,
            'what_heard_text': caption if caption else "[Фото без подписи]",
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }
        
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions?id=eq.{session_id}"
        
        try:
            response = requests.patch(api_url, headers=self.headers, data=json.dumps(update_data))
            if response.status_code == 204:
                logger.info(f"Фото с подписью сохранено для сессии {session_id}")
            else:
                logger.error(f"Ошибка сохранения фото: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении фото: {e}")
    
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
            [InlineKeyboardButton("🎧 Что ты слышишь теперь?", callback_data="start_practice")],
            [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")],
            [InlineKeyboardButton("ℹ️ Как это работает", callback_data="how_it_works")]
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
            [InlineKeyboardButton("🎧 Что ты слышишь теперь?", callback_data="start_practice")],
            [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")],
            [InlineKeyboardButton("ℹ️ Как это работает", callback_data="how_it_works")]
        ])
        
        await query.edit_message_text(text, reply_markup=keyboard)

    # ===== Library (список записей) =====
    async def show_library(self, update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
        """Показываем список записей пользователя."""
        user_id = update.effective_user.id
        await self._render_library(chat_id=update.effective_chat.id, user_id=user_id, page=page, edit_message_id=None, context=context)

    async def show_library_from_callback(self, query, context):
        """Показываем библиотеку из callback с пагинацией."""
        user_id = query.from_user.id
        try:
            parts = query.data.split(":")  # lib:page:<n>
            page = int(parts[2]) if len(parts) > 2 else 1
            if page < 1:
                page = 1
        except Exception:
            page = 1
        try:
            await query.answer()
        except Exception:
            pass
        await self._render_library(chat_id=query.message.chat_id, user_id=user_id, page=page, edit_message_id=query.message.message_id, context=context)

    async def _render_library(self, chat_id: int, user_id: int, page: int, edit_message_id: Optional[int], context: ContextTypes.DEFAULT_TYPE):
        PAGE_SIZE = 10
        offset = (page - 1) * PAGE_SIZE

        # Загружаем сессии пользователя
        sessions_url = (
            f"{self.supabase_url}/rest/v1/listening_sessions"
            f"?user_id=eq.{user_id}&select=id,created_at,session_duration_seconds,what_heard_text"
            f"&order=created_at.desc&limit={PAGE_SIZE}&offset={offset}"
        )
        try:
            resp = requests.get(sessions_url, headers=self.headers)
            if resp.status_code != 200:
                text = "Не удалось получить список записей. Попробуйте позже."
                if edit_message_id:
                    await context.bot.edit_message_text(chat_id=chat_id, message_id=edit_message_id, text=text)
                else:
                    await context.bot.send_message(chat_id=chat_id, text=text)
                return
            sessions = resp.json() or []
        except Exception:
            sessions = []

        if not sessions:
            text = "Пока нет записей. Начните практику командой /listen"
            if edit_message_id:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=edit_message_id, text=text)
            else:
                await context.bot.send_message(chat_id=chat_id, text=text)
            return

        # Формируем список с кнопками проигрывания
        # Подготовим хранилище коротких токенов для callback data
        if 'lib_tokens' not in context.bot_data:
            context.bot_data['lib_tokens'] = {}
        lib_tokens = context.bot_data['lib_tokens']

        rows = []
        for s in sessions:
            created_at = s.get("created_at")
            dur = s.get("session_duration_seconds") or 0
            text_answer = s.get("what_heard_text") or ""
            keywords = self._extract_keywords(text_answer)

            # Ищем аудио ответа (reflection). Если нет, попробуем окружение (environment)
            file_id = await self._get_session_audio_file_id(s.get("id"), preferred_type="reflection")
            if not file_id:
                file_id = await self._get_session_audio_file_id(s.get("id"), preferred_type="environment")

            # Форматируем дату и длительность
            try:
                # created_at уже в ISO, берём только дату
                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")) if created_at else datetime.now()
                date_str = dt.strftime("%d.%m.%Y")
            except Exception:
                date_str = "—"
            mm = int(dur // 60)
            ss = int(dur % 60)
            dur_str = f"{mm:02d}:{ss:02d}"
            kw_str = (", ".join(keywords)) if keywords else "—"

            label = f"{date_str} · {dur_str} · {kw_str}"
            if len(label) > 64:
                label = label[:61] + "…"

            if file_id:
                # Генерируем короткий токен вместо длинного file_id (ограничение 64 байта)
                import uuid
                token = uuid.uuid4().hex[:32]
                lib_tokens[token] = {"file_id": file_id, "user_id": user_id}
                rows.append([InlineKeyboardButton(f"▶️ {label}", callback_data=f"lib:play:{token}")])
            else:
                rows.append([InlineKeyboardButton(f"📝 {label}", callback_data=f"lib:page:{page}")])

        # Пагинация
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("◀️", callback_data=f"lib:page:{page-1}"))
        if len(sessions) == PAGE_SIZE:
            nav.append(InlineKeyboardButton("▶️", callback_data=f"lib:page:{page+1}"))
        if nav:
            rows.append(nav)

        keyboard = InlineKeyboardMarkup(rows)
        header = "📚 Мои записи"
        if edit_message_id:
            try:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=edit_message_id, text=header, reply_markup=keyboard)
            except Exception:
                # В случае "Message is not modified" просто игнорируем
                pass
        else:
            await context.bot.send_message(chat_id=chat_id, text=header, reply_markup=keyboard)

    async def library_play_audio(self, query, context):
        """Проигрываем выбранный файл по file_id."""
        try:
            token = query.data.split(":")[2]
        except Exception:
            try:
                await query.answer()
            except Exception:
                pass
            return
        try:
            await query.answer()
        except Exception:
            pass

        # Разрешаем токен в file_id
        file_id = None
        meta = context.bot_data.get('lib_tokens', {}).get(token)
        if isinstance(meta, dict):
            file_id = meta.get('file_id')

        if not file_id:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Ссылка на аудио устарела. Обновите список /library")
            return

        try:
            await context.bot.send_voice(chat_id=query.message.chat_id, voice=file_id)
        except Exception:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Не удалось воспроизвести аудио")

    async def _get_session_audio_file_id(self, session_id: str, preferred_type: str) -> Optional[str]:
        """Возвращает telegram_file_id из audio_files для указанной сессии и типа файла."""
        url = (
            f"{self.supabase_url}/rest/v1/audio_files"
            f"?session_id=eq.{session_id}&file_type=eq.{preferred_type}&select=telegram_file_id&limit=1"
        )
        try:
            r = requests.get(url, headers=self.headers)
            if r.status_code == 200:
                arr = r.json() or []
                if arr:
                    return arr[0].get("telegram_file_id")
        except Exception:
            pass
        return None

    def _extract_keywords(self, text: str, max_words: int = 5) -> list[str]:
        """Очень простое извлечение ключевых слов из текста."""
        if not text:
            return []
        text_l = text.lower()
        # простой набор стоп-слов (ru/en)
        stop = {
            "и","в","на","что","это","как","я","мы","он","она","они","оно","а","но","или","к","у","из","за","для","по","с","со","же","ли","не","да","то","the","a","an","and","or","of","to","in","on","at","is","are","was","were","be","been","being"
        }
        # грубое токенизирование
        words = [w.strip(",.;:!?()[]{}\"'»«–—") for w in text_l.split()]
        words = [w for w in words if w and w not in stop and w.isalpha() and len(w) > 2]
        # сохраняем порядок появления, удаляя дубликаты
        seen = set()
        uniq = []
        for w in words:
            if w not in seen:
                seen.add(w)
                uniq.append(w)
            if len(uniq) >= max_words:
                break
        return uniq
    
    async def show_how_it_works(self, query, context):
        """Показываем как работает бот"""
        text = """
ℹ️ Как работает Deep Listening Bot:

🎧 **Практика слушания**  
Найди удобное место и слушай звуки вокруг

🤔 **Поделись опытом**
Расскажи, что услышал - текстом или голосом

🔄 **Непрерывный цикл**
После каждого ответа я приглашаю тебя начать новую практику

📊 **Отслеживай прогресс**
Смотри статистику твоих практик

Это простая, но мощная практика осознанности! 🧘‍♀️
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Что ты слышишь теперь?", callback_data="start_practice")],
            [InlineKeyboardButton("📊 Моя статистика", callback_data="show_stats")],
            [InlineKeyboardButton("ℹ️ Как это работает", callback_data="how_it_works")]
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
    
    async def prompt_environment_recording(self, query, context):
        """Предлагаем записать аудио окружения"""
        text = """
🎙️ Запись звуков окружения

Отправьте голосовое сообщение, чтобы записать звуки, которые вы слышите прямо сейчас.

Это поможет вам позже вспомнить атмосферу момента!
        """
        
        await query.answer()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text
        )
        
        # Отмечаем, что ждем аудио окружения
        if 'user_sessions' not in context.bot_data:
            context.bot_data['user_sessions'] = {}
        
        user_id = query.from_user.id
        if user_id not in context.bot_data['user_sessions']:
            context.bot_data['user_sessions'][user_id] = {}
        
        context.bot_data['user_sessions'][user_id]['waiting_for_environment_audio'] = True
        context.bot_data['user_sessions'][user_id]['session_id'] = context.user_data.get('current_session')
    
    async def save_environment_audio(self, session_id: str, file_id: str, duration: int = None, message_id: int = None):
        """Сохраняем аудио окружения"""
        update_data = {
            'environment_audio_file_id': file_id
        }
        
        if duration:
            update_data['session_duration_seconds'] = duration
        
        if message_id:
            update_data['environment_audio_message_id'] = message_id
        
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions?id=eq.{session_id}"
        
        try:
            response = requests.patch(api_url, headers=self.headers, data=json.dumps(update_data))
            if response.status_code == 204:
                logger.info(f"Аудио окружения сохранено для сессии {session_id}")
                
                # Также сохраняем в таблицу audio_files
                await self.save_audio_metadata(session_id, file_id, 'environment', duration)
            else:
                logger.error(f"Ошибка сохранения аудио окружения: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении аудио окружения: {e}")
    
    async def save_audio_metadata(self, session_id: str, file_id: str, file_type: str, duration: int = None):
        """Сохраняем метаданные аудиофайла"""
        audio_data = {
            'session_id': session_id,
            'file_type': file_type,
            'telegram_file_id': file_id,
            'duration_seconds': duration,
            'created_at': datetime.now().isoformat()
        }
        
        api_url = f"{self.supabase_url}/rest/v1/audio_files"
        
        try:
            response = requests.post(api_url, headers=self.headers, data=json.dumps(audio_data))
            if response.status_code in [200, 201]:
                logger.info(f"Метаданные аудио сохранены: {file_type} для сессии {session_id}")
            else:
                logger.error(f"Ошибка сохранения метаданных аудио: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении метаданных аудио: {e}")
    
    async def transcribe_audio(self, file_id: str) -> str:
        """Транскрибируем аудио через OpenAI Whisper. Возвращаем текст или заглушку."""
        if not self.openai_client:
            logger.warning("OPENAI_API_KEY не задан — возвращаю заглушку транскрипции")
            return "[Голосовое сообщение — транскрипция недоступна]"

        try:
            # 1) Получаем путь к файлу в Telegram
            get_file_url = f"https://api.telegram.org/bot{self.bot_token}/getFile"
            r = requests.get(get_file_url, params={"file_id": file_id}, timeout=30)
            r.raise_for_status()
            file_path = r.json()["result"]["file_path"]

            # 2) Скачиваем файл
            file_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            audio_resp = requests.get(file_url, timeout=60)
            audio_resp.raise_for_status()

            audio_bytes = io.BytesIO(audio_resp.content)
            audio_bytes.name = os.path.basename(file_path) or "voice.ogg"

            # 3) Отправляем в OpenAI Whisper
            res = self.openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_bytes,
                response_format="text"
            )

            text = res if isinstance(res, str) else getattr(res, "text", "").strip()
            if not text:
                text = "[распознавание завершилось без текста]"

            return text
        except Exception as e:
            logger.error(f"Ошибка транскрипции через OpenAI: {e}")
            return "[Не удалось распознать аудио]"

    def run(self):
        """Запускаем бота"""
        logger.info("Запускаем Simple Deep Listening Bot...")
        
        # JobQueue запускается автоматически с application.run_polling()
        
        # Для Railway используем polling с drop_pending_updates
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

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