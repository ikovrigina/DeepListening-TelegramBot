# DeepListening Telegram Bot - Railway Deployment

## 🚀 Пошаговая инструкция для Railway

### 1. Подготовка проекта

Создадим файлы для Railway:

#### `Procfile` (для запуска бота):
```
web: python telegram_bot.py
```

#### `runtime.txt` (версия Python):
```
python-3.9.18
```

### 2. Настройка Railway

1. **Зарегистрируйтесь**: https://railway.app/
2. **Создайте новый проект**: "New Project" → "Deploy from GitHub repo"
3. **Подключите GitHub** (если нужно создать репозиторий)
4. **Выберите репозиторий** с ботом

### 3. Переменные окружения в Railway

В настройках проекта Railway добавьте:

```
TELEGRAM_BOT_TOKEN=8272024094:AAHz8c8UlJQyX5jD9ERUECzgI1dZhBNPoD0
SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E
```

### 4. Деплой

Railway автоматически развернет бота после подключения репозитория.

## 🎉 Результат

- ✅ Бот работает 24/7 в облаке
- ✅ Автоматические перезапуски при сбоях
- ✅ Логи доступны в Railway Dashboard
- ✅ Бесплатно (500 часов в месяц)

## 🔧 Альтернатива: Render

Если Railway не подходит:

1. **Зарегистрируйтесь**: https://render.com/
2. **Создайте Web Service** из GitHub репозитория
3. **Настройте переменные окружения**
4. **Деплой**: автоматический
