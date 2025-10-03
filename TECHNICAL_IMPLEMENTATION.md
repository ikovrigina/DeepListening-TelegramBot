# 🛠️ Техническая реализация Deep Listening Bot

## 📊 Структура базы данных

### Расширение существующей схемы Supabase:

```sql
-- Таблица пользователей и их настроек
CREATE TABLE user_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL, -- Telegram user_id
    username TEXT,
    first_name TEXT,
    timezone TEXT DEFAULT 'UTC',
    language TEXT DEFAULT 'ru',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Настройки напоминаний
CREATE TABLE reminder_settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT REFERENCES user_profiles(user_id),
    morning_enabled BOOLEAN DEFAULT false,
    morning_time TIME DEFAULT '09:00',
    day_enabled BOOLEAN DEFAULT false,
    day_time TIME DEFAULT '14:00',
    evening_enabled BOOLEAN DEFAULT false,
    evening_time TIME DEFAULT '20:00',
    custom_reminders JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Сессии практик глубокого слушания
CREATE TABLE listening_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT REFERENCES user_profiles(user_id),
    session_date DATE DEFAULT CURRENT_DATE,
    session_time TIME DEFAULT CURRENT_TIME,
    duration_minutes INTEGER, -- планируемая длительность
    actual_duration INTEGER, -- фактическая длительность
    location TEXT,
    location_type TEXT, -- 'home', 'nature', 'city', 'other'
    mood_before INTEGER CHECK (mood_before >= 1 AND mood_before <= 10),
    mood_after INTEGER CHECK (mood_after >= 1 AND mood_after <= 10),
    tags TEXT[], -- массив тегов
    reflection_text TEXT,
    insights TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Аудиозаписи
CREATE TABLE audio_recordings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES listening_sessions(id),
    user_id BIGINT REFERENCES user_profiles(user_id),
    telegram_file_id TEXT NOT NULL, -- ID файла в Telegram
    file_size INTEGER,
    duration_seconds INTEGER,
    file_format TEXT DEFAULT 'ogg', -- формат аудио
    transcription TEXT, -- автоматическая расшифровка (опционально)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Достижения и статистика
CREATE TABLE user_achievements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT REFERENCES user_profiles(user_id),
    achievement_type TEXT NOT NULL, -- 'streak_7', 'total_50', 'location_nature'
    achievement_name TEXT NOT NULL,
    description TEXT,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для производительности
CREATE INDEX idx_listening_sessions_user_date ON listening_sessions(user_id, session_date DESC);
CREATE INDEX idx_listening_sessions_tags ON listening_sessions USING gin(tags);
CREATE INDEX idx_audio_recordings_session ON audio_recordings(session_id);
CREATE INDEX idx_user_achievements_user ON user_achievements(user_id, earned_at DESC);
```

## 🤖 Архитектура бота

### Основные модули:

```python
# bot/
├── main.py                 # Точка входа
├── handlers/
│   ├── __init__.py
│   ├── start.py           # /start, регистрация
│   ├── practice.py        # Практики слушания
│   ├── reminders.py       # Настройка напоминаний
│   ├── history.py         # Просмотр записей
│   ├── audio.py           # Обработка аудио
│   └── stats.py           # Статистика
├── services/
│   ├── __init__.py
│   ├── database.py        # Работа с Supabase
│   ├── scheduler.py       # Планировщик напоминаний
│   ├── audio_processor.py # Обработка аудио
│   └── analytics.py       # Аналитика и инсайты
├── models/
│   ├── __init__.py
│   ├── user.py           # Модель пользователя
│   ├── session.py        # Модель сессии
│   └── recording.py      # Модель записи
└── utils/
    ├── __init__.py
    ├── keyboards.py      # Клавиатуры
    ├── messages.py       # Шаблоны сообщений
    └── helpers.py        # Вспомогательные функции
```

## 🔄 Основные сценарии использования

### 1. Регистрация нового пользователя:

```python
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Создаем профиль пользователя
    await create_user_profile(user.id, user.username, user.first_name)
    
    # Приветственное сообщение
    welcome_text = """
    🎧 Добро пожаловать в Deep Listening Bot!
    
    Я помогу вам развить практику глубокого слушания.
    Давайте настроим ваши напоминания?
    """
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⏰ Настроить напоминания", callback_data="setup_reminders")],
        [InlineKeyboardButton("🎧 Начать практику сейчас", callback_data="start_practice")],
        [InlineKeyboardButton("ℹ️ Узнать больше", callback_data="learn_more")]
    ])
    
    await update.message.reply_text(welcome_text, reply_markup=keyboard)
```

### 2. Начало практики:

```python
async def start_practice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Создаем новую сессию
    session_id = await create_listening_session(user_id)
    context.user_data['current_session'] = session_id
    
    # Выбор длительности
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("5 минут", callback_data="duration_5")],
        [InlineKeyboardButton("10 минут", callback_data="duration_10")],
        [InlineKeyboardButton("15 минут", callback_data="duration_15")],
        [InlineKeyboardButton("Свое время", callback_data="duration_custom")]
    ])
    
    text = """
    🎧 Отлично! Начинаем практику глубокого слушания.
    
    Выберите длительность практики:
    """
    
    await update.callback_query.edit_message_text(text, reply_markup=keyboard)
```

