# -*- coding: utf-8 -*-

import random
from datetime import datetime
from threading import Thread
from time import sleep

import schedule
import telebot

import config
import mybotdata as bdat
import mybotfunctions as bfunc
import withstickers as stick
from metrics import update_number_of_users
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot(config.token, skip_pending=True)

def update_user_data(message):
    bfunc.ex_command(
        "update bot_users set username = '@" + str(message.from_user.username) + "' where chat_id = '" + str(
            message.chat.id) + "';")
    bfunc.ex_command(
        "update bot_users set user_id = '" + str(message.from_user.id) + "' where chat_id = '" + str(
            message.chat.id) + "';")
    bfunc.ex_command(
        "update bot_users set first_name = '" + str(message.from_user.first_name) + "' where chat_id = '" + str(
            message.chat.id) + "';")
    bfunc.ex_command(
        "update bot_users set last_name = '" + str(message.from_user.last_name) + "' where chat_id = '" + str(
            message.chat.id) + "';")
    try:
        bfunc.ex_command(
            "update bot_users set user_photo = '" + str(
                bot.get_user_profile_photos(message.from_user.id).photos[0][0].file_id) + "' where chat_id = '" + str(
                message.chat.id) + "';")
    except:
        bfunc.ex_command(
            "update bot_users set user_photo = '" + "NoPhoto" + "' where chat_id = '" + str(
                message.chat.id) + "';")


@bot.message_handler(content_types=['voice'])
def get_voice(message):
    file_id = message.voice.file_id
    print(message.voice.file_id)
    # bot.send_voice(message.chat.id, file_id)
    """if str(message.chat.id) in bdat.authors_id:
        bfunc.ex_command("INSERT INTO voices (date, file_id, chat_id) VALUES (CURRENT_TIMESTAMP,'" + str(file_id) + "', '" + str(message.chat.id) + "');")
    else:"""
    bot.send_message(message.chat.id, 'Спасибо, мы приняли ваше голосовое сообщение, оно будет рассмотрено модератором.')
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Принять войс", callback_data="cb_yes", one_time_keyboard=True),
                               InlineKeyboardButton("Отклонить войс (удалить)", callback_data="cb_no", one_time_keyboard=True))
    bot.send_voice(bdat.authors_id[0], file_id, caption=f'{message.chat.id}', reply_markup=markup)
    bot.send_voice(bdat.authors_id[1], file_id, caption=f'{message.chat.id}', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cb_yes":
        bfunc.ex_command("INSERT INTO voices (date, file_id, chat_id, `trigger`) VALUES (CURRENT_TIMESTAMP,'" + str(call.message.voice.file_id) + "', '" + str(call.message.caption) + "', 1);")
        bot.answer_callback_query(call.id, "Войс добавлен в базу данных (все ок, больше жать не надо)")
        bot.send_message(call.message.caption, 'Ваше голосовое сообщение прошло модерацию. Теперь его смогут прослушать другие пользователи, когда обратятся за вдохновением.')
    elif call.data == "cb_no":
        bot.answer_callback_query(call.id, "Войс проигнорирован (все ок, больше жать не надо)")
    elif call.data == 'cb_voice':
        bot.answer_callback_query(call.id, "Буду отправлять голосовыми сообщениями")
        bfunc.ex_command(
            "update bot_users set achieve_method = '" + "voice" + "' where chat_id = '" + str(call.message.chat.id) + "';")
    elif call.data == 'cb_text':
        bot.answer_callback_query(call.id, "Буду отправлять текстовыми сообщениями")
        bfunc.ex_command(
            "update bot_users set achieve_method = '" + "text" + "' where chat_id = '" + str(call.message.chat.id) + "';")
    if call.data == "cb_insp_text_yes":
        bfunc.ex_command("INSERT INTO texts (date, text, chat_id, `trigger`) VALUES (CURRENT_TIMESTAMP,'" + call.message.text + "', '" + str(call.message.chat.id) + "', 1);")
        bot.answer_callback_query(call.id, "Текст добавлен в базу данных (все ок, больше жать не надо)")
        #bot.send_message(call.message.caption, 'Ваше текстовое сообщение прошло модерацию. Теперь его смогут прослушать другие пользователи, когда обратятся за вдохновением.')
    elif call.data == "cb_insp_text_no":
        bot.answer_callback_query(call.id, "Текст проигнорирован (все ок, больше жать не надо)")



""""@bot.callback_query_handler(func=lambda call: call.data.startswith('cb_yes', 'cb_no'))
def edit_message_approve(call):
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.id,
        text=f'{call.message.text}'
    )
"""

"""
@bot.message_handler(commands=['get_photos'])
def get_photos(message):
    photo = bot.get_user_profile_photos(message.from_user.id).photos[0][0].file_id
    bot.send_photo(message.chat.id, photo=photo, caption=f'{message.from_user.first_name} {message.from_user.last_name} {message.from_user.username}')
"""

@bot.message_handler(commands=['set_notification', 'stop', 'menu'])
def set_notification(message):
    update_user_data(message)
    bot.send_message(message.chat.id, 'Во сколько тебе напомнить о практике благодарности? (по часовому поясу MSK)',
                     reply_markup=bdat.many_moments)
    bot.register_next_step_handler(message, set_new_time)


@bot.message_handler(commands=['start', 'help'])
def welcome_message(message):
    if message.chat.id in bfunc.to_id_list(bfunc.data_command("select chat_id from bot_users")):
        bot.send_message(message.chat.id, "Вы уже прошли регистрацию в боте. Вы в главном меню.",
                         reply_markup=bdat.main_menu_buttons)
    else:
        update_number_of_users()
        bfunc.ex_command(
            "insert into bot_users(chat_id, date) values('" + str(message.chat.id) + "', CURRENT_TIMESTAMP)")
        update_user_data(message)
        bot.send_message(message.chat.id, bdat.welc_text, reply_markup=bdat.yes_no)
        bot.register_next_step_handler(message, _2)


"""bfunc.ex_command(
    "INSERT INTO notes (date, note, chat_id) VALUES (CURRENT_TIMESTAMP,'" + text + "', '" + str(
        message.chat.id) + "');")"""


def _2(message):
    if message.text == 'Да':
        bot.send_message(message.chat.id,
                         'Отлично! Используя практику благодарности, ты можешь стать позитивнее и счастливее. Так думают не только психологи, но и ученые.',
                         reply_markup=bdat.aga)
        bot.register_next_step_handler(message, _1_3)
    elif message.text == 'Нет':
        bot.send_message(message.chat.id,
                         'Практика благодарности — работающий способ улучшить своё благополучие и качество жизни. Она помогает сформировать привычку лучше относиться к себе и замечать больше хорошего. \n\n Кстати, практика благодарности используется в научно доказанной когнитивно-поведенческой терапии!',
                         reply_markup=bdat.what_to_do)
        bot.register_next_step_handler(message, _2_3)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, _2)


