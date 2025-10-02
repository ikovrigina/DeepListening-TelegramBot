# 🗄️ Настройка базы данных Supabase

Подробное руководство по настройке базы данных Supabase для DeepListening Telegram Bot.

## 🎯 Обзор

DeepListening Bot сохраняет все сообщения в таблицу `telegram_messages` в базе данных Supabase PostgreSQL.

## 🚀 Быстрая настройка

### 1. Создание проекта Supabase

1. **Зарегистрируйтесь** на [supabase.com](https://supabase.com/)
2. **Создайте новый проект**:
   - Название: `DeepListening Bot`
   - Пароль базы данных: сохраните его!
   - Регион: выберите ближайший

### 2. Создание таблицы

В **SQL Editor** выполните:

```sql
-- Создание таблицы для сообщений
CREATE TABLE telegram_messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    message_text TEXT NOT NULL,
    message_id BIGINT NOT NULL,
    chat_id BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX idx_telegram_messages_user_id ON telegram_messages(user_id);
CREATE INDEX idx_telegram_messages_chat_id ON telegram_messages(chat_id);
CREATE INDEX idx_telegram_messages_created_at ON telegram_messages(created_at);

-- Комментарии к полям
COMMENT ON TABLE telegram_messages IS 'Сообщения от Telegram бота';
COMMENT ON COLUMN telegram_messages.user_id IS 'ID пользователя в Telegram';
COMMENT ON COLUMN telegram_messages.username IS 'Username пользователя (@username)';
COMMENT ON COLUMN telegram_messages.first_name IS 'Имя пользователя';
COMMENT ON COLUMN telegram_messages.last_name IS 'Фамилия пользователя';
COMMENT ON COLUMN telegram_messages.message_text IS 'Текст сообщения';
COMMENT ON COLUMN telegram_messages.message_id IS 'ID сообщения в Telegram';
COMMENT ON COLUMN telegram_messages.chat_id IS 'ID чата в Telegram';
```

## 📊 Структура таблицы

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | UUID | ✅ | Уникальный идентификатор записи |
| `user_id` | BIGINT | ✅ | ID пользователя в Telegram |
| `username` | TEXT | ❌ | Username пользователя (может отсутствовать) |
| `first_name` | TEXT | ❌ | Имя пользователя |
| `last_name` | TEXT | ❌ | Фамилия пользователя |
| `message_text` | TEXT | ✅ | Текст сообщения |
| `message_id` | BIGINT | ✅ | ID сообщения в Telegram |
| `chat_id` | BIGINT | ✅ | ID чата |
| `created_at` | TIMESTAMP | ✅ | Время создания записи |

## 🔐 Настройка безопасности

### Row Level Security (RLS)

По умолчанию Supabase включает RLS. Для работы бота создайте политику:

```sql
-- Отключаем RLS для этой таблицы (бот использует service_role ключ)
ALTER TABLE telegram_messages DISABLE ROW LEVEL SECURITY;

-- Или создаем политику для anon ключа
ALTER TABLE telegram_messages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow insert for anon users" ON telegram_messages
    FOR INSERT 
    TO anon 
    WITH CHECK (true);

CREATE POLICY "Allow select for anon users" ON telegram_messages
    FOR SELECT 
    TO anon 
    USING (true);
```

### API ключи

В **Settings** → **API** найдите:

1. **Project URL**: `https://your-project.supabase.co`
2. **anon key**: для клиентских приложений
3. **service_role key**: для серверных приложений (более мощный)

> 💡 **Рекомендация**: используйте `anon` ключ для бота

## 📈 Полезные запросы

### Просмотр последних сообщений
```sql
SELECT 
    first_name,
    username,
    message_text,
    created_at
FROM telegram_messages 
ORDER BY created_at DESC 
LIMIT 10;
```

### Статистика по пользователям
```sql
SELECT 
    first_name,
    username,
    COUNT(*) as message_count,
    MAX(created_at) as last_message
FROM telegram_messages 
GROUP BY user_id, first_name, username
ORDER BY message_count DESC;
```

### Сообщения за сегодня
```sql
SELECT COUNT(*) as today_messages
FROM telegram_messages 
WHERE DATE(created_at) = CURRENT_DATE;
```

### Активность по часам
```sql
SELECT 
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as messages
FROM telegram_messages 
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;
```

## 🔄 Миграции и обновления

### Добавление новых полей

Если нужно добавить поля в будущем:

```sql
-- Добавить поле для типа сообщения
ALTER TABLE telegram_messages 
ADD COLUMN message_type TEXT DEFAULT 'text';

-- Добавить поле для геолокации
ALTER TABLE telegram_messages 
ADD COLUMN latitude DECIMAL(10,8),
ADD COLUMN longitude DECIMAL(11,8);

-- Добавить метаданные
ALTER TABLE telegram_messages 
ADD COLUMN metadata JSONB;
```

### Архивирование старых данных

```sql
-- Создать таблицу архива
CREATE TABLE telegram_messages_archive (
    LIKE telegram_messages INCLUDING ALL
);

-- Переместить старые данные (старше 6 месяцев)
WITH archived AS (
    DELETE FROM telegram_messages 
    WHERE created_at < NOW() - INTERVAL '6 months'
    RETURNING *
)
INSERT INTO telegram_messages_archive 
SELECT * FROM archived;
```

## 📊 Мониторинг и аналитика

### Создание представлений

```sql
-- Представление для дневной статистики
CREATE VIEW daily_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_messages,
    COUNT(DISTINCT user_id) as unique_users
FROM telegram_messages 
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Представление для топ пользователей
CREATE VIEW top_users AS
SELECT 
    user_id,
    first_name,
    username,
    COUNT(*) as message_count,
    MIN(created_at) as first_message,
    MAX(created_at) as last_message
FROM telegram_messages 
GROUP BY user_id, first_name, username
ORDER BY message_count DESC;
```

## 🛠️ Troubleshooting

### Проблема: Таблица не создается
```sql
-- Проверьте права доступа
SELECT current_user, current_database();

-- Проверьте существование таблицы
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'telegram_messages';
```

### Проблема: Бот не может писать в БД
```sql
-- Проверьте политики RLS
SELECT * FROM pg_policies 
WHERE tablename = 'telegram_messages';

-- Временно отключите RLS для тестирования
ALTER TABLE telegram_messages DISABLE ROW LEVEL SECURITY;
```

### Проблема: Медленные запросы
```sql
-- Проверьте использование индексов
EXPLAIN ANALYZE 
SELECT * FROM telegram_messages 
WHERE user_id = 123456789;

-- Создайте дополнительные индексы при необходимости
CREATE INDEX idx_telegram_messages_message_text 
ON telegram_messages USING gin(to_tsvector('russian', message_text));
```

## 📈 Оптимизация производительности

### Партиционирование по датам

Для больших объемов данных:

```sql
-- Создать партиционированную таблицу
CREATE TABLE telegram_messages_partitioned (
    LIKE telegram_messages INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Создать партиции по месяцам
CREATE TABLE telegram_messages_2024_01 
PARTITION OF telegram_messages_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE telegram_messages_2024_02 
PARTITION OF telegram_messages_partitioned
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

## 🔗 Интеграции

### Webhook для уведомлений

```sql
-- Создать функцию для уведомлений
CREATE OR REPLACE FUNCTION notify_new_message()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify('new_message', 
        json_build_object(
            'user_id', NEW.user_id,
            'message_text', NEW.message_text,
            'created_at', NEW.created_at
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создать триггер
CREATE TRIGGER telegram_message_notification
    AFTER INSERT ON telegram_messages
    FOR EACH ROW
    EXECUTE FUNCTION notify_new_message();
```

## 🎯 Результат

После настройки у вас будет:

- ✅ **Надежная база данных** в облаке
- ✅ **Автоматическое резервное копирование**
- ✅ **Масштабируемость** до миллионов записей
- ✅ **Быстрые запросы** благодаря индексам
- ✅ **Аналитика** через SQL запросы
- ✅ **Безопасность** через RLS политики

---

**База данных готова к работе! 🎉**
