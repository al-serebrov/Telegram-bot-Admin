from telebot import types
import telebot
import time
import math
import config
import sqlite3
import re
import os

user_plus = ('creator', 'administrator')
my_id = config.my_id

bot = telebot.TeleBot(config.TOKEN)
conn = sqlite3.connect('warn.db', check_same_thread=False)

def check(message):
    if bot.get_chat_member(message.chat.id, message.from_user.id).status in user_plus:
        return True

@bot.message_handler(commands=['pin', 'Pin'])
def pin(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id, disable_notification=True)
        except AttributeError:
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /pin на нужное сообщение')

@bot.message_handler(commands=['sd', 'Sd'])
def sd(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        bot.send_message(message.chat.id, message.text[3:])

@bot.message_handler(commands=['sd_ch', 'Sd_ch'])
def sd_ch(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin and message.from_user.id == my_id:
        text = message.reply_to_message.text if not message.reply_to_message is None else message.text[6:]
        bot.send_message('@pylearn_channel', text)
        bot.send_message(message.chat.id, "Cообщение успешно отправлено в канал t.me/pylearn_channel", disable_web_page_preview=True)

def warn_do(message, warn):
    c = conn.cursor()
    test = c.execute('SELECT chat_id, user_id, warn_count FROM warn WHERE chat_id=? AND user_id=?', warn[:2]).fetchone()
    name = message.reply_to_message.from_user.first_name if message.reply_to_message else warn[2]
    if test is None:
        c.execute('INSERT INTO warn (chat_id, user_id, warn_count) VALUES (?, ?, 1)', warn[:2])
        text = 'Количество предупреждений <b>{0}</b> - 1.'.format(name)
        bot.send_message(message.chat.id, parse_mode='HTML', text=text)
    else:
        c.execute('UPDATE warn SET warn_count = warn_count + 1 WHERE chat_id=? AND user_id=?', warn[:2])
        c.execute('SELECT warn_count FROM warn WHERE chat_id=? AND user_id=?', warn[:2])
        warn_count = c.fetchone()[0]
        c.execute('SELECT max_warn, time_ban FROM settings WHERE chat_id=?', (message.chat.id,))
        data = c.fetchone()
        max_warn, time_ban = data[0], data[1]
        text = 'Количество предупреждений <b>{0}</b> - {1}.'.format(name, warn_count)
        bot.send_message(message.chat.id, parse_mode='HTML', text=text)
        if warn_count >= max_warn:
            until = math.floor(time.time()) + time_ban * 60
            bot.restrict_chat_member(message.chat.id, warn[1], until_date=until, 
                                    can_send_messages= False, 
                                    can_send_media_messages=False, 
                                    can_send_other_messages=False,
                                    can_add_web_page_previews=False)
            bot.send_message(message.chat.id, '<b>{0}</b> забанен на {1} мин.'.format(name, time_ban), parse_mode='HTML')
            c.execute('DELETE FROM warn WHERE chat_id=? AND user_id=?', warn[:2])
    conn.commit()
    c.close()

@bot.message_handler(commands=['warn', 'Warn'])
def warn(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            warn = (message.chat.id, message.reply_to_message.from_user.id)
        except AttributeError:
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /warn на нужное сообщение')
        else:
            if check(message):
                bot.send_message(message.chat.id, 'Невозможно выдать предупреждение админу')
            else:
                warn_do(message, warn)

@bot.message_handler(commands=['unwarn', 'Unwarn'])
def unwarn(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            warn_c = (message.text.split()[1], message.chat.id, message.reply_to_message.from_user.id)
        except IndexError:
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /unwarn на нужное сообщение и указать количество варнов, которые Вы хотите снять')
        else:
            c = conn.cursor()
            c.execute('UPDATE warn SET warn_count=warn_count - ? WHERE chat_id = ? AND user_id = ?', warn_c)
            c.execute('SELECT warn_count FROM warn WHERE chat_id=? AND user_id=?', warn_c[1:])
            warn = c.fetchone()
            if warn[0] <= 0:
                c.execute('DELETE FROM warn WHERE chat_id=? AND user_id=?', warn_c[1:])
                bot.send_message(message.chat.id, '<b>{0}</b> больше не имеет предупреждений.'.format(message.reply_to_message.from_user.first_name), parse_mode='HTML')
            else:
                bot.send_message(message.chat.id, 'Количество предупреждений <b>{0}</b> уменьшено до - {1}.'.format(message.reply_to_message.from_user.first_name, warn[0]), parse_mode='HTML')
            conn.commit()
            c.close()

@bot.message_handler(commands=['iau', 'Iau'])
def info_about_user(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            user_info = (message.chat.id, message.reply_to_message.from_user.id)
        except AttributeError:
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /iau на сообщение пользователя о котором хотете узнать информацию')
        else:
            c = conn.cursor()
            c.execute('SELECT warn_count FROM warn WHERE chat_id=? AND user_id=?', user_info)
            warn_count = c.fetchone()
            if warn_count:
                bot.send_message(message.chat.id, '<b>{0}</b> имеет количество предупреждений - {1}.'.format(message.reply_to_message.from_user.first_name, warn_count[0]), parse_mode='HTML')
            else:
                bot.send_message(message.chat.id, '<b>{0}</b> не имеет предупреждений.'.format(message.reply_to_message.from_user.first_name), parse_mode='HTML')
            conn.commit()
            c.close()

@bot.message_handler(commands=['set_settings', 'Set_settings'])
def set_settings(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            settings = (message.text.split()[1:], message.chat.id)
            c = conn.cursor()
            c.execute('SELECT id FROM settings WHERE chat_id=?', settings[1:])
            id = c.fetchone()
            if id:
                c.execute('UPDATE settings SET max_warn = ?, time_ban = ?, mat_lst = ? WHERE chat_id = ?', (settings[0][0], settings[0][1], settings[0][2], settings[1]))
            else:
                c.execute('INSERT INTO settings (chat_id, max_warn, time_ban, mat_lst) VALUES (?, ?, ?, ?);', (settings[1], settings[0][0], settings[0][1], settings[0][2]))
            bot.send_message(message.chat.id, 'Настройки чата успешно обновлены')
            conn.commit()
            c.close()
        except IndexError:
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно отправить команду /set_settings 3 7200 мат,мат  -  где 3 - максимум предупреждений перед мутом, time_ban - время мута после лимита предупреждений, mat_lst - список запрещенных слов')

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
                bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=10)
                bot.send_message(message.chat.id, '<b>{0}</b> забанен навсегда'.format(name), parse_mode='HTML')
            else:
                bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
                bot.send_message(message.chat.id, '<b>{0}</b> забанен на {1} мин.'.format(name, message.text[5:]), parse_mode='HTML')
        except (AttributeError, ValueError):
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /ban на нужное сообщение и указать время бана, если время не указано - бан навсегда')

@bot.message_handler(commands=['mute', 'Mute'])
def mute(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            until = math.floor(time.time()) + int(message.text.split()[1]) * 60
            bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until, 
                can_send_messages= False,
                can_send_media_messages=False, 
                can_send_other_messages=False,
                can_add_web_page_previews=False)
            text = '<b>{0}</b> muted на {1} мин.'.format(message.reply_to_message.from_user.first_name, int(message.text.split()[1]))
            bot.send_message(message.chat.id, parse_mode='HTML', text=text)
        except (AttributeError, IndexError, ValueError):
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: /mute кол-во_минут')


@bot.message_handler(commands=['unmute', 'Unmute'])
def unmute(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            bot.restrict_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=None, 
                can_send_messages= True,
                can_send_media_messages=True, 
                can_send_other_messages=True,
                can_add_web_page_previews=True)
            text = '<b>{0}</b> разблокирован'.format(message.reply_to_message.from_user.first_name)
            bot.send_message(message.chat.id, parse_mode='HTML', text=text)
        except AttributeError:
            bot.send_message(message.chat.id, 'Неверный синтаксис команды: нужно ответить /unmute на сообщения юзера, которого нужно размутить')

def check_command(message):
    if not message.text is None:
        return message.text.startswith('/')

@bot.message_handler(func=check_command)
def del_command(message):
    bot.delete_message(message.chat.id, message.message_id)

def check_mat(message):
    if not message.text is None:
        c = conn.cursor()
        c.execute('SELECT mat_lst FROM settings WHERE chat_id = ?', (message.chat.id,))
        res = c.fetchone()
        conn.commit()
        c.close()
        try:
            mes = frozenset(re.findall(r'\w+', message.text.lower())) & frozenset(res[0].split(','))
        except TypeError:
            pass
        else:
            mes = frozenset(re.findall(r'\w+', message.text.lower())) & frozenset(res[0].split(','))
        return True if mes else False

@bot.message_handler(func=check_mat)
def del_mat(message):
    bot.delete_message(message.chat.id, message.message_id)
    warn = (message.chat.id, message.from_user.id, message.from_user.first_name)
    if check(message):
        bot.send_message(message.chat.id, 'Невозможно выдать предупреждение админу')
    else:
        warn_do(message, warn)

if __name__ == '__main__':
    bot.remove_webhook()
    while True:
        try:
            bot.polling(none_stop=True, interval=2)
        except:
            bot.polling(none_stop=True, interval=2)