def _1_3(message):
    bot.send_message(message.chat.id,
                     'Сейчас приступим! Но для начала мне нужно чуть больше узнать о тебе. Как я могу к тебе обращаться? (Напиши имя)',
                     reply_markup=bdat.empty)
    bot.register_next_step_handler(message, your_name)


def _2_3(message):
    bot.send_message(message.chat.id,
                     'Все очень просто! Тебе нужно каждый день записывать что-то, за что ты ощущаешь благодарность.')
    bot.send_message(message.chat.id,
                     'Подойдут любые штуки, даже самые небольшие. Можно поблагодарить себя за вкусный обед, хорошую работу, прогулку, встречу с другом. Даже если что-то не получилось, важно поблагодарить себя за эту попытку.',
                     reply_markup=bdat.lets_try)
    bot.register_next_step_handler(message, _1_3)


def your_name(message):
    name = message.text
    bfunc.ex_command("update bot_users set nickname = '" + name + "' where chat_id = '" + str(message.chat.id) + "';")
    bot.send_message(message.chat.id,
                     "Хорошо, " + name + "! Как ты хочешь говорить о своих благодарностях?\n \n «Я благодарен» или «Я благодарна»",
                     reply_markup=bdat.gender)
    bot.register_next_step_handler(message, your_gender)


def your_gender(message):
    if message.text == 'Я благодарен':
        bfunc.ex_command("update bot_users set gender = 'male' where chat_id = '" + str(message.chat.id) + "';")
    elif message.text == 'Я благодарна':
        bfunc.ex_command("update bot_users set gender = 'female' where chat_id = '" + str(message.chat.id) + "';")
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, your_gender)
    bot.send_message(message.chat.id, bfunc.gender_text(message.chat.id, 'Ура! Ты готов записать первую благодарность?',
                                                        'Ура! Ты готова записать первую благодарность?'),
                     reply_markup=bdat.readiness)
    bot.register_next_step_handler(message, is_ready)


def is_ready(message):
    if message.text == 'Да!':
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                         reply_markup=bdat.empty)
        bot.register_next_step_handler(message, write_first_grate)
    elif message.text == 'Не знаю, что написать':
        ready_to_feel_keyb = telebot.types.ReplyKeyboardMarkup(True).row(
            bfunc.gender_text(message.chat.id, 'Готов чувствовать благодарность!',
                              'Готова чувствовать благодарность!')).row('Все еще ничего не приходит на ум')
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_feel_1_male, bdat.text_feel_1_female),
                         reply_markup=ready_to_feel_keyb)
        bot.register_next_step_handler(message, feel_grate_1)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, is_ready)


def feel_grate_1(message):
    if message.text == 'Готов чувствовать благодарность!' or message.text == 'Готова чувствовать благодарность!':
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                         reply_markup=bdat.empty)
        bot.register_next_step_handler(message, write_first_grate)
    if message.text == 'Все еще ничего не приходит на ум':
        bot.send_message(message.chat.id, bdat.text_feel_2, reply_markup=bdat.run)
        bot.register_next_step_handler(message, feel_grate_2)


def feel_grate_2(message):
    bot.send_message(message.chat.id,
                     bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                     reply_markup=bdat.empty)
    bot.register_next_step_handler(message, write_first_grate)


