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

def check(message, user_id = 0):
    u_id = message.from_user.id if not user_id else user_id
    if bot.get_chat_member(message.chat.id, u_id).status in user_plus:
        return True

@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    c = conn.cursor()
    c.execute('SELECT welcome_mes FROM settings WHERE chat_id=?', (message.chat.id,))
    welcome_m = c.fetchone()
    if welcome_m[0]:
        sent_m = bot.send_message(message.chat.id,
        'Приветствуем, '+'<a href="tg://user?id='+str(message.new_chat_member.id)+'">'+message.new_chat_member.first_name+"</a>, в нашем чате!"+welcome_m[0],
        parse_mode='HTML', disable_web_page_preview=True)
    elif message.new_chat_member.id == config.bot_id:
        sent_m = bot.send_message(message.chat.id, 'Я должен быть администратором. Иначе мой функционал работать не будет!')
        c.execute('SELECT id FROM settings WHERE chat_id=?', (message.chat.id,))
        db_id = c.fetchone()
        if db_id:
            c.execute('UPDATE settings SET last_mess = ? WHERE chat_id = ?', (message.message_id, message.chat.id))
        else:
            c.execute('INSERT INTO settings (chat_id, last_mess) VALUES (?, ?)', (message.chat.id, message.message_id))
    conn.commit()
    Timer(60.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()
    c.close()


@bot.message_handler(commands=['pin', 'Pin'])
def pin(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id, disable_notification=True)
        except AttributeError:
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /pin на нужное сообщение.')
            Timer(10.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

@bot.message_handler(commands=['sd', 'Sd'])
def sd(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            bot.send_message(message.chat.id, ' '.join(message.text.split()[1:]))
        except telebot.apihelper.ApiException:
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно отправить команду /sd text - где text Ваше сообщение.')
            Timer(10.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

@bot.message_handler(commands=['sd_ch', 'Sd_ch'])
def sd_ch(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin and message.from_user.id == config.my_id:
        try:
            text = message.reply_to_message.text if not message.reply_to_message is None else ' '.join(message.text.split()[1:])
            bot.send_message('@pylearn_channel', text)
            bot.send_message(message.chat.id, "Cообщение успешно отправлено в канал t.me/pylearn_channel", disable_web_page_preview=True)
        except IndexError:
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /sd_ch на нужное сообщение или через пробел написать текст для отправки.')
            Timer(10.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

def warn_do(message, warn):
    c = conn.cursor()
    test = c.execute('SELECT chat_id, user_id, warn_count FROM warn WHERE chat_id=? AND user_id=?', warn[:2]).fetchone()
    name = warn[2] if len(warn) == 4 else warn[2]
    if test is None:
        c.execute('INSERT INTO warn (chat_id, user_id, warn_count) VALUES (?, ?, 1)', warn[:2])
        text = 'Количество предупреждений [{0}](tg://user?id={1}) увеличено до - 1.'.format(name, warn[1])
        sent_m = bot.send_message(message.chat.id, parse_mode='markdown', text=text)
    else:
        c.execute('UPDATE warn SET warn_count = warn_count + 1 WHERE chat_id=? AND user_id=?', warn[:2])
        c.execute('SELECT warn_count FROM warn WHERE chat_id=? AND user_id=?', warn[:2])
        warn_count = c.fetchone()[0]
        c.execute('SELECT max_warn, time_ban FROM settings WHERE chat_id=?', (message.chat.id,))
        data = c.fetchone()
        max_warn, time_ban = data[0], data[1]
        text = 'Количество предупреждений [{0}](tg://user?id={1}) увеличено до - {2}.'.format(name, warn[1], warn_count)
        sent_m = bot.send_message(message.chat.id, parse_mode='markdown', text=text)
        if warn_count >= max_warn:
            until = math.floor(time.time()) + time_ban * 60
            bot.restrict_chat_member(message.chat.id, warn[1], until_date=until, 
                                    can_send_messages= False, 
                                    can_send_media_messages=False, 
                                    can_send_other_messages=False,
                                    can_add_web_page_previews=False)
            sent_m = bot.send_message(message.chat.id, '[{0}](tg://user?id={1}) заблокирован на {2} мин.'.format(name, warn[1], time_ban), parse_mode='markdown')
            c.execute('DELETE FROM warn WHERE chat_id=? AND user_id=?', warn[:2])
    conn.commit()
    Timer(30.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()
    c.close()

@bot.message_handler(commands=['warn', 'Warn'])
def warn(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            warn = (message.chat.id, message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.is_bot)
        except AttributeError:
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /warn на нужное сообщение.')
        else:
            if check(message, message.reply_to_message.from_user.id):
                sent_m = bot.send_message(message.chat.id, 'Невозможно выдать предупреждение админу.')
            else:
                bot.delete_message(message.chat.id, message.reply_to_message.message_id)
                warn_do(message, warn)
        Timer(10.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

@bot.message_handler(commands=['unwarn', 'Unwarn'])
def unwarn(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            warn_c = (message.text.split()[1], message.chat.id, message.reply_to_message.from_user.id)
            c = conn.cursor()
            c.execute('UPDATE warn SET warn_count=warn_count - ? WHERE chat_id = ? AND user_id = ?', warn_c)
            c.execute('SELECT warn_count FROM warn WHERE chat_id=? AND user_id=?', warn_c[1:])
            warn = c.fetchone()
            if warn[0] <= 0:
                c.execute('DELETE FROM warn WHERE chat_id=? AND user_id=?', warn_c[1:])
                sent_m = bot.send_message(message.chat.id,
                '[{0}](tg://user?id={1}) больше не имеет предупреждений.'.format(message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.id),
                 parse_mode='markdown')
            else:
                sent_m = bot.send_message(message.chat.id,
                 'Количество предупреждений [{0}](tg://user?id={1}) уменьшено до - {2}.'.format(message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.id, warn[0]),
                  parse_mode='markdown')
            conn.commit()
            c.close()
        except (IndexError, TypeError, AttributeError):
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /unwarn на нужное сообщение и указать количество варнов, которые Вы хотите снять.')
        Timer(15.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

@bot.message_handler(commands=['iau', 'Iau'])
def info_about_user(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            user_info = (message.chat.id, message.reply_to_message.from_user.id)
        except AttributeError:
            sent_m = bot.send_message(message.chat.id, 
            'Неверный синтаксис команды: Нужно ответить командой /iau на сообщение пользователя о котором хотете узнать информацию.')
        else:
            c = conn.cursor()
            c.execute('SELECT warn_count FROM warn WHERE chat_id=? AND user_id=?', user_info)
            warn_count = c.fetchone()
            if warn_count:
                sent_m = bot.send_message(message.chat.id,
                '[{0}](tg://user?id={1}) имеет количество предупреждений - {2}.'.format(message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.id, warn_count[0]),
                parse_mode='markdown')
            else:
                sent_m = bot.send_message(message.chat.id, '[{0}](tg://user?id={1}) не имеет предупреждений.'.format(message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.id), parse_mode='markdown')
            c.close()
        Timer(15.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()
            

@bot.message_handler(commands=['set_settings', 'Set_settings'])
def set_settings(message):
    user_is_admin = check(message)
    bot.delete_message(message.chat.id, message.message_id)
    if user_is_admin:
        try:
            settings = (message.text.split()[1:], message.chat.id)
            c = conn.cursor()
            c.execute('UPDATE settings SET max_warn = ?, time_ban = ?, mat_lst = ? WHERE chat_id = ?', (settings[0][0], settings[0][1], settings[0][2], settings[1]))
            sent_m = bot.send_message(message.chat.id, 'Настройки чата успешно обновлены.')
            conn.commit()
            c.close()
        except IndexError:
            sent_m = bot.send_message(message.chat.id,
            'Неверный синтаксис команды: Нужно отправить команду /set_settings 3 7200 мат,мат  -  где 3 - максимум предупреждений перед мутом, time_ban - время мута после лимита предупреждений, mat_lst - список запрещенных слов.')
        Timer(15.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start() 

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
                sent_m = bot.send_message(message.chat.id, '[{0}](tg://user?id={1}) забанен навсегда'.format(name, message.reply_to_message.from_user.id), parse_mode='markdown')
            else:
                bot.kick_chat_member(message.chat.id, message.reply_to_message.from_user.id, until_date=until)
                sent_m = bot.send_message(message.chat.id, '[{0}](tg://user?id={1}) забанен на {2} мин.'.format(name, message.reply_to_message.from_user.id, message.text[5:]), parse_mode='markdown')
        except (AttributeError, ValueError):
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: Нужно ответить командой /ban на нужное сообщение и указать время бана, если время не указано - бан навсегда.')
        Timer(25.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

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
            text = '[{0}](tg://user?id={1}) замутен на {2} мин.'.format(message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.id, int(message.text.split()[1]))
            sent_m = bot.send_message(message.chat.id, parse_mode='markdown', text=text)
        except (AttributeError, IndexError, ValueError):
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: /mute кол-во_минут.')
        Timer(15.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

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
            text = '[{0}](tg://user?id={1}) разблокирован.'.format(message.reply_to_message.from_user.first_name, message.reply_to_message.from_user.id)
            sent_m = bot.send_message(message.chat.id, parse_mode='markdown', text=text)
        except AttributeError:
            sent_m = bot.send_message(message.chat.id, 'Неверный синтаксис команды: нужно ответить /unmute на сообщения юзера, которого нужно размутить.')
        Timer(15.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()

def check_command(message):
    c = conn.cursor()
    notif = c.execute('SELECT notif_range, last_mess, notif_mess FROM settings WHERE chat_id=?', (message.chat.id,)).fetchone()
    if notif and not notif[0] is None:     # Функция циклических напоминаний
        if message.message_id - notif[1] >= notif[0]+1:
            bot.send_message(message.chat.id, notif[2], disable_web_page_preview=True)
            c.execute('UPDATE settings SET last_mess = ? WHERE chat_id = ?', (message.message_id, message.chat.id))
    command_is_allowed = c.execute('SELECT com_is_allow FROM settings WHERE chat_id=?', (message.chat.id,)).fetchone()
    conn.commit()
    c.close()
    if not message.text is None:    # Функция запрета сообщений начинающих с /(тоесть команд ботам)
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
    if not message.text is None:
        c = conn.cursor()
        c.execute('SELECT mat_lst, auto_warn FROM settings WHERE chat_id = ?', (message.chat.id,))
        res = c.fetchone()
        c.close()
        try:
            if res[1] == 'False':
                return False
            mes = frozenset(re.findall(r'\w+', message.text.lower())) & frozenset(res[0].split(','))
        except (AttributeError, TypeError):
            pass
        else:
            mes = frozenset(re.findall(r'\w+', message.text.lower())) & frozenset(res[0].split(','))
            return True if mes else False

@bot.message_handler(func=check_mat)
def del_mat(message):
    bot.delete_message(message.chat.id, message.message_id)
    warn = (message.chat.id, message.from_user.id, message.from_user.first_name)
    if check(message):
        sent_m = bot.send_message(message.chat.id, 'Невозможно выдать предупреждение админу')
        Timer(10.0, bot.delete_message, args=[sent_m.chat.id, sent_m.message_id]).start()
    else:
        warn_do(message, warn)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            bot.send_message(config.debug_chat, e)
            bot.polling(none_stop=True)