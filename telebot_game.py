import telebot
from tp_game import TPGame
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
import os
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_ESCAPEGAME")

user_games = {}  # 全局字典，用於存用戶遊玩記錄
image_to_file_id = {} # 存照片的

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def exp_start(msg):
    id = msg.chat.id
    text = f"""
你好，請使用
/TP_Escape 指令來開始遊戲。
會自動從你上次的進度執行。
請用
/Delete_TP 指令來刪除遊戲進度。
"""
    bot.send_message(id, text)


@bot.message_handler(commands=['TP_Escape'])
def send_photo_to_group(msg):
    user_id = msg.from_user.id
    if user_id not in user_games:
        user_games[user_id] = TPGame(str(user_id))
    tpgame = user_games[user_id]
    image, description, actions = tpgame.tg_display()
    image_path = f'images/{image}'
    markup = InlineKeyboardMarkup()
    for action in actions:
        if not "condition" in action:
            button = InlineKeyboardButton(text=action["action"], callback_data=f'normal{action["action"]}')
        elif "unlocked" in action["condition"]["conditionKey"]:
            button = InlineKeyboardButton(text=action["action"], callback_data=f'normal{action["action"]}')
        else:
            button = InlineKeyboardButton(text=action["action"], callback_data=f'normal{action["action"]}')
        markup.add(button)

    if image ==  "5_0.jpg":
        # 這裡就代表說成功逃脫了。
        with open(image_path, 'rb') as photo:
            send = bot.send_photo(msg.chat.id, photo, caption=description)
            send = bot.send_message(msg.chat.id, "完成成就：")

    if image in image_to_file_id:
        file_id = image_to_file_id[image]
        bot.send_photo(msg.chat.id, file_id, caption=description, reply_markup=markup)
    else:
        with open(image_path, 'rb') as photo:
            send = bot.send_photo(msg.chat.id, photo, caption=description, reply_markup=markup)
            file_id = send.photo[0].file_id
            image_to_file_id[image] = file_id

@bot.callback_query_handler(func=lambda call: call.data.startswith("normal"))
def handle_query(call):
    action = call.data[6:]
    user_id = call.from_user.id
    if user_id not in user_games:
        user_games[user_id] = TPGame(str(user_id))
    tpgame = user_games[user_id]
    message_id = call.message.id
    tpgame.make_move(action)
    image, description, actions = tpgame.tg_display()
    image_path = f'images/{image}'
    markup = InlineKeyboardMarkup()
    if "password" in tpgame.get_current_state():
        button = InlineKeyboardButton(text="輸入密碼", callback_data="ask_input")
        markup.add(button)
    for action in actions:
        button = InlineKeyboardButton(text=action["action"], callback_data=f'normal{action["action"]}')

        markup.add(button)
    
    bot.delete_message(user_id, message_id)

    if image in image_to_file_id:
        file_id = image_to_file_id[image]
        bot.send_photo(user_id, file_id, caption=description, reply_markup=markup)
    else:
        with open(image_path, 'rb') as photo:
            send = bot.send_photo(user_id, photo, caption=description, reply_markup=markup)
            file_id = send.photo[0].file_id
            image_to_file_id[image] = file_id

@bot.callback_query_handler(func=lambda call: call.data == "ask_input")
def ask_input(call):
    msg = bot.send_message(call.message.chat.id, "請輸入您的內容：", reply_markup=ForceReply(selective=True))
    bot.register_next_step_handler(msg, handle_input)

def handle_input(msg):
    user_id = msg.from_user.id
    message_id = msg.id
    bot.delete_message(user_id, message_id)
    pwd = msg.text
    if user_id not in user_games:
        user_games[user_id] = TPGame(str(user_id))
    tpgame = user_games[user_id]
    tpgame.make_move(pwd)
    image, description, actions = tpgame.tg_display()
    image_path = f'images/{image}'
    markup = InlineKeyboardMarkup()
    if "password" in tpgame.get_current_state():
        button = InlineKeyboardButton(text="輸入密碼", callback_data="ask_input")
    for action in actions:
        button = InlineKeyboardButton(text=action["action"], callback_data=f'normal{action["action"]}')   
        markup.add(button)

    if image in image_to_file_id:
        file_id = image_to_file_id[image]
        bot.send_photo(user_id, file_id, caption=description, reply_markup=markup)
    else:
        with open(image_path, 'rb') as photo:
            send = bot.send_photo(user_id, photo, caption=description, reply_markup=markup)
            file_id = send.photo[0].file_id
            image_to_file_id[image] = file_id

    
bot.polling(none_stop=True)