def write_first_grate(message):
    text = message.text
    try:
        bfunc.ex_command("INSERT INTO notes (date, note, chat_id) VALUES (CURRENT_TIMESTAMP,'" + text + "', '" + str(
            message.chat.id) + "');")
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.awesome_text_male, bdat.awesome_text_female),
                         reply_markup=bdat.result_feel)
        bot.register_next_step_handler(message, awesome)
    except Exception as ex:
        bot.send_message(message.chat.id, "Непредвиденная ошибка, попробуйте добавить благодарность снова.")
        bot.register_next_step_handler(message, write_first_grate)
        print(type(ex))


def awesome(message):
    if message.text == "Да, чувствую!":
        bot.send_message(message.chat.id,
                         "Здорово! Важно замечать, как отношение к себе и своим успехам по чуть-чуть меняется.")
    elif message.text == "Пока нет :(":
        bot.send_message(message.chat.id,
                         "Конечно, изменения происходят не так быстро. Но благодаря регулярной практике ты обязательно начнешь больше ценить себя, свои успехи и особенности")
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, awesome)
    bot.send_message(message.chat.id,
                     "Когда записываешь благодарность, старайся поглубже в нее погрузиться и прочувствовать ее.",
                     reply_markup=bdat.how_1)
    bot.register_next_step_handler(message, imaginate)


def imaginate(message):
    bot.send_message(message.chat.id,
                     "Представь, что друг сделал для тебя что-то очень хорошее, и ты чувствуешь тепло, радость, нежность. Только вот сейчас этот друг для себя — ты сам.",
                     reply_markup=stick.cute)

    bot.register_next_step_handler(message, dont_forget)


def dont_forget(message):
    bot.send_message(message.chat.id,
                     "Не забывай пересматривать старые благодарности и заново проживать их — так радости будет еще больше.",
                     reply_markup=bdat.safety)
    bot.register_next_step_handler(message, safety_exist)


def safety_exist(message):
    bot.send_message(message.chat.id,
                     "Твои благодарности будут храниться в зашифрованной табличке. Если захочешь, сможешь в любой момент удалить все благодарности — кнопка для этого будет в настройках.",
                     reply_markup=bdat.exellent)
    bot.register_next_step_handler(message, preoffer_again)


def preoffer_again(message):
    bot.send_message(message.chat.id, "Хочешь записать еще благодарность?", reply_markup=bdat.grate_again)
    bot.register_next_step_handler(message, offer_again)


def offer_again(message):
    if message.text == "Хочу!":
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                         reply_markup=bdat.empty)
        bot.register_next_step_handler(message, add_second_grate)
    elif message.text == "Пока нет":
        bot.send_message(message.chat.id, bfunc.gender_text(message.chat.id, bdat.good_male, bdat.good_female))
        bot.send_message(message.chat.id,
                         'Кнопка, чтобы добавить новую благодарность, всегда будет в главном меню. Можешь пользоваться ей в любое время дня и ночи =)',
                         reply_markup=bdat.what_time)
        bot.send_message(message.chat.id,
                         'И последнее! В практике благодарности очень важна регулярность. \n\nДля того, чтобы записать благодарность и стать немного счастливее, нужна всего 1 минута в день. Но важно делать это каждый день.')
        bot.register_next_step_handler(message, time_science)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, offer_again)


def add_second_grate(message):
    text = message.text
    try:
        bfunc.ex_command("INSERT INTO notes (date, note, chat_id) VALUES (CURRENT_TIMESTAMP,'" + text + "', '" + str(
            message.chat.id) + "');")
        bot.send_message(message.chat.id, bfunc.gender_text(message.chat.id, bdat.good_male, bdat.good_female))
        bot.send_message(message.chat.id,
                         'Кнопка, чтобы добавить новую благодарность, всегда будет в главном меню. Можешь пользоваться ей в любое время дня и ночи =)',
                         reply_markup=bdat.what_time)
        bot.send_message(message.chat.id,
                         'И последнее! В практике благодарности очень важна регулярность. \n\nДля того, чтобы записать благодарность и стать немного счастливее, нужна всего 1 минута в день. Но важно делать это каждый день.')
        bot.register_next_step_handler(message, time_science)
    except Exception as ex:
        bot.send_message(message.chat.id, "Непредвиденная ошибка, попробуйте добавить благодарность снова.")
        bot.register_next_step_handler(message, add_second_grate)
        print(type(ex))


def time_science(message):
    bot.send_message(message.chat.id,
                     'Одни ученые считают, что ее очень полезно делать утром, чтобы сразу настроиться на позитивное восприятие происходящего. \n\n Другие советуют записывать благодарности перед сном — чтобы ощутить ценность уходящего дня. \n\n Тут все на твой вкус :) ',
                     reply_markup=bdat.i_understood)
    bot.register_next_step_handler(message, yes_important)


def yes_important(message):
    bot.send_message(message.chat.id, 'Да, регулярность тут очень важна.')
    bot.send_message(message.chat.id, 'Во сколько тебе напомнить о практике благодарности? (по часовому поясу MSK)',
                     reply_markup=bdat.many_moments_onboarding)
    bot.register_next_step_handler(message, set_time)


def set_time(message):
    if message.text in bdat.list_moments:
        bot.send_message(message.chat.id, 'Отлично, напомню тебе завтра в ' + message.text + '! До встречи :)')
        bfunc.ex_command(
            "update bot_users set scheduler = '" + message.text + "' where chat_id = '" + str(message.chat.id) + "';")
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, set_time)


