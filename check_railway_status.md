# Проверка статуса Railway

## Что нужно сделать:

1. **Перейдите на https://railway.app**
2. **Войдите в свой аккаунт**
3. **Найдите проект DeepListening-TelegramBot**
4. **Проверьте статус деплоя:**
   - Зеленый статус = работает
   - Красный статус = ошибка
   - Желтый статус = деплоится

## Если проект НЕ найден:
Нужно создать новый проект на Railway:
1. New Project → Deploy from GitHub repo
2. Выберите `ikovrigina/DeepListening-TelegramBot`
3. Добавьте переменные окружения

## Если проект найден, но не работает:
1. Откройте вкладку **"Logs"**
2. Посмотрите последние ошибки
3. Проверьте переменные окружения в **Settings → Environment Variables**

## Переменные окружения должны быть:
```
TELEGRAM_BOT_TOKEN=8272024094:AAHz8c8UlJQyX5jD9ERUECzgI1dZhBNPoD0
SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E
```

## После настройки Railway:
Попробуйте отправить `/start` боту @DeepListeningBot в Telegram

