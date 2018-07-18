from telebot import types
from threading import Timer
import telebot
import time
import math
import config
import sqlite3
import re

user_plus = ('creator', 'administrator')
bot = telebot.TeleBot(config.TOKEN)
conn = sqlite3.connect('warn.db', check_same_thread=False)

wrong_syntax = 'Неверный синтаксис команды: '
text_messages = {
    'welcome': (
        'Приветствуем, <a href="tg://user?id='
        '{}> {} </a>, в нашем чате! " + {}'
    ),
    'admin_required': (
        'Я должен быть администратором. '
        'Иначе мой функционал работать не будет!'
    ),
    'wrong_pin_syntax': (
        wrong_syntax +
        'Нужно ответить командой /pin на нужное сообщение.'
    ),
    'wrong_sd_syntax': (
        wrong_syntax +
        'Нужно отправить команду /sd text - где text Ваше сообщение.'
    ),
    'wrong_sd_ch_syntax': (
        wrong_syntax +
        'Нужно ответить командой /sd_ch на нужное сообщение '
        'или через пробел написать текст для отправки.'
    ),
    'wrong_warn_syntax': (
        wrong_syntax +
        'Нужно ответить командой /warn на нужное сообщение.'
    ),
    'wrong_unwarn_syntax': (
        wrong_syntax +
        'Нужно ответить командой /unwarn на нужное сообщение '
        'и указать количество варнов, которые Вы хотите снять.'
    ),
    'wrong_iau_sytax': (
        wrong_syntax +
        'Нужно ответить командой /iau на сообщение '
        'пользователя о котором хотете узнать информацию.'
    ),
    'wrong_warn_settings_syntax': (
        wrong_syntax +
        'Нужно отправить команду /warn_settings 3 7200 - где 3 - '
        'максимум предупреждений перед мутом(меньше 2 нельзя), '
        '7200 - время мута после лимита предупреждений.'
    ),
    'wrong_black_words_syntax': (
        wrong_syntax +
        'Нужно отправить команду /black_words слово,слово,слово - '
        'где "слово" запрещенное слово. ВАЖНО: пробелы имеют значение'
    ),
    'wrong_com_is_allow_sytax': (
        wrong_syntax +
        'Нужно отправить команду /com_is_allow значение '
        '- где допустимые значения True или False. По-умолчанию False'
    ),
    'wrong_auto_warn_syntax':
    (
        wrong_syntax +
        'Нужно отправить команду /auto_warn значение - '
        'где допустимые значения True или False. По-умолчанию True'
    ),
    'wrong_notif_range_syntax': (
        wrong_syntax +
        'Нужно отправить команду /notif_range значение - '
        'где допустимые значения от 1 и больше, если 0 - '
        'функция считается отключенной. По умолчанию отключена'
    ),
    'wrong_notif_mess_syntax': (
        wrong_syntax +
        'Нужно отправить команду /notif_mess ... - где ... '
        'текст, который будет отправляться в чат с переодичностью '
        'заданной команде /notif_range.'
    ),
    'wrong_welcome_mes_syntax': (
        wrong_syntax +
        'Нужно отправить команду /welcome_mes ... '
        '- где ... текст, который будет отправляться '
        'при вступлении пользователя в чат. '
        'Для отключения передайте текст dis'
    ),
    'wrong_ban_syntax': (
        wrong_syntax +
        'Нужно ответить командой /ban на нужное сообщение '
        'и указать время бана, если время не указано - бан навсегда.'
    ),
    'wrong_mute_syntax': (
        wrong_syntax +
        '/mute кол-во_минут.'
    ),
    'wrong_unmute_syntax': (
        wrong_syntax +
        'нужно ответить /unmute на сообщения юзера, которого нужно размутить.'
    ),
    'chat_settings': (
        'Настройки чата:'
        '1) Максимальное кол-во предупреждений:_ *{0}*'
        '2) Время мута после получение макс. кол-ва предупреждений:_*{1}* мин.'
        '3) Команды ботам:_ *{2}*'
        '4) Автоматические предупреждения:_ *{3}*'
        '5) Циклические рассылки:_ *{4}*'
    ),
    'chat_settings_updated': 'Настройки чата успешно обновлены.',
    'unable_to_warn_admin': 'Невозможно выдать предупреждение админу.',

}


