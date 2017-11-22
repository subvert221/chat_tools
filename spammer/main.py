#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import codecs
import os
import time
import requests
import vk_api
from PIL import Image, ImageTk
from Tkinter import Tk, Label, Entry, Button


MESSAGE_PATH = 'message'
ACCOUNT_FILE = 'account.txt'
CHATLIST = 'chats.txt'
DEFAULT_TIMEOUT = 0.5

def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--timeout', type=int)
    return parser

def main():
    needs_restart = False
    if not os.path.exists(ACCOUNT_FILE):
        open(ACCOUNT_FILE, 'a').close()
        print 'account.txt created!'
        needs_restart = True
    else:
        with open(ACCOUNT_FILE, 'r') as file:
            login, password = file.read().strip().split(':')
        
    if not os.path.exists(CHATLIST):
        open(CHATLIST, 'a').close()
        print 'chats.txt created!'
        needs_restart = True
    else:
        with open(CHATLIST, 'r') as file:
            try:
                chats = [int(line.strip()) for line in file if line.strip()]
            except ValueError:
                print 'couldn\'t parse chat id in chats.txt, check for validity'
                needs_restart = True
    if not os.path.exists(MESSAGE_PATH):
        os.mkdir(MESSAGE_PATH)
        with codecs.open('{0}/{1}'.format(MESSAGE_PATH, 'message.txt'), 'w', 'utf-8') as file:
            file.write('test')
        print 'message dir created! \ntest message created!'
        needs_restart = True
        
    if needs_restart:
        print 'Fill necessary files in and restart the script.'
        return
    
    parser = create_parser()
    namespace = parser.parse_args()
    
    message = get_message()
    if not message:
        print 'can\'t proceed with empty message!'
        return
    
    api = auth(login, password)
    if api['success']:
        send_messages(api['api'], api['vk_session'], chats, message, namespace.timeout if namespace.timeout else DEFAULT_TIMEOUT)
    
def auth(login, password):
    api = {}
    vk_session = vk_api.VkApi(login, password, captcha_handler = captcha_handler)
    try:
        vk_session.auth()
        api['api'] = vk_session.get_api()
        api['vk_session'] = vk_session
        api['success'] = 1
        print '### auth {0} success! ###'.format(login)
    except vk_api.AuthError as error_message:
        print '{0}: {1}'.format(self.login, str(error_message))
        api['success'] = 0
    return api
    

def get_message():
    message = {'text': '', 'image_paths': [], 'image_links': []}
    message_items = os.listdir(MESSAGE_PATH)
    for item in message_items:
        if item.endswith('txt'):
            with open('{0}/{1}'.format(MESSAGE_PATH, item)) as file:
                message['text'] = file.read().strip()
        elif item.endswith(('jpg', 'png')):
            message['image_paths'].append('{0}/{1}'.format(MESSAGE_PATH, item))
    return message
    
def send_messages(api, vk_session, chats, message, timeout):
    if message['image_paths']:
        message['image_links'] = []
        for image_path in message['image_paths']:
            message['image_links'].append(image_upload(vk_session, image_path))
    while True:
        for chat in chats:
            msg = api.messages.send(chat_id = chat, message = message['text'], attachment = (','.join(image for image in message['image_links']) if message['image_links'] else ''))
            print 'message {0} was sent to chat {1}'.format(msg, chat)
            time.sleep(timeout)

def image_upload(vk_session, image):
    upload = vk_api.VkUpload(vk_session)
    photo = upload.photo_messages(image)
    return 'photo{0}_{1}'.format(photo[0]['owner_id'], photo[0]['id'])

def captcha_handler(captcha):
    root = Tk()
    root.title('captcha')
    def executor(event):
        global text
        text = entry.get()
        root.destroy()
    r = requests.get(captcha.get_url())
    with open('captcha.jpg', 'wb') as image:
        image.write(r.content)
    img = Image.open('captcha.jpg')
    photo = ImageTk.PhotoImage(img)
    label = Label(root, image=photo)
    entry = Entry()
    root.bind('<Return>', executor)
    root.focus_force()
    label.pack()
    entry.pack()
    entry.focus_force()
    root.mainloop()
    return captcha.try_again(text)

if __name__ == '__main__':
    main()
