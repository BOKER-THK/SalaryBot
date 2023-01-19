import io
import time
from essentials import API_KEY, DATA_PATH
import utils
from DatabaseLevel import get_row, update_data, update_row, produce_graph, produce_report
import datetime
import telebot
import requests

pic_path = DATA_PATH + "SalaryChart.png"

bot = telebot.TeleBot(API_KEY)


@bot.message_handler(commands=["start", "help"])
def print_menu(message):
    bot.send_message(message.chat.id, "Welcome to the Salary bot!\n"
                                      "You may enter a command from the options below:\n"
                                      "[To be filled later...]")


@bot.message_handler(commands=["insert"])
def insert_single_row(message):
    bot.send_message(message.chat.id, "Enter the info in format [year, month, total, taxes, earnings]: ")
    bot.register_next_step_handler(message, insert_row)


@bot.message_handler(content_types=["document"])
def document_insertion(message):
    f_info = bot.get_file(message.document.file_id)
    file = requests.get(f'https://api.telegram.org/file/bot{API_KEY}/{f_info.file_path}').content
    df = utils.create_salary_df(io.BytesIO(file))
    add_data(message, df)


@bot.message_handler(commands=["graph"])
def plot_graph(message):
    produce_graph()
    bot.send_photo(message.chat.id, open(pic_path, "rb"))


@bot.message_handler(commands=["report"])
def create_report(message):
    produce_report()
    bot.send_photo(message.chat.id, open(pic_path, "rb"))


def insert_row(message):
    info_list = message.text.split(',')
    info_list = list(map(int, info_list))
    info_date = datetime.datetime(year=info_list.pop(0), month=info_list.pop(0), day=1)

    new_row = utils.create_salary_df(None)
    new_row.loc[info_date] = info_list
    add_data(message, new_row)


def add_data(message, data):
    try:
        update_data(data)
        bot.reply_to(message, "data added successfully.")
    except utils.DuplicateException as exp:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        replace_btn = telebot.types.KeyboardButton("Replace")
        discard_btn = telebot.types.KeyboardButton("Discard")
        markup.row(replace_btn, discard_btn)
        bot.send_message(message.chat.id, "An error occurred: duplicate information was found.", reply_markup=markup)
        time.sleep(2)
        duplicate_handler(message, exp.duplicate_df, begin=True)


def duplicate_handler(message, data, index=0, begin=False):
    if not begin:
        if message.text == "Replace":
            update_row(index, data.iloc[0])
            bot.send_message(message.chat.id, "Data updated.")
        else:
            bot.send_message(message.chat.id, "Your changes have been discarded.")
    if data.index.size > 0:
        i = data.index[0]
        bot.send_message(message.chat.id, f"The date inserted {i.month}/{i.year % 100} is already in the system.")
        bot.send_message(message.chat.id, f"current: {get_row(i)},\nnew: {get_row(i, data)}")
        bot.send_message(message.chat.id, "Do you want to replace the existing entry, or discard the changes?")
        bot.register_next_step_handler(message, duplicate_handler, data.loc[data.index.drop(i)], i)
    else:
        markup = telebot.types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "data added successfully.", reply_markup=markup)


bot.polling()