def check(message, user_id=0):
    u_id = message.from_user.id if not user_id else user_id
    if bot.get_chat_member(message.chat.id, u_id).status in user_plus:
        return True


@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    c = conn.cursor()
    c.execute(
        'SELECT welcome_mes FROM settings WHERE chat_id=?',
        (message.chat.id,)
    )
    welcome_m = c.fetchone()
    sent_m = 0
    if welcome_m is not None \
            and not message.new_chat_member.id == config.bot_id:
        if not isinstance(welcome_m[0], type(None))\
                or not welcome_m[0] == 'dis':
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['welcome'].format(
                    str(message.new_chat_member.id),
                    message.new_chat_member.first_name,
                    welcome_m[0]
                ),
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    elif message.new_chat_member.id == config.bot_id:
        sent_m = bot.send_message(
            message.chat.id,
            text_messages['admin_required']
        )
        c.execute('SELECT id FROM settings WHERE chat_id=?',
                  (message.chat.id,))
        db_id = c.fetchone()
        if db_id:
            c.execute('UPDATE settings SET last_mess = ? WHERE chat_id = ?',
                      (message.message_id, message.chat.id))
        else:
            c.execute(
                'INSERT INTO settings (chat_id, last_mess) VALUES (?, ?)',
                (message.chat.id, message.message_id)
            )
    conn.commit()
    if sent_m:
        Timer(60.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()
    c.close()


@bot.message_handler(commands=['pin', 'Pin'])
def pin(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            bot.pin_chat_message(
                message.chat.id,
                message.reply_to_message.message_id,
                disable_notification=True
            )
        except AttributeError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_pin_syntax']
            )
            Timer(10.0, bot.delete_message, args=[
                  sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['sd', 'Sd'])
def sd(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            bot.send_message(message.chat.id, ' '.join(
                message.text.split()[1:]))
        except telebot.apihelper.ApiException:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_sd_syntax']
            )
            Timer(10.0, bot.delete_message, args=[
                  sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['sd_ch', 'Sd_ch'])
def sd_ch(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin and message.from_user.id == config.my_id:
        try:
            text = \
                message.reply_to_message.text \
                if message.reply_to_message is not None \
                else ' '.join(
                    message.text.split()[1:]
                )
            bot.send_message('@pylearn_channel', text)
            bot.send_message(
                message.chat.id,
                "Cообщение успешно отправлено в канал t.me/pylearn_channel",
                disable_web_page_preview=True
            )
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_sd_ch_syntax']
            )
            Timer(10.0, bot.delete_message, args=[
                  sent_m.chat.id, sent_m.message_id]).start()


def warn_do(message, warn):
    c = conn.cursor()
    test = c.execute(
        '''SELECT chat_id, user_id, warn_count
        FROM warn
        WHERE chat_id=? AND user_id=?''',
        warn[:2]
    ).fetchone()
    name = warn[2] if len(warn) == 4 else warn[2]
    if test is None:
        c.execute(
            '''INSERT INTO warn
            (chat_id, user_id, warn_count) VALUES (?, ?, 1)''',
            warn[:2]
        )
        text = 'Количество предупреждений \
[{0}](tg://user?id={1}) увеличено до - 1.'.format(
            name, warn[1]
        )
        bot.send_message(message.chat.id, parse_mode='markdown', text=text)
    else:
        c.execute(
            '''UPDATE warn
            SET warn_count = warn_count + 1
            WHERE chat_id=? AND user_id=?''',
            warn[:2]
        )
        c.execute(
            '''SELECT warn_count
            FROM warn
            WHERE chat_id=? AND user_id=?''',
            warn[:2]
        )
        warn_count = c.fetchone()[0]
        c.execute(
            '''SELECT max_warn, time_ban
            FROM settings
            WHERE chat_id=?''',
            (message.chat.id,)
        )
        data = c.fetchone()
        max_warn, time_ban = data[0], data[1]
        text = 'Количество предупреждений \
[{0}](tg://user?id={1}) увеличено до - {2}.'.format(
            name, warn[1], warn_count
        )
        bot.send_message(message.chat.id, parse_mode='markdown', text=text)
        if warn_count >= max_warn:
            until = math.floor(time.time()) + time_ban * 60
            bot.restrict_chat_member(
                message.chat.id, warn[1], until_date=until,
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
            bot.send_message(
                message.chat.id,
                '[{0}](tg://user?id={1}) заблокирован на {2} мин.'.format(
                    name, warn[1], time_ban
                ),
                parse_mode='markdown')
            c.execute(
                'DELETE FROM warn WHERE chat_id=? AND user_id=?', warn[:2])
    conn.commit()
    c.close()


@bot.message_handler(commands=['warn', 'Warn'])
def warn(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            warn = (
                message.chat.id,
                message.reply_to_message.from_user.id,
                message.reply_to_message.from_user.first_name,
                message.reply_to_message.from_user.is_bot
            )
        except AttributeError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_warn_syntax']
            )
        else:
            if check(message, message.reply_to_message.from_user.id):
                sent_m = bot.send_message(
                    message.chat.id,
                    text_messages['unable_to_warn_admin']
                )
            else:
                bot.delete_message(
                    message.chat.id, message.reply_to_message.message_id)
                warn_do(message, warn)
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['unwarn', 'Unwarn'])
def unwarn(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            warn_c = (
                message.text.split()[1],
                message.chat.id,
                message.reply_to_message.from_user.id
            )
            c = conn.cursor()
            c.execute(
                '''UPDATE warn
                SET warn_count=warn_count - ?
                WHERE chat_id = ? AND user_id = ?''',
                warn_c
            )
            c.execute(
                '''SELECT warn_count
                FROM warn WHERE chat_id=? AND user_id=?''',
                warn_c[1:]
            )
            warn = c.fetchone()
            if warn[0] <= 0:
                c.execute(
                    '''DELETE FROM warn
                    WHERE chat_id=? AND user_id=?''',
                    warn_c[1:]
                )
                sent_m = bot.send_message(
                    message.chat.id,
                    '[{0}](tg://user?id={1}) больше не имеет предупреждений.'
                    .format(
                        message.reply_to_message.from_user.first_name,
                        message.reply_to_message.from_user.id
                    ),
                    parse_mode='markdown')
            else:
                sent_m = bot.send_message(
                    message.chat.id,
                    'Количество предупреждений \
[{0}](tg://user?id={1}) уменьшено до - {2}.'
                    .format(
                        message.reply_to_message.from_user.first_name,
                        message.reply_to_message.from_user.id, warn[0]
                    ),
                    parse_mode='markdown')
            conn.commit()
            c.close()
        except (IndexError, TypeError, AttributeError):
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_unwarn_syntax']
            )
        Timer(25.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['iau', 'Iau'])
def info_about_user(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            user_info = (message.chat.id,
                         message.reply_to_message.from_user.id)
        except AttributeError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_iau_sytax']
            )
        else:
            c = conn.cursor()
            c.execute(
                '''SELECT warn_count
                FROM warn WHERE chat_id=? AND user_id=?''',
                user_info
            )
            warn_count = c.fetchone()
            if warn_count:
                sent_m = bot.send_message(
                    message.chat.id,
                    '[{0}](tg://user?id={1}) имеет \
количество предупреждений - {2}.'
                    .format(
                        message.reply_to_message.from_user.first_name,
                        message.reply_to_message.from_user.id,
                        warn_count[0]
                    ),
                    parse_mode='markdown')
            else:
                sent_m = bot.send_message(
                    message.chat.id,
                    '[{0}](tg://user?id={1}) не имеет предупреждений.'
                    .format(
                        message.reply_to_message.from_user.first_name,
                        message.reply_to_message.from_user.id),
                    parse_mode='markdown'
                )
            c.close()
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['info_about_chat', 'Info_about_chat'])
def info_about_chat(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        c = conn.cursor()
        c.execute(
            ''''SELECT max_warn, time_ban,
            com_is_allow, auto_warn, notif_range
            FROM settings
            WHERE chat_id = ?''',
            (message.chat.id,)
        )
        info = list(c.fetchone())
        info[2] = 'Разрешены' if info[2] == 'True' else 'Запрещены'
        info[3] = 'Включены' if info[3] == 'True' else 'Отключены'
        info[4] = info[4] if info[4] else 'Отключены'
        sent_m = bot.send_message(
            message.chat.id,
            text_messages['chat_settings']
            .format(
                info[0],
                info[1],
                info[2],
                info[3],
                info[4]
            ),
            parse_mode='markdown')
        c.close()
        Timer(45.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['warn_settings', 'Warn_settings'])
def warn_settings(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            settings = (message.text.split()[1:], message.chat.id)
            if int(settings[0][0]) <= 1 or int(settings[0][1]) < 1:
                raise IndexError
            c = conn.cursor()
            c.execute(
                '''UPDATE settings
                SET max_warn = ?, time_ban = ?
                WHERE chat_id = ?''',
                (settings[0][0], settings[0][1], settings[1])
            )
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['chat_settings_updated']
            )
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_warn_settings_syntax']
            )
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['black_words', 'Black_words'])
def black_words(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            settings = (message.text.split()[1], message.chat.id)
            if ',' not in settings[0] or ' ' in settings[0]:
                raise IndexError
            c = conn.cursor()
            c.execute('UPDATE settings SET mat_lst = ? WHERE chat_id = ?',
                      (settings[0], settings[1]))
            sent_m = bot.send_message(
                message.chat.id, text_messages['chat_settings_updated'])
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_black_words_syntax']
            )
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['com_is_allow', 'Com_is_allow'])
def com_is_allow(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            settings = (message.text.split()[1], message.chat.id)
            if settings[0] not in ('False', 'True'):
                raise IndexError
            c = conn.cursor()
            c.execute('UPDATE settings SET com_is_allow = ? WHERE chat_id = ?',
                      (settings[0], settings[1]))
            sent_m = bot.send_message(
                message.chat.id, text_messages['chat_settings_updated'])
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_com_is_allow_sytax']
            )
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['auto_warn', 'Auto_warn'])
def auto_warn(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            settings = (message.text.split()[1], message.chat.id)
            if settings[0] not in ('False', 'True'):
                raise IndexError
            c = conn.cursor()
            c.execute('UPDATE settings SET auto_warn = ? WHERE chat_id = ?',
                      (settings[0], settings[1]))
            sent_m = bot.send_message(
                message.chat.id, text_messages['chat_settings_updated'])
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_auto_warn_syntax']
            )
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['notif_range', 'Notif_range'])
def notif_range(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            settings = (message.text.split()[1], message.chat.id)
            if not isinstance(settings[0], str):
                raise IndexError
            c = conn.cursor()
            c.execute('UPDATE settings SET notif_range = ? WHERE chat_id = ?',
                      (settings[0], settings[1]))
            sent_m = bot.send_message(
                message.chat.id, text_messages['chat_settings_updated'])
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_notif_range_syntax']
            )
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['notif_mess', 'Notif_mess'])
def notif_mess(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            if ' ' not in message.text:
                raise IndexError
            settings = (message.text[12:], message.chat.id)
            c = conn.cursor()
            c.execute('UPDATE settings SET notif_mess = ? WHERE chat_id = ?',
                      (settings[0], settings[1]))
            sent_m = bot.send_message(
                message.chat.id, text_messages['chat_settings_updated'])
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_notif_mess_syntax']
            )
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['welcome_mes', 'Welcome_mes'])
def welcome_mess(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            if ' ' not in message.text:
                raise IndexError
            settings = (message.text[13:], message.chat.id)
            c = conn.cursor()
            c.execute('UPDATE settings SET welcome_mes = ? WHERE chat_id = ?',
                      (settings[0], settings[1]))
            sent_m = bot.send_message(
                message.chat.id, text_messages['chat_settings_updated'])
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_welcome_mes_syntax']

            )
        Timer(15.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['ban', 'Ban'])
