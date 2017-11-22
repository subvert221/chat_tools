#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

BOTLIST = []
WHITELIST = []

class VKThread(threading.Thread):
    def __init__(self, login, password):
        super(VKThread, self).__init__()
        self.login = login
        self.password = password
    
    def run(self):
        api = self.auth(login = self.login, password = self.password)
        if api['success']:
            global BOTLIST
            self.user_id = self.get_id(api['api'])
            BOTLIST.append(self.user_id)
            try:
                self.longpoll_loop(api['vk_session'], api['api'])
            except ValueError:
                pass
    def auth(self, login, password):
        api = {}
        vk_session = vk_api.VkApi(login, password)
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
    
    def get_id(self, api):
        return api.users.get()[0]['id']

    def longpoll_loop(self, vk_session, api):
        longpoll = VkLongPoll(vk_session)
        for event in longpoll.listen():
            if event.from_chat and event.type == VkEventType.MESSAGE_NEW:
                try:
                    if event.text:
                        if event.text == '/assemble' and int(event.raw[7]['from']) in BOTLIST+WHITELIST:
                            with vk_api.VkRequestsPool(vk_session) as pool:
                                pool.method_one_param('messages.addChatUser', key='user_id', values=BOTLIST, default_values={'chat_id':event.chat_id})
                        elif event.text == '/shutdown' and int(event.raw[7]['from']) in BOTLIST+WHITELIST:
                                api.messages.removeChatUser(chat_id = event.chat_id, user_id = self.user_id)
                    elif not event.text:
                        if event.raw[7]['source_act'] == 'chat_kick_user' and int(event.raw[7]['source_mid']) in BOTLIST+WHITELIST and int(event.raw[7]['from'] != event.raw[7]['source_mid']):
                            api.messages.addChatUser(chat_id = event.chat_id, user_id = event.raw[7]['source_mid'])
                except (IndexError, KeyError):
                    pass
                except vk_api.vk_api.ApiError as error:
                    if '[9]' in str(error):
                        api.messages.send(chat_id = event.chat_id, message = 'See you in a couple of minutes...')
                        api.messages.removeChatUser(chat_id = event.chat_id, user_id = self.user_id)