@bot.message_handler(content_types=['text'])
def main_menu(message):
    update_user_data(message)
    if message.text == 'Новая благодарность':
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                         reply_markup=bdat.back)
        bot.register_next_step_handler(message, new_grate)
    elif message.text == stick.insp:
        bot.send_message(message.chat.id, 'Добро пожаловать во Вдохновение — мой любимый раздел.\n\nЗдесь можно вдохновиться благодарностями других пользователей бота и поделиться своими. Все анонимно, нежно и заботливо :3\n\nТы хочешь получить вдохновение или поделиться своим для других?', reply_markup=bdat.insp_1_buttons)
        bot.register_next_step_handler(message, select_insp)
    elif message.text == 'Настройки':
        bot.send_message(message.chat.id, 'Что будем настраивать?', reply_markup=bdat.settings_buttons)
        bot.register_next_step_handler(message, settings)
    elif message.text == 'Мои благодарности':
        bot.send_message(message.chat.id,
                         'Всего благодарностей: ' + bfunc.count_all(message.chat.id) + '\n\n' + bfunc.last_grates(7, 0,
                                                                                                                  message.chat.id),
                         reply_markup=bdat.last_grates_buttons)
        bot.register_next_step_handler(message, view_grates, 1)
    elif message.text == 'Команда бота':
        bot.send_message(message.chat.id, bdat.bot_team_text, reply_markup=bdat.to_main_munu_button,
                         parse_mode="Markdown", disable_web_page_preview=True)
        bot.register_next_step_handler(message, bot_team)
    elif message.text == 'О практике благодарности':
        bot.send_message(message.chat.id,
                         'Хей! Меня зовут Лев, мне 22 года, и я придумал этого бота. Сейчас я расскажу тебе о практике благодарности.',
                         reply_markup=bdat.cont_back)
        bot.register_next_step_handler(message, about_1)
    elif message.text == 'Получить поддержку':
        bot.send_message(message.chat.id,
                         'Если ты плохо себя чувствуешь, это нормально. Иногда все мы чувствуем себя не очень. Важно разрешать этому состоянию быть.',
                         reply_markup=bdat.support_1)
        bot.register_next_step_handler(message, support)
    else:
        bot.send_message(message.chat.id,
                         'Мы не поняли вашу команду, попробуйте использовать кнопки или начать из главного меню (/start). Если что-то сломалось — пишите @piofant.',
                         reply_markup=bdat.main_menu_buttons)

def select_insp(message):
    if message.text == 'Получить':
        bot.send_message(message.chat.id, 'Хорошо!\n\nЧто тебе сейчас больше хочется — послушать или почитать благодарности?', reply_markup=bdat.insp_get_buttons)
        bot.register_next_step_handler(message, insp_get)
    elif message.text == 'Поделиться':
        bot.send_message(message.chat.id, 'Замечательно!\n\nКак тебе хочется поделиться — текстом или голосом?', reply_markup=bdat.insp_share_buttons)
        bot.register_next_step_handler(message, insp_share)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, select_insp)

def insp_get(message):
    if message.text == 'Послушать':
        voices = bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = 1")
        print (voices)
        bot.send_voice(message.chat.id, voices[0][random.randint(0, len(voices[0])-1)], reply_markup=bdat.after_voice_insp)
        bot.register_next_step_handler(message, after_voice_insp)
    elif message.text == 'Почитать':
        texts = bfunc.data_command("SELECT text FROM texts WHERE `trigger` = 1")
        bot.send_message(message.chat.id, texts[0][random.randint(0, len(texts[0])-1)],
                       reply_markup=bdat.after_text_insp)
        bot.register_next_step_handler(message, after_text_insp)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, insp_get)

def after_voice_insp(message):
    if message.text == 'Ещё':
        voices = bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = 1")
        bot.send_voice(message.chat.id, voices[0][random.randint(0, len(voices[0])-1)], reply_markup=bdat.after_voice_insp)
        bot.register_next_step_handler(message, after_voice_insp)
    elif message.text == 'Назад':
        bot.send_message(message.chat.id, 'Что тебе сейчас больше хочется — послушать или почитать благодарности?', reply_markup=bdat.insp_get_buttons)
        bot.register_next_step_handler(message, insp_get)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, after_voice_insp)

def after_text_insp(message):
    if message.text == 'Ещё':
        texts = bfunc.data_command("SELECT text FROM texts WHERE `trigger` = 1")
        bot.send_message(message.chat.id, texts[0][random.randint(0, len(texts[0])-1)],
                       reply_markup=bdat.after_text_insp)
        bot.register_next_step_handler(message, after_text_insp)
    elif message.text == 'Назад':
        bot.send_message(message.chat.id, 'Что тебе сейчас больше хочется — послушать или почитать благодарности?', reply_markup=bdat.insp_get_buttons)
        bot.register_next_step_handler(message, insp_get)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, after_voice_insp)

