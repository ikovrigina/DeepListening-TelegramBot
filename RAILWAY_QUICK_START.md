# 🚂 Railway Quick Start

## 🚀 Быстрый деплой за 5 минут

### 1. Создайте проект на Railway
1. Откройте [railway.app](https://railway.app/)
2. Войдите через GitHub
3. **New Project** → **Deploy from GitHub repo**
4. Выберите `ikovrigina/DeepListening-TelegramBot`
5. Нажмите **Deploy**

### 2. Добавьте переменные окружения

В Railway Dashboard → **Variables** добавьте:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E
```

### 3. Получите Telegram Bot Token

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/mybots` или `/newbot`
3. Скопируйте токен и вставьте в `TELEGRAM_BOT_TOKEN`

### 4. Деплой завершен! 🎉

- ✅ Бот автоматически запустится
- ✅ Будет работать 24/7
- ✅ Автоматические обновления при изменениях в GitHub
- ✅ Логи доступны в Railway Dashboard

### 5. Тестирование

1. Найдите вашего бота в Telegram
2. Отправьте любое сообщение
3. Получите ответ "Сохранил"
4. Проверьте данные в Supabase Dashboard

---

**Готово! Ваш бот работает в облаке! 🚀**

Подробная инструкция: [`docs/RAILWAY_DEPLOYMENT.md`](docs/RAILWAY_DEPLOYMENT.md)

