-- 🗄️ SQL скрипт для создания таблиц DeepListening Bot

-- 1. Таблица пользователей
CREATE TABLE IF NOT EXISTS listening_users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    morning_reminder_enabled BOOLEAN DEFAULT TRUE,
    morning_time TIME DEFAULT '08:00:00',
    timezone TEXT DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Таблица сессий прослушивания
CREATE TABLE IF NOT EXISTS listening_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id BIGINT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    environment_description TEXT,
    feelings_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Таблица аудио файлов
CREATE TABLE IF NOT EXISTS audio_files (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES listening_sessions(id),
    file_id TEXT NOT NULL,
    duration INTEGER,
    message_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_listening_users_telegram_user_id ON listening_users(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_listening_sessions_user_id ON listening_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_listening_sessions_started_at ON listening_sessions(started_at);
CREATE INDEX IF NOT EXISTS idx_audio_files_session_id ON audio_files(session_id);

-- Отключаем RLS для работы с anon ключом
ALTER TABLE listening_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE listening_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE audio_files DISABLE ROW LEVEL SECURITY;

-- Комментарии к таблицам
COMMENT ON TABLE listening_users IS 'Пользователи DeepListening Bot';
COMMENT ON TABLE listening_sessions IS 'Сессии практики слушания';
COMMENT ON TABLE audio_files IS 'Аудио файлы от пользователей';

