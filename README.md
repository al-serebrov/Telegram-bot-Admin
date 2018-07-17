Forked to try Telegram bot functionality and also add some more functionalities to basic repository.

# Telegram-bot-Admin

Simple Telegram bot to admin chats.

## Installation and configuration

Start a new virtual environment with Python3 and install all needed dependencies to it:
```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then you need to talk to BotFather as described [here](https://core.telegram.org/bots#botfather) and get an API TOKEN.
Also you need to disable privacy by sending BotFather a command `/setprivacy`

Add your API token to `env` file along with [user_id](https://www.youtube.com/watch?v=gLZqOmx8pl8) [bot_id and chat_id](https://habr.com/post/306222/), for example `config.env` as:
```
export TELEGRAM_BOT_TOKEN="your_token"
export USER_ID="your user id"
export BOT_ID="your bot id"
export DEBUG_CHAT_ID="0"
```
And run shell command `source config.env` to make that environmental variable available for `config.py` script.

Create a group in Telegram, convert it to the super group, add the bot to the group and grant it with admin rights.

## Available commands
Provide BotFather with the list of available commands:
```
pin - Pin message
sd - Send a message from bot
sd_ch - send a message to the chat
warn - Make a warning to the user
unwarn - Remove a warning from a user (provide a number of warnings to remove)
iau - Get quantity of user warnings
info_about_chat - Get chat settings info
ban - Ban user
mute - Mute user
unmute - Unmute user
warn_settings - Warn system settings
com_is_allow - Allow all users to use bot commands
auto_warn - Automatic warning settings
notif_range - Range of sending notifications
notif_mess - Notification message
welcome_mes - Set a welcome message
black_words - Get the list of restricted words
```

To use commands you need to reply to a user message with the command.