### 3. Обработка аудиозаписи:

```python
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session_id = context.user_data.get('current_session')
    
    if not session_id:
        await update.message.reply_text("Сначала начните практику командой /practice")
        return
    
    # Сохраняем аудио
    audio_file = update.message.voice or update.message.audio
    file_id = audio_file.file_id
    duration = audio_file.duration
    
    await save_audio_recording(session_id, user_id, file_id, duration)
    
    # Запрашиваем рефлексию
    text = """
    🎙️ Спасибо за запись!
    
    Теперь поделитесь своими впечатлениями:
    • Какие звуки вы услышали?
    • Что вы почувствовали?
    • Какие мысли или инсайты пришли к вам?
    """
    
    await update.message.reply_text(text)
    context.user_data['awaiting_reflection'] = True
```

## ⏰ Система напоминаний

### Планировщик задач:

```python
import asyncio
from datetime import datetime, time
import pytz

class ReminderScheduler:
    def __init__(self, bot):
        self.bot = bot
        self.running = False
    
    async def start(self):
        self.running = True
        while self.running:
            await self.check_reminders()
            await asyncio.sleep(60)  # проверяем каждую минуту
    
    async def check_reminders(self):
        now = datetime.now(pytz.UTC)
        current_time = now.time()
        
        # Получаем пользователей с активными напоминаниями
        users = await get_users_with_reminders(current_time)
        
        for user in users:
            await self.send_reminder(user['user_id'], user['reminder_type'])
    
    async def send_reminder(self, user_id: int, reminder_type: str):
        messages = {
            'morning': "🌅 Доброе утро! Время для утренней практики слушания.",
            'day': "☀️ Сделайте паузу и послушайте мир вокруг вас.",
            'evening': "🌙 Завершите день практикой осознанного слушания."
        }
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎧 Начать практику", callback_data="start_practice")],
            [InlineKeyboardButton("⏰ Позже", callback_data="remind_later")]
        ])
        
        await self.bot.send_message(
            chat_id=user_id,
            text=messages[reminder_type],
            reply_markup=keyboard
        )
```

## 📊 Аналитика и статистика

### Генерация инсайтов:

```python
async def generate_user_insights(user_id: int) -> dict:
    # Получаем данные пользователя
    sessions = await get_user_sessions(user_id, limit=30)  # последние 30 сессий
    
    insights = {
        'total_sessions': len(sessions),
        'average_duration': calculate_average_duration(sessions),
        'favorite_locations': get_most_common_locations(sessions),
        'mood_improvement': calculate_mood_change(sessions),
        'streak_days': calculate_current_streak(user_id),
        'most_active_time': get_most_active_time(sessions),
        'common_tags': get_most_common_tags(sessions)
    }
    
    return insights

async def format_stats_message(user_id: int) -> str:
    insights = await generate_user_insights(user_id)
    
    text = f"""
    📊 Ваша статистика практик:
    
    🎧 Всего практик: {insights['total_sessions']}
    ⏱️ Средняя длительность: {insights['average_duration']} мин
    🔥 Текущая серия: {insights['streak_days']} дней
    
    📍 Любимые места:
    {format_locations(insights['favorite_locations'])}
    
    📈 Улучшение настроения: +{insights['mood_improvement']:.1f}
    
    🕐 Самое активное время: {insights['most_active_time']}
    
    🏷️ Частые теги: {', '.join(insights['common_tags'][:5])}
    """
    
    return text
```

## 🎵 Обработка аудио

### Дополнительные возможности:

```python
import speech_recognition as sr
from pydub import AudioSegment

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    async def process_audio(self, file_path: str) -> dict:
        """Обрабатывает аудиофайл и извлекает метаданные"""
        
        # Получаем длительность и размер
        audio = AudioSegment.from_file(file_path)
        duration = len(audio) / 1000  # в секундах
        
        # Опционально: распознавание речи
        transcription = None
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = self.recognizer.record(source)
                transcription = self.recognizer.recognize_google(
                    audio_data, language='ru-RU'
                )
        except:
            pass  # Если не удалось распознать
        
        return {
            'duration': duration,
            'transcription': transcription,
            'file_size': len(audio.raw_data)
        }
```

## 🚀 Деплой и масштабирование

### Docker контейнер:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot/main.py"]
```

### requirements.txt:

```txt
python-telegram-bot==20.7
supabase==2.3.4
python-dotenv==1.0.0
requests==2.31.0
asyncio==3.4.3
pytz==2023.3
APScheduler==3.10.4
SpeechRecognition==3.10.0
pydub==0.25.1
```

### Переменные окружения:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# Дополнительные настройки
REMINDER_CHECK_INTERVAL=60  # секунды
MAX_AUDIO_SIZE_MB=20
ENABLE_SPEECH_RECOGNITION=true
DEFAULT_TIMEZONE=UTC
```

## 🔧 Команды для разработки

### Локальный запуск:
```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env

# Запуск бота
python bot/main.py
```

### Тестирование:
```bash
# Запуск тестов
pytest tests/

# Проверка кода
flake8 bot/
black bot/
```

---

**Эта архитектура обеспечивает масштабируемость, надежность и простоту разработки Deep Listening Bot.** 🎧🚀
