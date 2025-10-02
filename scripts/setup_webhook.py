#!/usr/bin/env python3
"""
Скрипт для настройки Telegram webhook для Edge Function
"""

import os
import requests
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SUPABASE_URL = "https://acadfirvavgabutlxdvx.supabase.co"
WEBHOOK_URL = f"{SUPABASE_URL}/functions/v1/telegram-bot-webhook"

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!")
    exit(1)

def set_webhook():
    """Устанавливаем webhook для Telegram бота"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    
    data = {
        'url': WEBHOOK_URL,
        'allowed_updates': ['message']  # Получаем только сообщения
    }
    
    print(f"🔗 Устанавливаем webhook: {WEBHOOK_URL}")
    
    response = requests.post(url, json=data)
    result = response.json()
    
    if result.get('ok'):
        print("✅ Webhook успешно установлен!")
        print(f"📝 Описание: {result.get('description', 'N/A')}")
    else:
        print(f"❌ Ошибка установки webhook: {result}")
        return False
    
    return True

def get_webhook_info():
    """Получаем информацию о текущем webhook"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    
    response = requests.get(url)
    result = response.json()
    
    if result.get('ok'):
        webhook_info = result.get('result', {})
        print("\n📊 Информация о webhook:")
        print(f"   URL: {webhook_info.get('url', 'Не установлен')}")
        print(f"   Статус: {'Активен' if webhook_info.get('url') else 'Не активен'}")
        print(f"   Последняя ошибка: {webhook_info.get('last_error_message', 'Нет ошибок')}")
        print(f"   Ожидающих обновлений: {webhook_info.get('pending_update_count', 0)}")
    else:
        print(f"❌ Ошибка получения информации: {result}")

def delete_webhook():
    """Удаляем webhook (возвращаемся к polling)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
    
    response = requests.post(url)
    result = response.json()
    
    if result.get('ok'):
        print("🗑️ Webhook удален!")
    else:
        print(f"❌ Ошибка удаления webhook: {result}")

if __name__ == "__main__":
    print("🤖 DeepListening Telegram Bot - Настройка Webhook")
    print("=" * 50)
    
    # Показываем текущую информацию
    get_webhook_info()
    
    print("\nВыберите действие:")
    print("1. Установить webhook для Edge Function")
    print("2. Удалить webhook (вернуться к polling)")
    print("3. Показать информацию о webhook")
    print("4. Выход")
    
    choice = input("\nВаш выбор (1-4): ").strip()
    
    if choice == "1":
        if set_webhook():
            print(f"\n🎉 Готово! Теперь бот работает через Edge Function:")
            print(f"   {WEBHOOK_URL}")
            print("\n💡 Не забудьте добавить переменные окружения в Supabase:")
            print("   - TELEGRAM_BOT_TOKEN")
            print("   - SUPABASE_SERVICE_ROLE_KEY")
    elif choice == "2":
        delete_webhook()
    elif choice == "3":
        get_webhook_info()
    elif choice == "4":
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор!")
