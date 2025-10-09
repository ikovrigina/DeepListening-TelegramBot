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
        await query.answer()
        
        if query.data == "start_practice":
            await self.start_listening_from_callback(query, context)
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
        """Сохраняем голосовой ответ с транскрипцией"""
        update_data = {
            'what_heard_audio_file_id': file_id,
            'reflection_audio_file_id': file_id,
            'reflection_transcription': transcription,
            'what_heard': transcription,  # Дублируем в старое поле для совместимости
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        }
        
        api_url = f"{self.supabase_url}/rest/v1/listening_sessions?id=eq.{session_id}"
        
        try:
            response = requests.patch(api_url, headers=self.headers, data=json.dumps(update_data))
            if response.status_code == 204:
                logger.info(f"Голосовой ответ с транскрипцией сохранен для сессии {session_id}")
                
                # Также сохраняем в таблицу audio_files
                await self.save_audio_metadata(session_id, file_id, 'reflection')
            else:
                logger.error(f"Ошибка сохранения голосового ответа с транскрипцией: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении голосового ответа с транскрипцией: {e}")
    
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
        """Транскрибируем аудио в текст (заглушка для будущей реализации)"""
        # TODO: Интеграция с сервисом транскрипции (OpenAI Whisper, Google Speech-to-Text, и т.д.)
        # Пока возвращаем заглушку
        return "[Голосовое сообщение - транскрипция будет добавлена позже]"

    def run(self):
        """Запускаем бота"""
        logger.info("Запускаем Simple Deep Listening Bot...")
        
        # Запускаем JobQueue
        if self.application.job_queue:
            self.application.job_queue.start()
        
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