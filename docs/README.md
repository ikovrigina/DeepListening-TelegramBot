# DeepListening Telegram Bot

**DeepListening** - телеграм-бот для сохранения сообщений в Supabase.

Этот бот автоматически сохраняет все текстовые сообщения, отправленные ему, в базу данных Supabase и отвечает "Сохранил".

## Возможности

- ✅ Сохранение всех текстовых сообщений в Supabase
- ✅ Сохранение информации о пользователе (ID, имя, username)
- ✅ Автоматический ответ "Сохранил" на каждое сообщение
- ✅ Логирование всех операций
- ✅ Обработка ошибок

## Установка и настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Создание телеграм-бота

1. Найдите в Telegram бота [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 3. Настройка переменных окружения

Создайте файл `.env` на основе `env.example`:

```bash
cp env.example .env
```

Заполните файл `.env` вашими данными:

```env
# Токен от @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Данные Supabase проекта
SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E
```

### 4. Запуск бота

```bash
python telegram_bot.py
```

## Структура базы данных

Бот создает таблицу `telegram_messages` со следующими полями:

- `id` - уникальный идентификатор записи
- `user_id` - ID пользователя в Telegram
- `username` - username пользователя (если есть)
- `first_name` - имя пользователя
- `last_name` - фамилия пользователя (если есть)
- `message_text` - текст сообщения
- `message_id` - ID сообщения в Telegram
- `chat_id` - ID чата
- `created_at` - время создания записи

## Использование

1. Запустите бота командой `python telegram_bot.py`
2. Найдите вашего бота в Telegram по имени, которое вы дали при создании
3. Отправьте любое текстовое сообщение
4. Бот ответит "Сохранил" и сохранит сообщение в базу данных

## Логи

Бот ведет подробные логи всех операций. Уровень логирования можно изменить в коде.

## Остановка бота

Нажмите `Ctrl+C` для остановки бота.

## Требования

- Python 3.7+
- Активный проект Supabase
- Токен телеграм-бота

## Зависимости

- `python-telegram-bot` - для работы с Telegram Bot API
- `supabase` - для работы с базой данных Supabase
- `python-dotenv` - для загрузки переменных окружения

## Безопасность

⚠️ **Важно**: Никогда не коммитьте файл `.env` с реальными токенами в публичный репозиторий!

Добавьте `.env` в `.gitignore`:

```
.env
__pycache__/
*.pyc
```
