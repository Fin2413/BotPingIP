import telebot
from pythonping import ping
import subprocess
import chardet
from telebot import types
import time
import threading


# Укажите токен вашего телеграмм бота
TOKEN = '6568395720:AAEVlxUZIvgDoqIPgEvAesCbSlogZGJieXg'
bot = telebot.TeleBot(TOKEN)



tracert_results = {}  # Словарь для хранения результатов трассировки по IP-адресам
authorized_users = {}  # Словарь для хранения авторизованных пользователей (только chat_id и authorized)
ast_interaction = {}  # Словарь для хранения времени последнего взаимодействия пользователя с ботом
last_interaction = {}  # Определение переменной last_interactioЫ

def decode_output(output_bytes):
    detected_encoding = chardet.detect(output_bytes)['encoding']
    return output_bytes.decode(detected_encoding)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('Авторизация'))
    bot.send_message(chat_id, "Для авторизации нажмите кнопку 'Авторизация'", reply_markup=markup)
    last_interaction[chat_id] = time.time()  # Записываем время начала взаимодействия

@bot.message_handler(func=lambda message: message.text == 'Авторизация')
def handle_authorization(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Пожалуйста, введите логин:")
    bot.register_next_step_handler(message, process_login_step)


def process_login_step(message):
    chat_id = message.chat.id
    login = message.text
    authorized_users[chat_id] = {"login": login}
    bot.send_message(chat_id, "Пожалуйста, введите пароль:")
    bot.register_next_step_handler(message, process_password_step)

def process_password_step(message):
    chat_id = message.chat.id
    password = message.text
    user_data = authorized_users.get(chat_id)
    if user_data:
        user_login = user_data.get("login")
        if user_login == "user1" and password == "1111":
            authorized_users[chat_id]["authorized"] = True
            bot.send_message(chat_id, f"Добро пожаловать, {user_login}. Теперь вы можете использовать команды.")
        elif user_login == "user2" and password == "2222":
            authorized_users[chat_id]["authorized"] = True
            bot.send_message(chat_id, f"Добро пожаловать, {user_login}. Теперь вы можете использовать команды.")
        else:
            bot.send_message(chat_id, "Неверный логин или пароль. Попробуйте еще раз.")
            bot.send_message(chat_id, "Пожалуйста, введите логин:")
            bot.register_next_step_handler(message, process_login_step)

# Функция для проверки времени последнего взаимодействия с ботом и выхода из учетной записи после 10 минут
def check_activity():
    while True:
        current_time = time.time()
        for chat_id, last_time in last_interaction.items():
            if current_time - last_time > 600:  # 600 секунд = 10 минут
                authorized_users.pop(chat_id, None)
                last_interaction.pop(chat_id, None)
        time.sleep(60)  # Проверяем каждую минуту

# Запуск функции для проверки активности пользователя
activity_thread = threading.Thread(target=check_activity)
activity_thread.start()

@bot.message_handler(commands=['ping'])
def send_ping(message):
    chat_id = message.chat.id
    if chat_id in authorized_users and authorized_users.get(chat_id, {}).get("authorized"):
        try:
            ip_address = message.text.split()[1]
            ping_result = ping(ip_address, count=4)
            if ping_result.success():
                bot.reply_to(message, f"Оборудование с IP-адресом {ip_address} доступно.")
            else:
                bot.reply_to(message, f"Оборудование с IP-адресом {ip_address} недоступно.")
        except (IndexError, Exception) as e:
            bot.reply_to(message, "Неверный формат команды. Пожалуйста, используйте /ping [IP-адрес].")
    else:
        bot.reply_to(message, "Вы не авторизованы. Пожалуйста, авторизуйтесь, чтобы использовать эту команду.")

@bot.message_handler(commands=['get_tracert'])
def get_tracert(message):
    chat_id = message.chat.id
    if chat_id in authorized_users and authorized_users.get(chat_id, {}).get("authorized"):
        try:
            ip_address = message.text.split()[1]
            tracert_output = subprocess.check_output(["tracert", ip_address]).decode('cp866')
            bot.reply_to(message, f"Результат трассировки для IP-адреса {ip_address} {tracert_output}")
        except (IndexError, Exception) as e:
            bot.reply_to(message, "Произошла ошибка. Пожалуйста, попробуйте еще раз.")
    else:
        bot.reply_to(message, "Вы не авторизованы. Пожалуйста, авторизуйтесь, чтобы использовать эту команду.")

@bot.message_handler(commands=['help'])
def help(message):
    chat_id = message.chat.id
    if chat_id in authorized_users and authorized_users.get(chat_id, {}).get("authorized"):
        response_text = """
            Список доступных команд:

            1. /ping [IP-адрес] - Проверить доступность оборудования по IP-адресу.
            2. /get_tracert [IP-адрес] - Получить результат трассировки до указанного IP-адреса.
        """
        # Отправка сообщения с ответом в виде списка
        bot.send_message(message.from_user.id, response_text, parse_mode='HTML')
    else:
        bot.reply_to(message, "Вы не авторизованы. Пожалуйста, авторизуйтесь, чтобы использовать эту команду.")

bot.polling()
