# 🔑 Токены и переменные окружения

## 📋 Для Railway Dashboard

Добавьте эти переменные в **Railway** → **Variables**:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
SUPABASE_URL=https://acadfirvavgabutlxdvx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFjYWRmaXJ2YXZnYWJ1dGx4ZHZ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg2MDM3ODcsImV4cCI6MjA3NDE3OTc4N30.3k-Xo-WqasrgufysdMtrzT0BHSzmkx_pVgBJcu5_33E
```

## 📱 Для локальной разработки

Создайте файл `.env` в корне проекта:

```bash
# Скопируйте шаблон
cp env.example.detailed .env

# Отредактируйте файл
nano .env  # или любой редактор
```

## 🔑 Как получить TELEGRAM_BOT_TOKEN

1. Найдите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/mybots` (если бот уже есть) или `/newbot` (создать нового)
3. Выберите бота → **API Token**
4. Скопируйте токен вида: `1234567890:AAHz8c8UlJQyX5jD9ERUECzgI1dZhBNPoD0`

## 🗄️ Supabase данные

Ваши данные уже готовы:
- **URL**: `https://acadfirvavgabutlxdvx.supabase.co`
- **Anon Key**: готов к использованию
- **Таблица**: `telegram_messages` уже создана и оптимизирована

## ⚠️ Безопасность

- ❌ **НЕ коммитьте** `.env` файл в Git
- ✅ **Используйте** переменные окружения в продакшене
- 🔄 **Обновляйте** токены при необходимости

---

**Все готово для использования! 🚀**