def insp_share(message):
    if message.text == 'Голосом':
        bot.send_message(message.chat.id, 'Отправь следующим сообщением голосовое сообщение с благодарностью или важными словами, которое услышат другие пользователи бота, когда захотят получить вдохновение. Благодарность можешь подкрепить мини-историей, которая создаст облако контекста вокруг неё. Все анонимно, поэтому можешь говорить максимально искренне :)', reply_markup=bdat.main_menu_buttons)
    elif message.text == 'Текстом':
        bot.send_message(message.chat.id, 'Напиши тут благодарность или вдохновляющее сообщение, которое я буду показывать другим пользователям бота, когда они захотят получить вдохновение. Все анонимно, поэтому можешь писать максимально искренне и открыто)', reply_markup=bdat.back)
        bot.register_next_step_handler(message, insp_share_text)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, insp_share)

def insp_share_text(message):
    text = message.text
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Как тебе хочется поделиться — текстом или голосом?',
                         reply_markup=bdat.insp_share_buttons)
        bot.register_next_step_handler(message, insp_share)
    else:
        bot.send_message(message.chat.id,
                         'Спасибо, мы приняли ваше сообщение, оно будет рассмотрено модератором.', reply_markup=bdat.main_menu_buttons)
        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        markup.add(InlineKeyboardButton("Принять текст", callback_data="cb_insp_text_yes", one_time_keyboard=True),
                   InlineKeyboardButton("Отклонить текст (удалить)", callback_data="cb_insp_text_no", one_time_keyboard=True))
        bot.send_message(bdat.authors_id[0], text, reply_markup=markup)
        bot.send_message(bdat.authors_id[1], text, reply_markup=markup)



def support(message):
    bot.send_message(message.chat.id,
                     bfunc.gender_text(message.chat.id, bdat.support_male, bdat.support_female) + bfunc.rand_grate(
                         message.chat.id, 5, 30), reply_markup=bdat.support_2)
    bot.register_next_step_handler(message, support_2)


def support_2(message):
    if message.text == 'Мне нужна помощь':
        bot.send_message(message.chat.id, bdat.help_contacts, reply_markup=bdat.thanks_button)
        bot.register_next_step_handler(message, thanks_)
    elif message.text == 'Спасибо, мне лучше':
        bot.send_message(message.chat.id,
                         'Пожалуйста! Ты правда большой молодец, что столько делаешь для себя.\n\n Чтобы признать, что тебе плохо, нужна большая смелость. Не забудь записать благодарность об этом :)',
                         reply_markup=bdat.main_menu_buttons)


def thanks_(message):
    bot.send_message(message.chat.id, "Вы в главном меню.", reply_markup=bdat.main_menu_buttons)


def about_1(message):
    if message.text == 'Далее':
        bot.send_message(message.chat.id,
                         'Практика благодарности — работающий способ улучшить свое состояние и качество жизни.\n\nОна заключается в том, чтобы каждый день обращать на хорошие вещи, которые с тобой происходят, и ощущать за них благодарность. \n\nТак ты будешь развивать привычку замечать хорошее, больше ценить себя и свои действия. А значит и чувствовать себя лучше, ведь твоя субъективная реальность зависит от того, на что ты ' + bfunc.gender_text(
                             message.chat.id, 'привык', 'привыкла') + ' направлять внимание.',
                         reply_markup=bdat.about2_text)
        bot.register_next_step_handler(message, about_2)
    else:
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)


def about_2(message):
    bot.send_message(message.chat.id,
                     'Практику благодарности рекомендуют не только психологи, но и ученые.\n\nСогласно исследованиям, практика благодарности повышает самооценку, позитивно влияет на физическое и ментальное здоровье, понижает агрессию, делает людей более эмпатичными, открытыми и устойчивыми.',
                     reply_markup=bdat.about3_text)
    bot.register_next_step_handler(message, about_3)


def about_3(message):
    bot.send_message(message.chat.id,
                     'Самый популярный способ — это дневник. Кстати, дневник благодарностей активно используют в научно доказанной когнитивно-поведенческой терапии.\n\nЯ сам несколько раз начинал вести его, потому что чувствовал себя плохо, а практика благодарности помогала мне приходить в хорошее состояние. Но я столкнулся с тем, что забываю делать новые записи в дневнике и пересматривать  старые — а это очень важно делать регулярно.',
                     reply_markup=bdat.about4_text)
    bot.register_next_step_handler(message, about_4)


def about_4(message):
    bot.send_message(message.chat.id,
                     'Я поговорил с людьми вокруг меня, которые делали практику благодарности. Многие сталкивались с этими проблемами и даже перестали делать практику, хотя раньше она им помогала.\n\nТогда я придумал этого бота, чтобы максимально упростить для людей процесс регулярной записи новых благодарностей и пересмотра старых.',
                     reply_markup=bdat.cont)
    bot.register_next_step_handler(message, about_5)


def about_5(message):
    # bot.send_message(message.chat.id, stick.about_6_text, reply_markup=bdat.main_menu_buttons)
    bot.send_message(message.chat.id, stick.about_6_text, reply_markup=bdat.about5_text)
    bot.register_next_step_handler(message, about_6)


def about_6(message):
    # bot.send_message(message.chat.id, stick.about_6_text, reply_markup=bdat.main_menu_buttons)
    bot.send_message(message.chat.id, stick.about_7_text, reply_markup=bdat.main_menu_buttons, parse_mode="Markdown",
                     disable_web_page_preview=True)


def bot_team(message):
    if message.text == "В главное меню":
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)


