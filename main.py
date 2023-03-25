
from config import TOKEN
from extensions import MOEX, info
from extensions import APIException
import traceback

# print(info('moex'))
# print(MOEX.get_price(1000, "uzs", "zar", False))
# print(MOEX.get_price(1000, "usd", "eur", False))
# print(MOEX.get_price(1000, "usd", "rub", False))
# print(MOEX.get_price(1000, "rub", "usd", False))
import telebot
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.last_name is not None:
        last_name =" " + str(message.chat.last_name)
    else:
        last_name =""
    bot.send_message(message.chat.id,f"Привет, {message.chat.first_name}{last_name}! "
                                     f"Меня зовут {bot.user.username}. Введите команду /help и я расскажу, что умею.")


@bot.message_handler(commands=['help'])
def information(message: telebot.types.Message):
    text = "Я могу конвертировать валюты.\n" \
           "Для этого нужно ввести 3 параметра:\n" \
           "'количество переводимой валюты' 'имя валюты' 'имя валюты в которую перевести'\n" \
           "Например: 100 usd rub\n" \
           "Чтобы узнать список всех доступных валют введите команду /value"  # тут нужна кнопка
    bot.reply_to(message,text)


@bot.message_handler(commands=['value'])
def list_currency_names(message: telebot.types.Message):
    text = "Список доступных валют: \n"
    bot.reply_to(message, f"{text}{info('moex')}")

@bot.message_handler(content_types=['text'])
def text_handler(message: telebot.types.Message):
    if message.text == "Список":
        text = "Список доступных валют: \n"
        bot.reply_to(message, f"{text} {info('moex')}")
    else:
        values = message.text.split(" ")
        try:
            if len(values) != 3:
                raise APIException('Я не знаю такую команду, для конвертации валют нужно 3 параметра!')
            answer = MOEX.get_price(*values)
        except APIException as e:
            bot.reply_to(message, f"Ошибка в команде:\n{e}")
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            bot.reply_to(message, f"Неизвестная ошибка:\n{e}")
        else:
            bot.reply_to(message, answer)

bot.polling(none_stop=True)