def ban(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            name = message.reply_to_message.from_user.first_name
            try:
                until = math.floor(time.time()) + int(message.text[5:]) * 60
            except ValueError:
                bot.kick_chat_member(
                    message.chat.id,
                    message.reply_to_message.from_user.id,
                    until_date=10
                )
                sent_m = bot.send_message(
                    message.chat.id,
                    '[{0}](tg://user?id={1}) забанен навсегда'
                    .format(
                        name,
                        message.reply_to_message.from_user.id
                    ),
                    parse_mode='markdown'
                )
            else:
                bot.kick_chat_member(
                    message.chat.id,
                    message.reply_to_message.from_user.id,
                    until_date=until
                )
                sent_m = bot.send_message(
                    message.chat.id,
                    '[{0}](tg://user?id={1}) забанен на {2} мин.'
                    .format(
                        name,
                        message.reply_to_message.from_user.id,
                        message.text[5:]
                    ),
                    parse_mode='markdown'
                )
        except (AttributeError, ValueError):
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_ban_syntax']

            )
        Timer(25.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['mute', 'Mute'])
def mute(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            until = math.floor(time.time()) + int(message.text.split()[1]) * 60
            bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                until_date=until,
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
            text = '[{0}](tg://user?id={1}) замутен на {2} мин.'\
                .format(
                    message.reply_to_message.from_user.first_name,
                    message.reply_to_message.from_user.id,
                    int(message.text.split()[1])
                )
            sent_m = bot.send_message(
                message.chat.id, parse_mode='markdown', text=text)
        except (AttributeError, IndexError, ValueError):
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_mute_syntax']
            )
        Timer(25.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


@bot.message_handler(commands=['unmute', 'Unmute'])
def unmute(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            bot.restrict_chat_member(
                message.chat.id,
                message.reply_to_message.from_user.id,
                until_date=None,
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
            text = '[{0}](tg://user?id={1}) разблокирован.'\
                .format(
                    message.reply_to_message.from_user.first_name,
                    message.reply_to_message.from_user.id
                )
            sent_m = bot.send_message(
                message.chat.id, parse_mode='markdown', text=text)
        except AttributeError:
            sent_m = bot.send_message(
                message.chat.id,
                text_messages['wrong_unmute_syntax']
            )
        Timer(25.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()


def check_command(message):
    c = conn.cursor()
    notif = c.execute(
        '''SELECT notif_range, last_mess, notif_mess
        FROM settings
        WHERE chat_id=?''',
        (message.chat.id,)
    ).fetchone()
    if notif and not notif[0] is None:     # Функция циклических напоминаний
        if not notif[0]:
            pass
        elif message.message_id - notif[1] >= notif[0] + 1:
            bot.send_message(
                message.chat.id, notif[2], disable_web_page_preview=True)
            c.execute('UPDATE settings SET last_mess = ? WHERE chat_id = ?',
                      (message.message_id, message.chat.id))
    command_is_allowed = c.execute(
        '''SELECT com_is_allow
        FROM settings
        WHERE chat_id=?''',
        (message.chat.id,)
    ).fetchone()
    conn.commit()
    c.close()
    # Функция запрета сообщений начинающих с /(тоесть команд ботам)
    if message.text is not None:
        try:
            if command_is_allowed[0] == 'True':
                return False
            elif message.text.startswith('/') and not check(message):
                return True
        except TypeError:
            pass


@bot.message_handler(func=check_command)
def del_command(message):
    bot.delete_message(message.chat.id, message.message_id)


def check_mat(message):
    if message.text is not None:
        c = conn.cursor()
        c.execute(
            '''SELECT mat_lst, auto_warn
            FROM settings
            WHERE chat_id = ?''',
            (message.chat.id,)
        )
        res = c.fetchone()
        c.close()
        try:
            if res[1] == 'False':
                return False
            mes = \
                frozenset(
                    re.findall(
                        r'\w+', message.text.lower())
                ) & \
                frozenset(
                    res[0].split(',')
                )
        except (AttributeError, TypeError):
            pass
        else:
            mes = frozenset(re.findall(r'\w+', message.text.lower())
                            ) & frozenset(res[0].split(','))
            return True if mes else False


@bot.message_handler(func=check_mat)
def del_mat(message):
    bot.delete_message(message.chat.id, message.message_id)
    warn = (message.chat.id, message.from_user.id,
            message.from_user.first_name)
    if check(message):
        sent_m = bot.send_message(
            message.chat.id, text_messages['unable_to_warn_admin'])
        Timer(10.0, bot.delete_message, args=[
              sent_m.chat.id, sent_m.message_id]).start()
    else:
        warn_do(message, warn)


if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            bot.send_message(config.debug_chat, e)
h