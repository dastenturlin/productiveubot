import json  # parse JSON responses from Telegram to Python dictionaries
import requests  # web requests to interact with telegram API
import time
import urllib
import logging
import os
from dbsetup import Databasesetup


from config import token

db = Databasesetup("/var/www/productiveubot/todo.sqlite")


TOKEN = token
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
NAME = "productiveubot"

users = []
tasks = []


def get_json_from_url(url):  # gets JSON from Telegram API url
    content = requests.get(url).content.decode("utf8")
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)

    js = get_json_from_url(url)  # list of updates in JSON format retrieved from API
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def handle_update(update):
    text = update["message"]["text"]
    chat = update["message"]["chat"]["id"]

    if chat not in users:
        users.append(chat)

    items = db.get_items(chat) 
    if text == "/done":
        if not items:
            send_message("*🐨There are no tasks at the moment. Start with typing anything below!*", chat)
        else:
            db.add_item("~", chat)
            
            items = db.get_items(chat)
            message = "\n".join(items)
            keyboard = build_keyboard(items)
            
            send_message("*🔥Congrats on completing the task! Select an item to delete from the keyboard: (just ignore ~ button)*", chat, build_keyboard(db.get_items(chat)))
            message = ""
            items = db.get_items(chat)
            keyboard = build_keyboard(items)
            send_message("*🔥Congrats on completing the task! Select an item to delete from the dropdown keyboard:*" + message, chat, keyboard)
            keyboard = build_keyboard(items)
            db.delete_item("~", chat)
    elif text in items:  # if user already sent this task
        tasks.append(text)

        db.delete_item(text, chat)
        items = db.get_items(chat)
        
        if not items:
            send_message("*☑Another task done!\nThere are no current tasks at the moment. Well done!*", chat)
        else:   
            message = "\n".join(items)
            keyboard = build_keyboard(items)
            send_message("*☑Another task done! Current tasks: \n*" + message, chat, keyboard)

    elif (text not in items) and (not text.startswith("/") and (text!="~")):  # if user didn't send it
        db.add_item(text, chat)
        items = db.get_items(chat)
        message = "\n".join(items)
        keyboard = build_keyboard(items)
        send_message("*✍New task added. Current tasks: \n*" + message, chat, keyboard)
    
    elif text == "/getnumusers":
        send_message("*Number of users: *" + str(len(users)), chat)

    elif text == "/getnummessages":
        send_message("*Number of tasks done: *" + str(len(tasks)), chat)
    
    
    elif text == "/start":
        keyboard = build_keyboard(items)
        send_message("*🗒️Welcome to your personal todo list! \n\nTo add the task, just type it below. "
            "\n\nDelete your task using dropdown menu or just type /done to remove it."
            " To clear your list, send /clear. \n\nThank you! Message @dastiish if you have any questions.*", chat, keyboard)
        message = "\n".join(items)
        send_message("*📝Current tasks: \n*" + message, chat)

    elif text == "/currenttasks":
        keyboard = build_keyboard(items)
        message = "\n".join(items)
        send_message("*📝Current tasks: \n*" + message, chat, keyboard)
    
    elif text == "/help":
        send_message("*🗒️Welcome to your personal todo list! \n\nTo add the task, just type it below. "
                         "\n\nDelete your task using dropdown menu or just type /done to remove it."
                         " To clear your list, send /clear. \n\nThank you! Message @dastiish if you have any questions.*", chat)

    elif text == "/clear":
        db.delete_all(text, chat)
        items = db.get_items(chat)

        message = "\n".join(items)
        keyboard = build_keyboard(items)
        send_message("*☑☑☑Well done!\nNow there are no tasks at the moment*" + message, chat)

    #elif text.startswith("/"):
        #continue


def handle_updates(updates):
    for update in updates["result"]:
        handle_update(update)

def get_last_chat_id_and_text(updates: {}):  # only last message instead of whole bunch of updates
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return text, chat_id


def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard": keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    requests.get(url).content.decode("utf8")


def main():
    db.setup()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)

    
if __name__ == '__main__':
    main()







