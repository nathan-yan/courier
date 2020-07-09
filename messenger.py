import curses
from curses import wrapper
from curses.textpad import Textbox
import random
import locale 

import threading
import time

from fbchat import Client
from fbchat.models import *
import emoji
import aenum

import constants

import hashlib
import webbrowser
import pprint as pp
import random
import math
import numpy as np
import time 
import threading
import base64
import re
import pickle
import os.path
from os import path
import json
import requests
from io import BytesIO

from window import *
from modal import *
import utils

locale.setlocale(locale.LC_ALL, "");

class Messenger:
    def __init__(self, personal_id, user_dict, threadlist, messages):
        self.ME = personal_id
        self.user_dict = user_dict
        self.threads = threadlist

        # this is a sorta crappy priority queue solution that displays the most important/recent threads by ranking them priority-wise
        # everytime a thread gets a message the maximum priority and add 1 and update that thread's priority so it is displayed first
        # you can pin a thread by giving it a priority of -1
        self.thread_priority = []
        for i in range (len(self.threads)): 
            self.thread_priority.append([len(self.threads) - i, i])

        self.messages = messages
        self.active_thread = 1
        self.show_hash = False
        self.force_update = False

        self.thread_pictures = {}

        self.compact = True    # are we rendering in compact mode
        self.peek_hash = ""
        
    def getActiveThread(self):
        return self.threads[self.active_thread]
    
    def getActiveMessages(self):
        return self.messages[self.active_thread]

class MessengerClient(Client):
    def __init__(self, username, password, max_tries = 2, session_cookies = ""):
        super().__init__(username, password, max_tries = max_tries, session_cookies = session_cookies)

    def setMessenger(self, messenger_obj):
        self.messenger =  messenger_obj
    
    def onMessage(self, mid, author_id, message_object, thread_id, thread_type, ts, metadata, msg, **kwargs):
        # todo: maybe make self.messenger.threads a dictionary?   id -> thread
        self.markAsDelivered(thread_id, mid)

        curses.beep()

        for i in range (len(self.messenger.threads)):
            # if you've received a message mark the read flag in self.messenger as false
            # the flag is because we don't want to keep sending markAsRead notifications to facebook every keystroke.

            if self.messenger.threads[i].uid == thread_id:
                # percolate this thread to the top
                # the max_priority is the first element
                max_priority = self.messenger.thread_priority[0][0]
                for j in self.messenger.thread_priority:
                    if j[1] == i:
                        #pass

                        j[0] = max_priority + 1
                
                # resort the priority
                self.messenger.thread_priority.sort(reverse = True)

                # if you didn't write the message, set read to false
                self.messenger.threads[i].read = author_id == self.messenger.ME
                self.messenger.messages[i] = [message_object] + self.messenger.messages[i]
            
                tid = self.messenger.threads[self.messenger.active_thread].uid
                
                return;
        
        # we haven't found the thread, it's a new one!
        # get the thread
        thread_info = self.fetchThreadInfo(thread_id)
        
        # fetch thread messages
        thread_messages = self.fetchThreadMessages(thread_id, limit = 20)

        # append to the respective arrays, add a new entry into the priority queue
        thread_info[thread_id].start = 0
        thread_info[thread_id].read = False

        self.messenger.threads.append(thread_info[thread_id])
        self.messenger.messages.append(thread_messages)

        max_priority = self.messenger.thread_priority[0][0]
        self.messenger.thread_priority.insert(0, [max_priority + 1, len(self.messenger.threads) - 1])
        

    def onMessageSeen(self, seen_by, thread_id, thread_type, seen_ts, ts, metadata, msg):
        for i in range (len(self.messenger.threads)):
            if self.messenger.threads[i].uid == thread_id:
                # update the most recent message with seen
                self.messenger.messages[i][0].read_by.append(seen_by)

                break;

    def onReactionAdded(self, mid, reaction, author_id, thread_id, thread_type, ts, msg, **kwargs):
        for i in range (len(self.messenger.threads)):
            if self.messenger.threads[i].uid == thread_id:
                #self.messenger.messages[i] = [message_object] + self.messenger.messages[i]
                for message in self.messenger.messages[i]:
                    if message.uid == mid:
                        message.reactions[author_id] = reaction

                        
                        tid = self.messenger.threads[self.messenger.active_thread].uid
                        if tid == thread_id:
                            self.messenger.createMessages()
                        break;

                break;
    
    def onReactionRemoved(self, mid, author_id, thread_id, thread_type, ts, msg, **kwargs):
        for i in range (len(self.messenger.threads)):
            if self.messenger.threads[i].uid == thread_id:
                #self.messenger.messages[i] = [message_object] + self.messenger.messages[i]
                for message in self.messenger.messages[i]:
                    if message.uid == mid:
                        del message.reactions[author_id]

                        if self.messenger.active_thread == thread_id:
                            self.messenger.createMessages()
                        break;

                break;

