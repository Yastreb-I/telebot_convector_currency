import telebot
from telebot import types
import traceback

from config import TOKEN
from extensions import Moex
from extensions import APIException


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.last_name is not None:
        last_name = " " + str(message.chat.last_name)
    else:
        last_name = ""
    bot.send_message(message.chat.id, f"Привет, {message.chat.first_name}{last_name}! "
                                      f"Меня зовут {bot.user.username}. Введите команду /help и я расскажу, что умею.",
                     )


@bot.message_handler(commands=['help'])
def information(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bt_list_cur = types.KeyboardButton("Список валют")
    btn_exch_rates = types.KeyboardButton("Курсы валют")
    markup.add(bt_list_cur, btn_exch_rates)

    text = "Я могу конвертировать валюты.\n" \
           "Для этого нужно ввести <b>3 параметра</b>:\n" \
           "'количество переводимой валюты' 'имя валюты' 'имя валюты в которую перевести'\n" \
           "Например: 100 usd rub\n" \
           "Чтобы узнать список всех доступных валют введите команду /value"  # тут нужна кнопка
    bot.reply_to(message, text, reply_markup=markup, parse_mode="HTML")


@bot.message_handler(commands=['value'])
def list_currency_names(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bt_list_cur = types.KeyboardButton("Список валют")
    btn_exch_rates = types.KeyboardButton("Курсы валют")
    markup.add(bt_list_cur, btn_exch_rates)
    text = "Список доступных валют: \n"
    bot.reply_to(message, f"{text}{Moex.info('moex')}", reply_markup=markup, parse_mode="HTML")


@bot.message_handler(content_types=['text'])
def text_handler(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bt_list_cur = types.KeyboardButton("Список валют")
    btn_exch_rates = types.KeyboardButton("Курсы валют")
    btn_what_i_can = types.KeyboardButton("/help")  # Как пользоваться?
    markup.add(bt_list_cur, btn_exch_rates)
    markup.add(btn_what_i_can)
    if message.text.lower() == "список валют":
        text = "Список доступных валют: \n"
        bot.reply_to(message, f"{text}{Moex.info('moex')}", reply_markup=markup, parse_mode="HTML")
    elif message.text.lower() == "курсы валют":
        text = "Курсы валют: \n"
        bot.reply_to(message, f"{text}{Moex.exchange_rates()}", reply_markup=markup, parse_mode="HTML")

    else:
        values = message.text.split(" ")
        try:
            if len(values) != 3:
                raise APIException('Я не знаю такую команду, для конвертации валют нужно 3 параметра!')
            answer = Moex.get_price(*values)
        except APIException as e:
            bot.reply_to(message, f"Ошибка в команде:\n{e}", reply_markup=markup)
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            bot.reply_to(message, f"Неизвестная ошибка:\n{e}", reply_markup=markup)
        else:
            bot.reply_to(message, answer, reply_markup=markup, parse_mode="HTML")


bot.polling(none_stop=True)
