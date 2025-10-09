# Инструкции по деплою на Railway

## Шаг 1: Подготовка
✅ Код загружен в GitHub: https://github.com/ikovrigina/DeepListening-TelegramBot
✅ Procfile настроен: `web: python simple_listening_bot.py`
✅ requirements.txt обновлен с `python-telegram-bot[job-queue]==20.7`
✅ runtime.txt указывает Python 3.9.18

## Шаг 2: Деплой через Railway веб-интерфейс

1. Перейдите на https://railway.app
2. Войдите в аккаунт или зарегистрируйтесь
3. Нажмите "New Project"
4. Выберите "Deploy from GitHub repo"
5. Выберите репозиторий `ikovrigina/DeepListening-TelegramBot`
6. Railway автоматически обнаружит Python проект

## Шаг 3: Настройка переменных окружения

В настройках проекта Railway добавьте переменные:

```
TELEGRAM_BOT_TOKEN=8272024094:AAHz8c8UlJQyX5jD9ERUECzgI1dZhBNPoD0
SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E
```

## Шаг 4: Деплой
Railway автоматически задеплоит проект после настройки переменных окружения.

## Шаг 5: Проверка
После успешного деплоя проверьте работу бота в Telegram.

## Альтернативный способ - через Railway CLI

Если удастся установить Railway CLI:
```bash
# Логин
railway login

# Инициализация проекта
cd /Users/ikovrigina/Documents/GitHub/Cursor/DeepListening-TelegramBot
railway init

# Добавление переменных окружения
railway variables set TELEGRAM_BOT_TOKEN=8272024094:AAHz8c8UlJQyX5jD9ERUECzgI1dZhBNPoD0
railway variables set SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
railway variables set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E

# Деплой
railway up
```