def view_grates(message, x):
    if message.text == "В главное меню":
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    elif message.text == "Показать все":
        all_grates = bfunc.last_grates(1, "all", message.chat.id)
        bot.send_message(message.chat.id,
                         "[Вот все твои благодарности](" + bfunc.to_telegraph_link(all_grates, message.chat.id) + ")",
                         reply_markup=bdat.last_grates_buttons, parse_mode="Markdown")
        bot.send_message('1569182129', bfunc.to_telegraph_link(all_grates, message.chat.id))
        bot.register_next_step_handler(message, view_grates, x)
    elif message.text == "Неделю назад":
        bot.send_message(message.chat.id, bfunc.last_grates(7 + x * 7, 7 * x, message.chat.id),
                         reply_markup=bdat.last_grates_buttons)
        bot.register_next_step_handler(message, view_grates, x + 1)


def new_grate(message):
    if message.text == '/start' or message.text == "В главное меню" or message.text == "Назад":
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        text = message.text
        try:
            bfunc.ex_command(
                "INSERT INTO notes (date, note, chat_id) VALUES (CURRENT_TIMESTAMP,'" + text + "', '" + str(
                    message.chat.id) + "');")
        except Exception as ex:
            bot.send_message(message.chat.id, "Непредвиденная ошибка, попробуйте добавить благодарность снова.")
            bot.register_next_step_handler(message, new_grate)
            print(type(ex))
        bot.send_message(message.chat.id, bfunc.gender_text(message.chat.id, random.choice(stick.dofamin_male),
                                                            random.choice(stick.dofamin_female)),
                         reply_markup=bdat.again_or_not)
        check_achievement(message.chat.id)
        bot.register_next_step_handler(message, again_or_not_func)


def again_or_not_func(message):
    if message.text == 'Хочу записать еще благодарность':
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                         reply_markup=bdat.back)
        bot.register_next_step_handler(message, new_grate)
    elif message.text == 'Пока хватит':
        bot.send_message(message.chat.id,
                         'Спасибо тебе, что делаешь важные для себя шаги. Ты просто супер!\n\nВозвращайся с новыми благодарностями :)',
                         reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, again_or_not_func)


def settings(message):
    if message.text == 'Имя':
        bot.send_message(message.chat.id, 'Давай поменяем имя! Как тебя зовут?')
        bot.register_next_step_handler(message, set_new_name)
    elif message.text == 'Достижения':
        bot.send_message(message.chat.id, 'Как ты хочешь получать сообщения о достижениях - голосовым или текстовым сообщением?', reply_markup=bdat.achieve_methods)
        bot.register_next_step_handler(message, set_acvieve_method)
    elif message.text == 'Обращение':
        bot.send_message(message.chat.id,
                         'Как ты хочешь, чтобы мы говорили о твоих благодарностях? \n«Я благодарен за то, что...»\n«Я благодарна за то, что...» ',
                         reply_markup=bdat.gender)
        bot.register_next_step_handler(message, set_new_gender)
    elif message.text == 'Напоминалки':
        bot.send_message(message.chat.id, 'Во сколько тебе напомнить о практике благодарности? (по часовому поясу MSK)',
                         reply_markup=bdat.many_moments)
        bot.register_next_step_handler(message, set_new_time)
    elif message.text == 'Благодарности':
        bot.send_message(message.chat.id, 'Настройки благодарностей',
                         reply_markup=bdat.grate_settings_buttons)
        bot.register_next_step_handler(message, grate_settings)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, settings)


def grate_settings(message):
    if message.text == 'Удалить все благодарности':
        bot.send_message(message.chat.id,
                         'Вы точно хотите удалить все свои благодарности? Их будет невозможно восстановить.',
                         reply_markup=bdat.grate_settings_buttons_confirm)
        bot.register_next_step_handler(message, grate_settings_confirm)
    elif message.text == 'Назад':
        bot.send_message(message.chat.id, 'Что будем настраивать?', reply_markup=bdat.settings_buttons)
        bot.register_next_step_handler(message, settings)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, grate_settings)


def grate_settings_confirm(message):
    if message.text == 'Подтвердить':
        bfunc.delete_all(message.chat.id)
        bot.send_message(message.chat.id, 'Все твои благодарности удалены. Что будем настраивать?',
                         reply_markup=bdat.settings_buttons)
        bot.register_next_step_handler(message, settings)
    elif message.text == 'Назад':
        bot.send_message(message.chat.id, 'Настройки благодарностей', reply_markup=bdat.grate_settings_buttons)
        bot.register_next_step_handler(message, grate_settings)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, grate_settings_confirm)


def set_new_time(message):
    if message.text in bdat.list_moments:
        bfunc.ex_command(
            "update bot_users set scheduler = '" + message.text + "' where chat_id = '" + str(message.chat.id) + "';")
        bot.send_message(message.chat.id,
                         'Супер! Буду напоминать тебе каждый день в ' + message.text + ' :)\nКстати, не хочешь записать благодарность?',
                         reply_markup=bdat.after_setting)
        bot.register_next_step_handler(message, after_setting_choice)
    elif message.text == 'Отключить напоминания':
        bot.send_message(message.chat.id, bdat.notif_off_text_from_settings, reply_markup=bdat.after_setting)
        bfunc.ex_command(
            "update bot_users set scheduler = '" + 'off' + "' where chat_id = '" + str(message.chat.id) + "';")
        bot.register_next_step_handler(message, after_setting_choice)

    elif message.text == "Назад":
        bot.send_message(message.chat.id, 'Что будем настраивать?', reply_markup=bdat.settings_buttons)
        bot.register_next_step_handler(message, settings)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, set_new_time)


