import telebot
from PIL import Image
import pytesseract
import re
import io
import os
import threading

BOT_TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

chat_numbers = {}
DELETE_REPLY_AFTER = 20*60

def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except:
        pass

@bot.message_handler(content_types=['photo'])
def process_image(message):
    chat_id = message.chat.id
    message_id = message.message_id
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(io.BytesIO(downloaded_file))

        text = pytesseract.image_to_string(image)

        pattern = r'(?:\+1[\s\.-]?|1[\s\.-]?)?\(?([2-9][0-9]{2})\)?[\s\.-]?([0-9]{3})[\s\.-]?([0-9]{4})'
        matches = re.findall(pattern, text)

        safe_delete(chat_id, message_id)

        if not matches:
            return

        numbers = [f"+1{m[0]}{m[1]}{m[2]}" for m in matches]
        chat_numbers.setdefault(chat_id, set()).update(numbers)

        reply = bot.send_message(chat_id, "\n".join(numbers))
        threading.Timer(DELETE_REPLY_AFTER, lambda: safe_delete(chat_id, reply.message_id)).start()

    except:
        pass

@bot.message_handler(commands=['all_numbers'])
def all_numbers(message):
    nums = chat_numbers.get(message.chat.id, set())
    if not nums:
        return
    reply = bot.send_message(message.chat.id, "\n".join(sorted(nums)))
    threading.Timer(DELETE_REPLY_AFTER, lambda: safe_delete(message.chat.id, reply.message_id)).start()

bot.infinity_polling()