class ListenThread(threading.Thread):
    def __init__(self, client):
        super().__init__(daemon = True)

        self.client = client
    
    def run(self):
        self.client.listen()

class DisplayThread(threading.Thread):
    def __init__(self, stdscr, thread_window, chat_window, textbox):
        super().__init__()

        self.thread_window = thread_window
        self.chat_window = chat_window
        self.textbox =  textbox

        self.stdscr = stdscr

    def run(self):
        curses.cbreak()
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        c = 0

        t = ""

        while True:
            c += 1
            time.sleep(0.015)

            if c % 10 == 0:
                # render 
                #curses.curs_set(0)
                self.thread_window.render()
                self.thread_window.refresh()

                #self.chat_window.render()
                #self.chat_window.refresh()

            #try:
            

            a = self.stdscr.getch()
            
            if a!= -1:
                t += str(a)
            
                self.stdscr.addstr(20, 100, t)
            

            if a == ord("Q"):
                break;
            
            self.textbox.processKey(a)
            self.textbox.render()
            
            self.textbox.refresh()

            #except curses.error as e:
            #    print(e)

            #self.stdscr.refresh()

def showPage(stdscr, lines, height_offset = 0):
    mheight, mwidth = stdscr.getmaxyx()

    max_length = max(len(l) for l in lines)
    
    for i, line in enumerate(lines):
        
        stdscr.addstr(mheight // 2 - len(lines) // 2 + i + height_offset, mwidth//2 - max_length // 2, line)

    return mheight // 2 - len(lines) // 2, mwidth//2 - max_length // 2, mheight // 2 - len(lines) // 2 + i + height_offset

def showLogin(stdscr):
    # splash screen
    # i'm just gonna manually center this screw it
    mheight, mwidth = stdscr.getmaxyx()

    lines = constants.login_page
    starty, startx, lasty = showPage(stdscr, lines)

    stdscr.addstr(starty + 1, startx + 2, "courier", curses.A_REVERSE)

    username = LoginTextBox(stdscr, 1, 30, lasty - 6, startx + 2)
    password = LoginTextBox(stdscr, 1, 30, lasty - 3, startx + 2, hidden = True)
    
    boxes = [username, password]
    focus = 0

    while True:
        time.sleep(0.02)
        a = stdscr.getch()

        if a == 10:     # enter
            break;
        elif a == 3:
            return None
        elif a == 9:    # tab
            boxes[focus].render(cursor = False) # remove the cursor from the previous focused box
            boxes[focus].refresh()

            focus += 1
            focus %= 2
                
        boxes[focus].processKey(a)
        
        boxes[focus].render()
        boxes[focus].refresh()
    
    return boxes

def main(stdscr):
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(4, 8, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
    
    stdscr.nodelay(True)
    curses.curs_set(0)

    mheight, mwidth = stdscr.getmaxyx()

    aenum.extend_enum(MessageReaction, "UNKNOWN_{}".format('💗'), '💗')
    #pretty.pprint(threads)
    #pretty.pprint(threadlist)

    #with open("./data.pkl", 'wb') as f:
    #    pickle.dump(threadlist, f)
    #    pickle.dump(threads, f)
    #    pickle.dump(threadInfo, f)
    #    pickle.dump(users, f)

    login_done = False
    if path.exists("cookies.json"):
        lines = constants.splash_page + ['', 'found cookies, attempting login...']
        starty, startx, lasty = showPage(stdscr, lines, height_offset = 0)
        stdscr.addstr(starty + 1, startx + 2, "courier", curses.A_REVERSE)

        with open("cookies.json", 'r') as cookies:
            c = json.loads(cookies.read())

            try:
                client = MessengerClient("", "", session_cookies = c, max_tries = 1)
                login_done = True
            except FBchatException:
                print("authentication by cookies failed") 
        

    while not login_done:
        stdscr.clear()
        response = showLogin(stdscr)
        if response == None:
            raise Exception("exiting because user quit program")
        
        username_box, password_box = response

        stdscr.refresh()

        username = username_box.text
        password = password_box.text
        
        stdscr.clear()

        lines = constants.splash_page + ['', 'attempting login...']
        starty, startx, lasty = showPage(stdscr, lines, height_offset = 0)
        stdscr.addstr(starty + 1, startx + 2, "courier", curses.A_REVERSE)

        stdscr.refresh()

        try:
            client = MessengerClient(username, password, max_tries = 2)
            login_done = True
        except FBchatException:
            print("authentication by credentials failed")

    with open("cookies.json", 'w') as f:
        # we have succesfully logged in, save cookies
        f.write(json.dumps(client.getSession()))

    # get personal_id
    personal_id = client.uid

    stdscr.clear()

    lines = constants.splash_page + ['', 'login successful!']
    starty, startx, lasty = showPage(stdscr, lines, height_offset = 0)
    stdscr.addstr(starty + 1, startx + 2, "courier", curses.A_REVERSE)

    stdscr.refresh()

    threads = client.fetchThreadList(limit = 20)
    messages = [client.fetchThreadMessages(threads[i].uid, limit = 20) for i in range (len(threads))]
    users = client.fetchAllUsersFromThreads(threads)
    
    for t, m in zip(threads, messages):
        if personal_id not in m[0].read_by:
            t.read = False
        else:
            t.read = True
        t.start = 0

    user_dict = {}
    for u in users:
        user_dict[u.uid] = u

    
    #with open("./data.pkl", 'rb') as f:
    #    threadlist = pickle.load(f)
    #    threads = pickle.load(f)
    #    threadInfo = pickle.load(f)
    #    users = pickle.load(f)
    
    #users = client.fetchAllUsersFromThreads(threadlist)
    #threads = [client.fetchThreadMessages(threadlist[i].uid) for i in range (len(threadlist))]

    #with open("./data.pkl", 'wb') as f:
    #    pickle.dump(threadlist, f)
    #    pickle.dump(threads, f)
    #    pickle.dump(threadInfo, f)
    #    pickle.dump(users, f)
    
    # create messenger object
    M = Messenger(personal_id,  user_dict, threads, messages,)
    
    client.setMessenger(M)
    M.active_thread = 0

    print(mwidth, mheight)
    thread_width = 0.25

    chat_window = MessengerChatWindow(client, M, stdscr, mheight - 5, int(mwidth * (1 - thread_width)) - 15, 0, int(mwidth * thread_width) + 6)

    thread_window = MessengerThreadWindow(client, M, stdscr, 
                                                        mheight - 1,
                                                        int(mwidth * thread_width), 1, 0)

    textbox = MessengerTextBox(client, M, stdscr, 3, 
                                                        int(mwidth * (1 - thread_width)) - 15, 
                                                        mheight - 4, 
                                                        int(mwidth * thread_width) + 10)

    stdscr.clear()

    # todo: eventually add a lock to prevent race conditions writing to the Messenger object
    # todo: add a separate requests thread that handles requests based on a queue of things to do, this prevents blocking in the main loop 
    lt = ListenThread(client)
    lt.start()

    c = 0

    t = ""

    while True:
        c += 1
        time.sleep(0.02)

        if c % 17 == 0 and c % 170 != 0:
            M.force_update = False

            # render 
            thread_window.render()
            thread_window.refresh()

        if c % 10 == 0:
            chat_window.render()
            chat_window.refresh()

        #if c % 10 == 0 or c % 17 == 0:
            #peek_modal.render()
            #peek_modal.refresh()

        #try:
        

        a = stdscr.getch()

        if a == 3:  # ctrl-c
            break;
                
        do_break = textbox.processKey(a)
        if do_break:
            break;

        textbox.render()
        textbox.refresh()


        curses.doupdate()

    #dt.start()
    #lt.start()

if __name__ == "__main__":
    wrapper(main)