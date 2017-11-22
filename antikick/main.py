#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import vkthread

ACCOUNTS_FILE = 'accounts.txt'
WHITELIST_FILE = 'whitelist.txt'

def main():
    if not os.path.exists(ACCOUNTS_FILE):
        open(ACCOUNTS_FILE, 'a').close()
        print 'accounts.txt created! fill it and re-run the script'
        return
    else:
        with open(ACCOUNTS_FILE, 'r') as file:
            accounts = [line.strip().split(':') for line in file if line.strip()]
    if not os.path.exists(WHITELIST_FILE):
        print 'whitelist.txt not found, returning only bots themselves.'
        open(WHITELIST_FILE, 'a').close()
    else:
        with open(WHITELIST_FILE, 'r') as file:
            vkthread.WHITELIST = [int(line.strip()) for line in file if line.strip()]
    threads = {}
    for account in accounts:
        threads[account[0]] = vkthread.VKThread(*account)
        threads[account[0]].start()
        
if __name__ == '__main__':
    main()
