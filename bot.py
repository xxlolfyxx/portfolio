import telebot
import schedule
import time
import threading
from datetime import datetime, timedelta
import pytz

# ВСТАВЬ СВОЙ ТОКЕН МЕЖДУ КАВЫЧКАМИ НИЖЕ (например: '123456:ABC-DEF...')
TOKEN = '8867057223:AAF06Qc-CnC-82Xd00Gz9tyI4DzVJrEwRRc'
bot = telebot.TeleBot(TOKEN)

# Настраиваем часовой пояс Алматы
ALMATY_TZ = pytz.timezone('Asia/Almaty')

def send_reminder(chat_id, text, target_time_str):
    """Функция, которая сработает в назначенное время"""
    reminder_text = f"⏰ **Напоминание на {target_time_str}!**\n\n🎯 Задача: {text}"
    bot.send_message(chat_id, reminder_text, parse_mode='Markdown')

def parse_time_and_text(message_text):
    """
    Разбирает текст сообщения. Находит время (абсолютное '18:30' или относительное 'через 2 минуты')
    и отделяет его от самого текста напоминания.
    """
    now_almaty = datetime.now(ALMATY_TZ)
    text_lower = message_text.lower().strip()
    
    # 1. Вариант: через Х минут
    if "через" in text_lower and "минут" in text_lower:
        try:
            parts = text_lower.split("через")
            after_cherez = parts[1].strip()
            number_str = after_cherez.split()[0]
            minutes = int(number_str)
            target_time = now_almaty + timedelta(minutes=minutes)
            
            clean_text = message_text
            for word in ["через", number_str, "минут", "минуты", "минуту"]:
                clean_text = clean_text.replace(word, "", 1).replace(word.capitalize(), "", 1)
            clean_text = clean_text.strip()
            if not clean_text: clean_text = "Таймер завершен!"
            return target_time, clean_text
        except (ValueError, IndexError): pass

    # 2. Вариант: через Х часов
    if "через" in text_lower and ("час" in text_lower or "ч" in text_lower):
        try:
            parts = text_lower.split("через")
            after_cherez = parts[1].strip()
            number_str = after_cherez.split()[0]
            hours = int(number_str)
            target_time = now_almaty + timedelta(hours=hours)
            
            clean_text = message_text
            for word in ["через", number_str, "час", "часа", "часов", "ч"]:
                clean_text = clean_text.replace(word, "", 1).replace(word.capitalize(), "", 1)
            clean_text = clean_text.strip()
            if not clean_text: clean_text = "Таймер завершен!"
            return target_time, clean_text
        except (ValueError, IndexError): pass

    # 3. Вариант: Точное время (18:30)
    try:
        time_part = message_text.split()[0]
        valid_time = datetime.strptime(time_part, "%H:%M")
        target_time = now_almaty.replace(hour=valid_time.hour, minute=valid_time.minute, second=0, microsecond=0)
        if target_time < now_almaty:
            target_time = target_time + timedelta(days=1)
        clean_text = message_text.replace(time_part, "", 1).strip()
        if not clean_text: clean_text = "Дело без названия"
        return target_time, clean_text
    except ValueError:
        return None, None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я твой умный планировщик задач по времени Алматы.\n\n"
        "**Как мне можно писать:**\n"
        "• `18:30 Позвонить папе` — поставлю на точное время\n"
        "• `через 5 минут проверить бота` — сработает быстрый таймер\n"
        "• `через 2 часа пойти на тренировку` — напомню через пару часов"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_reminder(message):
    target_time, reminder_text = parse_time_and_text(message.text)
    if target_time is None:
        bot.reply_to(message, "❌ Не смог распознать время. Напиши, например: `15:45 Задача` или `через 10 минут Задача`.")
        return
        
    time_str = target_time.strftime("%H:%M")
    now_almaty = datetime.now(ALMATY_TZ)
    delay_seconds = (target_time - now_almaty).total_seconds()
    
    if delay_seconds < 0:
        bot.reply_to(message, "🤔 Кажется, это время уже прошло.")
        return

    threading.Timer(delay_seconds, send_reminder, argument=[message.chat_id, reminder_text, time_str]).start()
    bot.reply_to(message, f"✅ Принято! Напоминание установлено на **{time_str}** (по Алматы).\n🎯 Задача: {reminder_text}", parse_mode='Markdown')

if __name__ == '__main__':
    print("Бот успешно запущен по времени Алматы...")
    bot.infinity_polling()