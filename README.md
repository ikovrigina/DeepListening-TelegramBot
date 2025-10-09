# 🤖 DeepListening Telegram Bot

**DeepListening** - профессиональный Telegram-бот для автоматического сохранения сообщений в базу данных Supabase.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![Supabase](https://img.shields.io/badge/Database-Supabase-green.svg)
![Railway](https://img.shields.io/badge/Deploy-Railway-purple.svg)

## 🎯 Возможности

- ✅ **Автоматическое сохранение** всех текстовых сообщений
- ✅ **Информация о пользователях** (ID, имя, username)
- ✅ **Мгновенное подтверждение** - отвечает "Сохранил"
- ✅ **Подробные логи** всех операций
- ✅ **Обработка ошибок** с уведомлениями
- ✅ **24/7 работа** в облаке через Railway

## 🚀 Быстрый старт

### 1. Локальный запуск

```bash
# Клонируйте репозиторий
git clone <your-repo-url>
cd DeepListening-TelegramBot

# Установите зависимости
pip install -r bot/requirements.txt

# Настройте переменные окружения
cp bot/.env.example .env
# Отредактируйте .env файл

# Запустите бота
python bot/telegram_bot.py
```

### 2. Деплой на Railway

```bash
# Подключите репозиторий к Railway
# Настройте переменные окружения в Railway Dashboard
# Автоматический деплой!
```

Подробная инструкция: [`deployment/railway_setup.md`](deployment/railway_setup.md)

## 📁 Структура проекта

```
DeepListening-TelegramBot/
├── 📁 bot/                    # Основной код бота
│   ├── telegram_bot.py        # Главный файл бота
│   ├── requirements.txt       # Python зависимости
│   └── .env.example          # Шаблон переменных окружения
├── 📁 deployment/            # Файлы для деплоя
│   ├── Procfile              # Команда запуска для Railway
│   ├── runtime.txt           # Версия Python
│   └── railway_setup.md      # Инструкция по деплою
├── 📁 docs/                  # Документация
│   ├── README.md             # Документация бота
│   ├── RAILWAY_DEPLOYMENT.md # Подробный гайд по Railway
│   └── DATABASE_SETUP.md     # Настройка Supabase
├── 📁 scripts/               # Вспомогательные скрипты
│   └── setup_webhook.py      # Настройка webhook
└── README.md                 # Этот файл
```

## 🔧 Настройка

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Токен от @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Данные Supabase проекта
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### База данных

Бот автоматически работает с таблицей `telegram_messages` в Supabase:

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный идентификатор |
| `user_id` | BIGINT | ID пользователя Telegram |
| `username` | TEXT | Username пользователя |
| `first_name` | TEXT | Имя пользователя |
| `last_name` | TEXT | Фамилия пользователя |
| `message_text` | TEXT | Текст сообщения |
| `message_id` | BIGINT | ID сообщения в Telegram |
| `chat_id` | BIGINT | ID чата |
| `created_at` | TIMESTAMP | Время создания |

## 🌐 Деплой

### Railway (Рекомендуется)

1. **Подключите репозиторий** к [Railway](https://railway.app/)
2. **Настройте переменные окружения**
3. **Деплой происходит автоматически**

Подробно: [`deployment/railway_setup.md`](deployment/railway_setup.md)

### Альтернативы

- **Render** - бесплатный хостинг
- **Heroku** - классическая платформа
- **VPS** - собственный сервер

## 📖 Документация

- [`docs/README.md`](docs/README.md) - Подробная документация бота
- [`docs/RAILWAY_DEPLOYMENT.md`](docs/RAILWAY_DEPLOYMENT.md) - Гайд по деплою
- [`docs/DATABASE_SETUP.md`](docs/DATABASE_SETUP.md) - Настройка базы данных

## 🔐 Безопасность

⚠️ **Важно**: 
- Никогда не коммитьте файл `.env` с токенами!
- Используйте переменные окружения в продакшене
- Регулярно обновляйте зависимости

## 🤝 Поддержка

Если у вас есть вопросы или проблемы:

1. Проверьте [документацию](docs/)
2. Посмотрите логи в Railway Dashboard
3. Создайте Issue в репозитории

## 📄 Лицензия

MIT License - используйте свободно!

---

**Создано с ❤️ для автоматизации Telegram-коммуникации**

