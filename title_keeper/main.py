#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import sys
import os
import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from PIL import Image, ImageTk
from Tkinter import Tk, Label, Entry, Button

ACCOUNT_FILE = 'account.txt'
CHATLIST = 'chats.txt'
TITLE_PATH = 'title'

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
    
    if not os.path.exists(TITLE_PATH):
        os.mkdir(TITLE_PATH)
        with codecs.open('{0}/{1}'.format(TITLE_PATH, 'title.txt'), 'w', 'utf-8') as file:
            file.write('test')
        print 'title dir created! \ntest title created!'
        needs_restart = True
    
    if needs_restart:
        print 'Fill necessary files in and restart the script.'
        return
    
    title = get_title()
    if not title:
        print 'can\'t proceed with empty title!'
        return

    api = auth(login, password)
    if api['success']:
        user_id = api['api'].users.get()[0]['id']
        longpoll_loop(api['vk_session'], api['api'], user_id, chats, title)
            
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

def get_title():
    title = {'text': '', 'image': ''}
    title_items = os.listdir(TITLE_PATH)
    for item in title_items:
        if item.endswith('txt'):
            with open('{0}/{1}'.format(TITLE_PATH, item)) as file:
                title['text'] = unicode(file.read().strip(), 'utf-8')
        elif item.endswith(('jpg', 'png')):
            title['image'] = '{0}/{1}'.format(TITLE_PATH, item)
    return title

def initial_check(api, upload, user_id, chats, title):
    chats_info = api.messages.getChat(chat_ids = ','.join(str(i) for i in chats))
    for chat in chats_info:
        if title['text']:
            if chat['title'] != unicode(title['text']):
                api.messages.editChat(chat_id = chat['id'], title = title['text'])
        if title['image']:
            if 'photo_50' in chat:
                if chat['photo_50'].split('/')[4][-3:] != str(user_id)[-3:]:
                    upload.photo_chat(photo = title['image'], chat_id = chat['id'])
            else:
                upload.photo_chat(photo = title['image'], chat_id = chat['id'])
    
def longpoll_loop(vk_session, api, user_id, chats, title):
    longpoll = VkLongPoll(vk_session)
    upload = vk_api.VkUpload(vk_session)
    initial_check(api, upload, user_id, chats, title)

    for event in longpoll.listen():
        if event.from_chat and event.chat_id in chats:
            try:
                if title['text'] and event.raw[7]['source_act'] == 'chat_title_update' and event.raw[7]['source_text'] != title['text']:
                    api.messages.editChat(chat_id = event.chat_id, title = title['text'])
                if title['image'] and ((event.raw[7]['source_act'] == 'chat_photo_update' and int(event.raw[7]['attach1'].split('_')[0]) != user_id) or event.raw[7]['source_act'] == 'chat_photo_remove'):
                    upload.photo_chat(photo = title['image'], chat_id = event.chat_id)
            except (IndexError, KeyError):
                pass
            except vk_api.vk_api.ApiError as error:
                print 'Error:', str(error)

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