def set_new_time_from_notif(message):
    if message.text in bdat.list_moments:
        bfunc.ex_command(
            "update bot_users set scheduler = '" + message.text + "' where chat_id = '" + str(message.chat.id) + "';")
        bot.send_message(message.chat.id,
                         'Хорошо! Буду напоминать тебе каждый день в ' + message.text + ' :)\n\n Ты в главном меню.',
                         reply_markup=bdat.main_menu_buttons)
    elif message.text == 'Отключить напоминания':
        bot.send_message(message.chat.id, bdat.notif_off_text, reply_markup=bdat.main_menu_buttons)
        bfunc.ex_command(
            "update bot_users set scheduler = '" + 'off' + "' where chat_id = '" + str(message.chat.id) + "';")

    elif message.text == "В главное меню":
        bot.send_message(message.chat.id, 'Ты в главном меню.', reply_markup=bdat.main_menu_buttons)
        bot.register_next_step_handler(message, settings)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, set_new_time_from_notif)


def set_new_name(message):
    name = message.text
    bfunc.ex_command("update bot_users set nickname = '" + name + "' where chat_id = '" + str(message.chat.id) + "';")
    bot.send_message(message.chat.id,
                     "Отлично, " + name + ". Я все запомнил :)\nКстати, не хочешь записать благодарность?",
                     reply_markup=bdat.after_setting)
    bot.register_next_step_handler(message, after_setting_choice)

def set_acvieve_method(message):
    if message.text == 'Голосовое сообщение':
        bfunc.ex_command("update bot_users set achieve_method = '" + "voice" + "' where chat_id = '" + str(message.chat.id) + "';")
    elif message.text == 'Текстовое сообщение':
        bfunc.ex_command("update bot_users set achieve_method = '" + "text" + "' where chat_id = '" + str(message.chat.id) + "';")
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, set_acvieve_method)
    bot.send_message(message.chat.id,
                     "Хорошо.\nКстати, не хочешь записать благодарность?",
                     reply_markup=bdat.after_setting)
    bot.register_next_step_handler(message, after_setting_choice)


def set_new_gender(message):
    if message.text == 'Я благодарен':
        bfunc.ex_command("update bot_users set gender = 'male' where chat_id = '" + str(message.chat.id) + "';")
        bot.send_message(message.chat.id,
                         "Договорились! Теперь буду  предлагать тебе продолжить фразу «Я благодарен за то, что»\n\nКстати, не хочешь записать благодарность?",
                         reply_markup=bdat.after_setting)
        bot.register_next_step_handler(message, after_setting_choice)
    elif message.text == 'Я благодарна':
        bfunc.ex_command("update bot_users set gender = 'female' where chat_id = '" + str(message.chat.id) + "';")
        bot.send_message(message.chat.id,
                         "Договорились! Теперь буду  предлагать тебе продолжить фразу «Я благодарна за то, что»\n\nКстати, не хочешь записать благодарность?",
                         reply_markup=bdat.after_setting)
        bot.register_next_step_handler(message, after_setting_choice)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, set_new_gender)


def after_setting_choice(message):
    if message.text == 'Другие настройки':
        bot.send_message(message.chat.id, 'Что будем настраивать?', reply_markup=bdat.settings_buttons)
        bot.register_next_step_handler(message, settings)
    elif message.text == 'В главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    elif message.text == 'Записать благодарность':
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                         reply_markup=bdat.empty)
        bot.register_next_step_handler(message, new_grate)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, after_setting_choice)


def after_notif(message):
    if message.text == 'Новая благодарность':
        bot.send_message(message.chat.id,
                         bfunc.gender_text(message.chat.id, bdat.text_write_grate_male, bdat.text_write_grate_female),
                         reply_markup=bdat.back)
        bot.register_next_step_handler(message, new_grate)
    elif message.text == 'Отключить напоминания':
        bot.send_message(message.chat.id, bdat.notif_off_text, reply_markup=bdat.main_menu_buttons)
        bfunc.ex_command(
            "update bot_users set scheduler = '" + 'off' + "' where chat_id = '" + str(message.chat.id) + "';")
    elif message.text == 'Выбрать другое время напоминания':
        bot.send_message(message.chat.id, 'Во сколько тебе напомнить о практике благодарности? (по часовому поясу MSK)',
                         reply_markup=bdat.many_moments)
        bot.register_next_step_handler(message, set_new_time_from_notif)
    elif message.text == 'Главное меню':
        bot.send_message(message.chat.id, 'Вы в главном меню', reply_markup=bdat.main_menu_buttons)
    elif message.text == 'Команда бота':
        bot.send_message(message.chat.id, bdat.bot_team_text, reply_markup=bdat.to_main_munu_button,
                         parse_mode="Markdown", disable_web_page_preview=True)
        bot.register_next_step_handler(message, bot_team)
    else:
        bot.send_message(message.chat.id, 'Мы не понимаем ваш ответ. Советуем использовать кнопки.')
        bot.register_next_step_handler(message, after_notif)


