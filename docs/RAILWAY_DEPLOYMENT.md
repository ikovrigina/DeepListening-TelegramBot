# 🚀 Деплой DeepListening Bot на Railway

Пошаговое руководство по развертыванию Telegram-бота на платформе Railway.

## 📋 Что вам понадобится

- ✅ Аккаунт на [Railway.app](https://railway.app/)
- ✅ Аккаунт на [GitHub](https://github.com/) с репозиторием
- ✅ Токен Telegram-бота от [@BotFather](https://t.me/BotFather)
- ✅ Настроенный проект [Supabase](https://supabase.com/)

## 🎯 Шаг 1: Подготовка репозитория

### 1.1 Загрузите проект на GitHub

```bash
# В папке проекта
git init
git add .
git commit -m "Initial commit: DeepListening Telegram Bot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/DeepListening-TelegramBot.git
git push -u origin main
```

### 1.2 Убедитесь, что файлы на месте

Проверьте структуру в GitHub:
```
DeepListening-TelegramBot/
├── bot/telegram_bot.py
├── deployment/Procfile
├── deployment/runtime.txt
└── bot/requirements.txt
```

## 🚂 Шаг 2: Настройка Railway

### 2.1 Создание проекта

1. **Войдите** на [railway.app](https://railway.app/)
2. **Нажмите** "New Project"
3. **Выберите** "Deploy from GitHub repo"
4. **Подключите** GitHub аккаунт (если не подключен)
5. **Выберите** ваш репозиторий `DeepListening-TelegramBot`

### 2.2 Настройка деплоя

1. **Root Directory**: оставьте пустым (корень проекта)
2. **Build Command**: Railway автоматически определит
3. **Start Command**: `python bot/telegram_bot.py`

## 🔐 Шаг 3: Переменные окружения

В Railway Dashboard → Settings → Variables добавьте:

### 3.1 Telegram Bot Token
```
TELEGRAM_BOT_TOKEN=8272024094:AAHz8c8UlJQyX5jD9ERUECzgI1dZhBNPoD0
```
> ⚠️ **Замените** на ваш реальный токен!

### 3.2 Supabase настройки
```
SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E
```

### 3.3 Как получить Supabase данные

1. Откройте ваш проект в [Supabase Dashboard](https://app.supabase.com/)
2. **Settings** → **API**
3. Скопируйте:
   - **Project URL** → `SUPABASE_URL`
   - **Project API keys** → **anon** → `SUPABASE_ANON_KEY`

## ⚙️ Шаг 4: Настройка файлов деплоя

### 4.1 Procfile (уже создан)
```
web: python bot/telegram_bot.py
```

### 4.2 runtime.txt (уже создан)
```
python-3.9.18
```

### 4.3 requirements.txt (уже создан)
```
python-telegram-bot==20.7
supabase==2.3.4
python-dotenv==1.0.0
requests==2.31.0
```

## 🎉 Шаг 5: Деплой

1. **Нажмите Deploy** в Railway Dashboard
2. **Ожидайте** завершения сборки (2-3 минуты)
3. **Проверьте логи** на наличие ошибок

### 5.1 Успешный деплой

В логах вы увидите:
```
INFO - Запускаем телеграм-бота...
INFO - Application started
```

### 5.2 Если есть ошибки

Частые проблемы:
- **Неверный токен**: проверьте `TELEGRAM_BOT_TOKEN`
- **Ошибка Supabase**: проверьте URL и ключ
- **Зависимости**: убедитесь, что `requirements.txt` корректен

## 🔄 Шаг 6: Настройка автообновлений

### 6.1 Webhook в GitHub

Railway автоматически настроит webhook для автодеплоя при изменениях в репозитории.

### 6.2 Проверка работы

1. **Найдите бота** в Telegram по имени
2. **Отправьте** тестовое сообщение
3. **Получите** ответ "Сохранил"
4. **Проверьте** данные в Supabase

## 📊 Мониторинг

### 7.1 Логи Railway

- **Railway Dashboard** → **Deployments** → **View Logs**
- Здесь видны все сообщения бота

### 7.2 Метрики

Railway показывает:
- **CPU usage** - использование процессора
- **Memory** - потребление памяти
- **Network** - сетевой трафик

## 💰 Тарифы Railway

### Бесплатный план
- ✅ **500 часов** в месяц
- ✅ **512 MB RAM**
- ✅ **1 GB диск**
- ✅ **Автосон** при неактивности

### Для продакшена
- 💳 **$5/месяц** за проект
- ✅ **Без лимитов времени**
- ✅ **Больше ресурсов**

## 🛠️ Troubleshooting

### Бот не отвечает
```bash
# Проверьте логи
Railway Dashboard → Logs

# Частые причины:
- Неверный токен
- Проблемы с Supabase
- Ошибка в коде
```

### Ошибки базы данных
```bash
# Проверьте таблицу в Supabase
CREATE TABLE telegram_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    message_text TEXT,
    message_id BIGINT,
    chat_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Проблемы с деплоем
```bash
# Проверьте файлы:
- deployment/Procfile
- deployment/runtime.txt
- bot/requirements.txt

# Убедитесь в правильности путей
```

## 🎯 Результат

После успешного деплоя:

- ✅ **Бот работает 24/7** в облаке Railway
- ✅ **Автоматические перезапуски** при сбоях
- ✅ **Логи доступны** в реальном времени
- ✅ **Автодеплой** при изменениях в GitHub
- ✅ **Масштабирование** по необходимости

## 🔗 Полезные ссылки

- [Railway Documentation](https://docs.railway.app/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Supabase Documentation](https://supabase.com/docs)
- [Python-telegram-bot](https://python-telegram-bot.readthedocs.io/)

---

**Поздравляем! 🎉 Ваш бот работает в облаке!**