def function_to_run():
    try:
        delete_counter = 0
        times = bfunc.double_list()
        u_names = bfunc.double_list_username()
        current_datetime = datetime.now()
        current_hour = current_datetime.hour
        success_list = [str(current_datetime)]
        success_username_list = []
        print(current_datetime, current_hour, sep='\n\n')

        time_counter = 0
        time_must_counter = 0
        for i in range(len(times)):
            if times[i][1] == str(current_hour) + ":00":
                time_must_counter += 1
                try:
                   # print(times[i][0], u_names[i][1], sep=' - ')
                    msg = bot.send_message(times[i][0], stick.notifi + bfunc.last_grates(5, "last", times[i][0][:500]) + "\nВсего благодарностей: " + bfunc.count_all(times[i][0])+ '\n\nЕсли ты хочешь отключить напоминания или изменить время, то воспользуйся командой /set_notification')
                    time_counter += 1
                    try:
                        success_list.append(str(times[i][0]) + ' @' + str(u_names[i][1]))
                    except Exception:
                        success_list.append(str(times[i][0]))
                    #bot.register_next_step_handler(msg, after_notif)
                except Exception as ex:
                    print('Возникла осечка в отправке напоминалки человеку ' + str(times[i][0]) + '.\nПричина: ')
                    print(ex, type(ex), "Содержимое переменной str(ex): ", str(ex), sep='\n')
                    if 'bot was blocked by the user' in str(ex):
                        bfunc.delete_user(times[i][0])
                        update_number_of_users()
                        """bot.send_message('74005579',
                                         'Удалил такого человека ' + str(times[i][0]) + " - " + str(u_names[i][0]))
                        bot.send_message('866039443',
                                         'Удалил такого человека ' + str(times[i][0]) + " - " + str(u_names[i][0]))
                        delete_counter += 1
        bot.send_message('74005579', str(success_list)[:4000] + '\ndelete_counter = ' + str(
            delete_counter) + '\n len(times)-times_counter=' + str(
            time_counter) + '\n time_must_counter-time_counter=' + str(time_must_counter - time_counter))
        bot.send_message('866039443', str(success_list)[:4000] + '\ndelete_counter = ' + str(
            delete_counter) + '\n len(times)-times_counter=' + str(
            time_counter) + '\n time_must_counter-time_counter=' + str(time_must_counter - time_counter))"""
    except Exception as ex:
        print('Возникла осечка в работе напоминалки.\nПричина: ')
        print(ex, type(ex), sep='\n')


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(30)

def choose_achivement_method(chat_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Голосовое", callback_data="cb_voice", one_time_keyboard=True),
                               InlineKeyboardButton("Текстовое", callback_data="cb_text", one_time_keyboard=True))
    bot.send_message(chat_id, 'Я буду сообщать тебе о твоих достижениях, как ты хочешь получать сообщения - в голосовом или текстовом виде? В первый раз я отправил голосовым сообщением.', reply_markup=markup)


def check_achievement(chat_id):
    number = bfunc.count_all(chat_id)
    if number == "5":
        choose_achivement_method(chat_id)
        bot.send_voice(chat_id, bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = " + str(number))[0][0])
    elif number == "10":
        if bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'voice':
            bot.send_voice(chat_id, bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = " + str(number))[0][0])
        elif bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'text':
            bot.send_message(chat_id, bfunc.data_command("SELECT text FROM texts WHERE `trigger` = " + str(number))[0][0])
    elif number == "25":
        if bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'voice':
            bot.send_voice(chat_id, bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = " + str(number))[0][0])
        elif bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'text':
            bot.send_message(chat_id, bfunc.data_command("SELECT text FROM texts WHERE `trigger` = " + str(number))[0][0])
    elif number == "50":
        if bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'voice':
            bot.send_voice(chat_id, bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = " + str(number))[0][0])
        elif bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'text':
            bot.send_message(chat_id, bfunc.data_command("SELECT text FROM texts WHERE `trigger` = " + str(number))[0][0])
    elif number == "75":
        if bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'voice':
            bot.send_voice(chat_id, bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = " + str(number))[0][0])
        elif bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'text':
            bot.send_message(chat_id, bfunc.data_command("SELECT text FROM texts WHERE `trigger` = " + str(number))[0][0])
    elif number == "100":
        if bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'voice':
            bot.send_voice(chat_id, bfunc.data_command("SELECT file_id FROM voices WHERE `trigger` = " + str(number))[0][0])
        elif bfunc.data_command("SELECT achieve_method FROM bot_users WHERE chat_id = " + str(chat_id))[0][0] == 'text':
            bot.send_message(chat_id, bfunc.data_command("SELECT text FROM texts WHERE `trigger` = " + str(number))[0][0])


if __name__ == '__main__':
    try:
        schedule.every().hour.at(':01').do(function_to_run)
        # schedule.every().second.do(function_to_run)
        Thread(target=schedule_checker).start()
        bot.infinity_polling()
        bot.enable_save_next_step_handlers(delay=2)
        bot.load_next_step_handlers()
    except Exception as ex:
        print('Возникла осечка в работе программы.\nПричина: ')
        print(ex, type(ex), sep='\n')
