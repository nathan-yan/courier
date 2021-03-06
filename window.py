
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
import curses
from curses import wrapper
from curses.textpad import Textbox
import random
import locale 
import emoji
import ago

from datetime import datetime

import constants

from fbchat import Client
from fbchat.models import *

from utils import *

color_search = re.compile("\${[0-9]}")
url_search = re.compile('(?:(?:https?|ftp):\/\/)?[\w/\-?=%#&.]+\.[\w/\-?=%#&.]+')

class ChangeYError(Exception):
    pass 

class Window:
    def __init__(self, stdscr, height, width, begin_y, begin_x):
        self.stdscr = stdscr

        self.width = width
        self.height = height
        self.begin_y = begin_y
        self.begin_x = begin_x

        self.mwidth = width
        self.mheight = height

        print("CREATING WINDOW H: %s, W: %s, Y: %s, X: %s" % (height, width, begin_y, begin_x))
        self.window = curses.newwin(height, width, begin_y, begin_x)

    def width(self, width):
        self.width= width
    
    def height(self, height):
        self.height = height
    
    def begin_y(self, begin_y):
        self.begin_y = begin_y
    
    def begin_x(self, begin_x):
        self.begin_x = begin_x

    def render(self):
        pass 

    def refresh(self):
        self.window.noutrefresh()
    
    def addstr(self, y, x, text, color = None):
        if color == None: 
            color = curses.color_pair(0)
        
        if y < 0 or (x + len(text)) > self.mwidth or x < 0 or y >= self.mheight:
            return
        
        else:
            self.window.addstr(y, x, text, color)

    def addch(self, y, x, text, color = None):
        if color == None: 
            color = curses.color_pair(0)
        
        if y < 0 or (x + len(text)) > self.mwidth or x < 0 or y >= self.mheight:
            return
        
        else:
            self.window.addstr(y, x, text, color)


class MessengerThreadWindow(Window):
    def __init__(self, client, messenger_obj, stdscr, height, width, begin_y, begin_x):
        super().__init__(stdscr, height, width, begin_y, begin_x)

        self.client = client
        self.M = messenger_obj

        self.init_pairs = True

    def render(self):
        self.window.clear()
        
        lines = []

        # draw the border
        self.addstr(0, 0, u"┌" + u"─" * (self.mwidth - 2) + u"┐")
        self.addstr(1, 0, ' ' * (self.mwidth - 1) + u"│")

        for i in range (self.mheight - 2):
            remaining_lines = self.mheight - (i + 1)

            if (i + 1) % (5 - 2 * self.M.settings['compact']) == 0 and i != 0 and (i + 1) // (5 - 2 * self.M.settings['compact']) < len(self.M.threads) and remaining_lines > 5:
                self.addch(i + 1, self.mwidth - 1, u'┤')
                self.addch(i + 1, 0, u'├')
            else:    
                self.addch(i + 1, self.mwidth - 1, u'│')
                self.addch(i + 1, 0, u'│')
        
        self.addstr(self.mheight - 2, 0, u"└" + u"─" * (self.mwidth - 2) + u"┘")

        for i, priority in enumerate(self.M.thread_priority[self.M.thread_start:]):
            thread_idx = priority[1]

            thread = self.M.threads[thread_idx]
            messages = self.M.messages[thread_idx]

            # draw separators
            remaining_lines = self.mheight - (i * (5 - 2 * self.M.settings['compact']))
            if remaining_lines > 5:
                if self.M.settings['compact']:
                    self.addstr(i * 3, 1, u"─" * (self.mwidth - 2))
                else:
                    self.addstr(i * 5, 1, u"─" * (self.mwidth - 2))

            try:
                if messages[0].text:
                    last = ellipses(self.window, self.M.user_dict[messages[0].author].name.split(" ")[0] + ": " + messages[0].text.encode('ascii', 'ignore').decode().replace("\n", ''), 9)
                else:
                    last = ellipses(self.window, self.M.user_dict[messages[0].author].name.split(" ")[0] + ": ?", 
                    9)
            except KeyError:
                # author can't be found
                last = "? : ?"

            pinned_code = self.M.settings['pinnedThreads'].get(thread.uid)

            code = pinned_code if pinned_code else produceHashThread(thread)[:3]
            name = ellipses(self.window, code + " " + str(thread.name), 9)
            lines.append([
                name,
                [(0, len(code), curses.color_pair(2)), (len(code) + 1, len(name), curses.color_pair(curses.COLOR_BLUE) | (curses.A_REVERSE) * (thread_idx == self.M.active_thread))]
            ])

            if self.M.ME not in messages[0].read_by and not self.M.threads[thread_idx].read:
                lines.append([
                    last,
                    [[0, len(last), curses.color_pair(5)]]
                ])
            else:
                lines.append([
                    last,
                    []
                ])

            if not self.M.settings['compact']:
                lines.append([''])
                lines.append([''])
            lines.append([''])
                                
                                # beginy       thread position, account for compactness
            start_identicon_y = self.begin_y + i * (5 - 2 * self.M.settings['compact']) + 1 - self.M.settings['compact']
            if (start_identicon_y) < self.mheight - 4:
                displayIdenticon(self.window, thread.uid, start_identicon_y, 2)

        render_lines(self.window, lines, padding = [2 - self.M.settings['compact'], 0, 5, 8])

        # if there's only 20 extra lines to render, load more threads
        if (len(lines) - self.mheight) < 20:
            new_threads = self.client.fetchThreadList(limit = 20, 
                                             before = self.M.last_thread_timestamp)[1:]

            new_messages = [self.client.fetchThreadMessages(new_threads[i].uid, limit = 2) for i in range (len(new_threads))]

            # update the last_thread_timestamp
            self.M.last_thread_timestamp = new_threads[-1].last_message_timestamp

            # grab new users
            new_users = self.client.fetchAllUsersFromThreads(new_threads)
            for u in new_users:
                self.M.user_dict[u.uid] = u

            for i, t in enumerate(new_threads):
                t.start = 0
                t.read = False
            
                min_priority = self.M.thread_priority[-1][0]
                self.M.thread_priority.append([min_priority - 1 - i, len(self.M.threads) + i])
            
            self.M.thread_priority.sort(reverse = True)

            self.M.threads += new_threads
            self.M.messages += new_messages

class MessengerChatWindow(Window):
    def __init__(self, client, messenger_obj, stdscr, height, width, begin_y, begin_x):
        super().__init__(stdscr, height, width, begin_y, begin_x)
        self.peek_modal = curses.newwin(20, 20, 0, 0)

        self.client = client
        self.M = messenger_obj
            
        self.current_y = self.mheight

        self.MARGIN = 6

        self.rendered_modal = False
        self.c = 0  # counter for rendering aesthetics 

    # todo: should move these bottom 3 methods to utils
    def processMessageText(self, msg):
        # this should return a list of lines with color instructions

        ret = []

        if msg.text:
            ret = [[i, []] for i in emoji.demojize(msg.text).split("\n")]

        msg.clickable = []

        clickable_counter = 0
        increment = 0
        mention_counter = 0     # how far along the text are we? used to count offset across split lines
        
        # check for links
        for i, line in enumerate(ret):
            # check for mentions
            # break each line apart based on mentions

            found_mentions = []

            print(msg.mentions)
            for mention in msg.mentions:
                if mention_counter + len(line[0]) >= mention.offset:
                    line[1].append([mention.offset, mention.offset + mention.length, curses.color_pair(3)]) 
                    found_mentions.append(mention)

            for match in url_search.finditer(line[0]):
                start, end = match.span()

                # check to make sure the span does not cross a mention
                for mention in found_mentions:
                    mention_start = mention.offset + increment
                    mention_end = mention.offset + mention.length + increment

                    if mention_start <= start <= mention_end or \
                       mention_start <= end <= mention_end or \
                       (mention_start <= start and mention_end >= end):
                        break;
                else:
                    start += increment
                    end += increment

                    url = line[0][start:end]
                    msg.clickable.append(url)

                    ret[i][0] = line[0][:start] +\
                        (url) +\
                        " [%s]" % (clickable_counter + 1) +\
                        line[0][end:]

                    extra = len(" [%s]" % (clickable_counter + 1))
                    increment += extra     # there are 12 extra characters added
                    clickable_counter += 1

                    # search for all instructions with a start after this one's end, and increment them (for mentions)
                    shiftInstructions(line[1], end, extra)

                    # add the instructions to line
                    line[1].append([start, end + extra, curses.color_pair(2)])
                        
                line[1].sort()  # sort the instructions by start. since they're non-overlapping it's fine

            mention_counter += 1 + len(line[0])    #newline + len(line)

        # check for attachments
        if msg.attachments:
            for i, attachment in enumerate(msg.attachments):
                if isinstance(attachment, ImageAttachment):
                    # get the url and add it to msg.clickable
                    msg.clickable.append(attachment.large_preview_url)

                    ret.append(["image attachment [%d] - %d x %d" % (clickable_counter + 1, attachment.large_preview_width, attachment.large_preview_height), 
                    
                    
                    [[0, len(str(clickable_counter)) + 1 + len('image attachment [%d]' % (clickable_counter + 1)), curses.color_pair(2)]]
                    
                    ])
                    
                    clickable_counter += 1

        return ret

    def processChunk(self, chunk):
        messages = []

        message_lines = []
        for i, message in enumerate(chunk):
            #try:
            message_lines = self.processMessageText(message)
            #except:
            #    text = [["cannot render", []]]
                
            messages.append(message_lines)
        # wrap the lines
        #wrapped_lines = wrapLines(lines, max_length = self.mwidth - 4)  # -4 for padding for surrounding messagebox characters 

        return messages

    def boxMessages(self, messages, message_objects, align = '<'):
        chars = '└┌│┐┘┤'

        lines = []
        message_start_locations = []    # these mark the relative y-coordinate of the first line of each boxed message, this is where things like reacts and message codes are displayed

        for i, (text, obj) in enumerate(zip(messages, message_objects)):
            max_length = max([len(t[0]) for t in text])

            if i == 0:
                lines = [[u"┌" + u"─" * (max_length + 1) + u"┐", []]]
            else:
                lines = []

            for c, l in enumerate(text):
                t = " " + l[0]

                lines.append([u"│" + t + u" " + (max_length + 1 - len(t)) + u"│", l[1]])

                if c == 0:
                    message_start_locations.append(len(lines))
                
            if i < len(messages):
                next_text = messages[i + 1]
                max_length_next = max([len(t[0]) for t in next_text])

                if max_length_next > max_length:
                    if align == '>':
                        lines.append([u"┌" + u"─" * max(0, max_length_next - max_length - 1)+ u"┴"+ u"─" * (max_length + 1) + u"┤", []])
                       #lines.append(u"├" + u"─" * (max_length + 1) + u"┴" + u"─" * max(0, max_length_next - max_length - 1) + u"┐")

                    else:
                        lines.append([u"├" + u"─" * (max_length + 1) + u"┴" + u"─" * max(0, max_length_next - max_length - 1) + u"┐", []])
                elif max_length_next == max_length:
                    if align == ">":
                        lines.append([u"├" + u"─" * (max_length - max_length_next - 1) + u"─" * (max_length_next + 1) + u"┤", []])
                    
                    else:
                        lines.append([u"├" + u"─" * (max_length_next + 1) + u"┤", []])
                else:
                    if align == ">":
                        lines.append([u"└" + u"─" * (max_length - max_length_next - 1) + u"┬" + u"─" * (max_length_next + 1) + u"┤", []])
                    
                    else:
                        lines.append([u"├" + u"─" * (max_length_next + 1) + u"┬" + u"─" * (max_length - max_length_next - 1) + u"┘", []])
                
            else:
                lines.append([u"└" + u"─" * (max_length + 1) + u"┘", []])

        return lines, message_start_locations

    def changeY(self, delta):
        self.current_y += delta
        
    def getRenderableMaxLength(self, message_object):
        processed_text = self.processMessageText(message_object)
        renderable_lines = []

        for line in processed_text:
            # wrap the line
            wrapped_line = wrapLine(line, int(self.mwidth * 0.4))
        
            # render these lines
            self.changeY(-len(wrapped_line))
            renderable_lines += wrapped_line
        
        if message_object.unsent:
            renderable_lines = [["message removed", [[0, len("message removed"), curses.color_pair(4)]]]]
            self.changeY(-1)        # because we're inserting a line

        if not renderable_lines:
            renderable_lines = [["cannot render", [[0, len("cannot render"), curses.color_pair(2)]]]]

            self.changeY(-1)        # because we're inserting a line

        max_length = max(len(t[0]) for t in renderable_lines)

        return max_length

    def add(self, message_object, align = "<", display = None, next_max_length = 0, color = None, show_hash = False, peek = False):
        # process text 
        if display == 'join-bottom' or display == 'join-bottom-reply':
            pass

        else:
            self.changeY(-1)

        processed_text = self.processMessageText(message_object)
        renderable_lines = []

        for line in processed_text:
            # wrap the line
            wrapped_line = wrapLine(line, int(self.mwidth * 0.4))
        
            # render these lines
            self.changeY(-len(wrapped_line))
            renderable_lines += wrapped_line
        
        if message_object.unsent:
            renderable_lines = [["message removed", [[0, len("message removed"), curses.color_pair(4)]]]]
            self.changeY(-1)        # because we're inserting a line

        if not renderable_lines:
            renderable_lines = [["cannot render", [[0, len("cannot render"), curses.color_pair(2)]]]]

            self.changeY(-1)        # because we're inserting a line

        max_length = max(len(t[0]) for t in renderable_lines)

        padding_left = 2 + self.MARGIN
        if align == '>':
            padding_left = self.mwidth - 2 - 2 - max_length - self.MARGIN

        if self.M.settings['compact']:
            if align == '<':
                padding_left -= 2
            else:
                padding_left += 2

        render_lines(self.window, renderable_lines, padding = [self.current_y + 1 * self.M.settings['compact'], 2, 0, padding_left], align = "<", default_color = color)

        if not self.M.settings['compact']:
            self.changeY(-1)

        # draw a box
        
        if align == ">":
            start_x = self.mwidth - 2 - 4 - max_length - self.MARGIN
        else:
            start_x = 0 + self.MARGIN

        if not self.M.settings['compact']:
            # render top border
            self.addstr(self.current_y, start_x, "┌" + "─" * (max_length + 2) + "┐", color)
            
            # render bottom border
            if display == 'join-bottom-reply':
                if align == '<':
                    self.addstr(self.current_y + len(renderable_lines) + 1, start_x + next_max_length + 4, "─" * (max_length - next_max_length - 1) + "┘" * ((max_length - next_max_length) > 0), color)
                elif align == '>':
                    self.addstr(self.current_y + len(renderable_lines) + 1, start_x, "└" * (max_length > next_max_length) + '─' * (max_length - next_max_length - 1), color)
                
            else:
                self.addstr(self.current_y + len(renderable_lines) + 1, start_x, "└" + "─" * (max_length + 2) + "┘", color)
        
            # render left border
            for h in range (len(renderable_lines)):
                self.addch(self.current_y + h + 1, start_x, "│", color)

            # render right border
            for h in range (len(renderable_lines)):
                self.addch(self.current_y + h + 1, start_x + max_length + 3, "│", color)

        if display == 'join-bottom' and not self.M.settings['compact']:
            # figure out where to join
            if next_max_length > max_length:
                if align == '<':
                    self.addch(self.current_y + h + 2, start_x, '├', color)
                    self.addch(self.current_y + h + 2, start_x + max_length + 3, '┴', color)
                
                elif align == '>':
                    self.addch(self.current_y + h + 2, start_x, '┴', color)
                    self.addch(self.current_y + h + 2, start_x + max_length + 3, '┤', color)

            elif next_max_length < max_length:
                if align == '<':
                    self.addch(self.current_y + h + 2, start_x, '├', color)
                    self.addch(self.current_y + h + 2, start_x + next_max_length + 3, '┬', color)
                
                elif align == '>':    
                    self.addch(self.current_y + h + 2, start_x + (max_length - next_max_length), '┬', color)
                    self.addch(self.current_y + h + 2, start_x + max_length + 3, '┤', color)
                
                
            elif next_max_length == max_length:
                if align == '>':
                    self.addch(self.current_y + h + 2, start_x, '├', color)
                    self.addch(self.current_y + h + 2, start_x + max_length + 3, '┤', color)
                elif align == '<':
                    
                    self.addch(self.current_y + h + 2, start_x, '├', color)
                    self.addch(self.current_y + h + 2, start_x + max_length + 3, '┤', color)
        
        # render react information
        if message_object.reactions:
            react_information = "["

            reactions = {}
            for key in message_object.reactions.keys():
                react = constants.react_mapping.get(message_object.reactions[key])
                if not react:
                    react = 'unk'

                if react not in reactions:
                    reactions[react] = 1
                else:
                    reactions[react] += 1

            for react in reactions.keys():
                react_information += '  %s: %d  ' % (react, reactions[react])

            react_information += ']'

            if align == '<':
                self.addstr(self.current_y + 1, start_x + max_length + 3 + 2, react_information)
            else:
                self.addstr(self.current_y + 1, start_x - len(react_information) - 2, react_information)

        # render hash
        code = produceHash(message_object)

        if align == '<' and show_hash:
            self.addstr(self.current_y + 1, start_x - 5, code[:4], curses.color_pair(2))
        elif align == '>' and show_hash:
            self.addstr(self.current_y + 1, start_x + max_length + 3 + 2 , code[:4], curses.color_pair(2))

        # if peeking, render a modal
        if code[:4] == self.M.peek_hash:
            timestamp = int(message_object.timestamp) / 1000
            formatted_time = datetime.fromtimestamp(timestamp).strftime('%d %B, %Y @ %I:%M%p')

            peek_lines = [
                [
                 "Peek information for message %s" % code[:4], 
                 [[len("Peek information for message "), len("Peek information for message %s" % code[:4]), curses.color_pair(2)]]
                ],
                [""],
                ["Sent at", [[0, len('sent at'), curses.color_pair(3)]]],
                [formatted_time, []],
                
            ]

            if message_object.reactions:
                peek_lines += [
                    [""],
                    ["Reacts", [[0, 6, curses.color_pair(3)]]],
                ]

                for key in message_object.reactions.keys():
                    react = constants.react_mapping.get(message_object.reactions[key]).upper()
                    name = self.M.user_dict[key].name
                    peek_lines.append(
                        ["%s - %s" % (name, react), [[len("%s -" % name), len("%s - %s" % (name, react)), curses.color_pair(2)]]]
                    )

            max_peek_length = max([len(l[0]) for l in peek_lines])

            self.peek_modal.resize(len(peek_lines) + 4, max_peek_length + 6)
            self.peek_modal.clear()

            move_y = self.current_y + 2 - len(peek_lines) - 4 + len(renderable_lines)
            if (move_y) < 1 or len(renderable_lines) >= len(peek_lines):
                move_y = self.current_y
            
            move_x = start_x + max_length + 3 + 2
            if align == '>':
                move_x = start_x - max_peek_length - 6  # bruh we got hella padding

            if move_y >= 1:
                self.peek_modal.mvwin(move_y, self.begin_x + move_x)
                render_lines(self.peek_modal, peek_lines, padding = [2, 0, 0, 3])
                self.peek_modal.box()

                self.rendered_modal = True

        return max_length
        
    def render(self):
        self.c += 1

        start = self.M.getActiveThread().start

        self.window.clear()

        lines = []
        self.current_y = self.mheight - 4
        messages = self.M.messages[self.M.active_thread][start:]

         # render the read_by
        if messages[0].read_by and start == 0:
            read_by_description = "Read by "

            for i, uid in enumerate(messages[0].read_by):
                name = self.M.user_dict[uid].name
                read_by_description += name + ", "

                if len(read_by_description) > self.mwidth * 0.6:
                    # stop here
                    read_by_description = read_by_description[:-2]
                    read_by_description += " and %s more" % (len(messages[0].read_by) - i)
                    break;
            else:
                read_by_description = read_by_description[:-2]

            self.addstr(self.current_y + 3, self.MARGIN, read_by_description)

            self.addstr(self.current_y + 3, self.MARGIN, read_by_description)

        #if self.c % 3 == 0:
        typing_description = ""
        user_count = 0
        users_typing = self.M.users_typing.get(self.M.getActiveThread().uid)

        if users_typing:
            for typing_user in users_typing:
                name = self.M.user_dict[typing_user].name
                typing_description += name + ", "
                user_count += 1 
            
            typing_description = typing_description[:-2]
            if user_count == 1:
                typing_description += " is typing"
            elif user_count > 1:
                typing_description += " are typing"
            
            self.addstr(self.current_y + 1, self.MARGIN, ["▪", "◼"][(self.c) % 2] + " " + typing_description)

        # messages are from most recent to latest

        # queued messages represents the current chunk
        # visually each message appended to the list is another message higher

        current_y = self.mheight - 5
        t = 0

        future_message = None
        future_message_max_length = None
        if start:
            future_message = self.M.messages[self.M.active_thread][start - 1]

            future_message_max_length = self.getRenderableMaxLength(future_message)

        messages_to_render = []

        for i, m in enumerate(messages):
            messages_to_render.append(m)
            m.is_replied_to = False

            if m.replied_to:
                m.replied_to.is_replied_to = True
                messages_to_render.append(m.replied_to)

        for i, m in enumerate(messages_to_render):
            align = "<"
            color = curses.color_pair(curses.COLOR_WHITE)

            check_align = m
            if m.is_replied_to:
                check_align = future_message

            if check_align.author == self.M.ME:
                align = ">"
                color = curses.color_pair(curses.COLOR_BLUE)


            # the current message is a grayed out replied_to message 
            # OR there exists a future message, the author was the same, this current message was not replied to, nor was the future message
            # AND if the last next message is less than 10 minutes apart
            if m.is_replied_to or ((future_message and future_message.author == m.author  and not m.replied_to and not future_message.is_replied_to) and (int(future_message.timestamp) - int(m.timestamp))/1000 < 60 * 10):

                display = 'join-bottom'
                if m.is_replied_to:
                    color = curses.color_pair(4)
                    display = 'join-bottom-reply'

                future_message_max_length = self.add(m, display = display, align = align, next_max_length = future_message_max_length, color = color, show_hash = self.M.show_hash)

                # if this is the message someone replied to, render the reply description

                if m.is_replied_to:
                    if m.author == future_message.author:
                        if m.author == self.M.ME:
                            description = "You replied to yourself"
                        else:
                            p1 = self.M.user_dict[future_message.author].name
                            description = "%s replied to themself" % p1
                    else:
                        p1 = "You" if future_message.author == self.M.ME else self.M.user_dict[future_message.author].name
                        p2 = "You" if m.author == self.M.ME else self.M.user_dict[m.author].name
                        description = "%s -> %s" % (p1, p2)

                    if not self.M.settings['compact']:
                        self.changeY(-1)

                    # render the description
                    render_lines(
                            self.window, 
                            [[description, [[0, len(description), curses.color_pair(3)]]]],
                            padding = [self.current_y, 2 + self.MARGIN - 2 * self.M.settings['compact'], 0, self.MARGIN],
                            align = ">" if future_message.author == self.M.ME else "<"
                        )
                    
                    self.changeY(-1)

            else:
                if future_message and future_message.author != self.M.ME and not future_message.is_replied_to:
                    if not self.M.settings['compact']:
                        self.changeY(-1)
                    author_name =self.M.user_dict[future_message.author].name

                    render_lines(
                        self.window, 
                        [[author_name, [[0, len(author_name), curses.color_pair(curses.COLOR_BLUE)]]]],
                        padding = [self.current_y, 2, 0, self.MARGIN],
                        align = "<"
                    )

                    self.changeY(-1)
            
                if future_message and (int(future_message.timestamp) - int(m.timestamp))/1000 >= 60 * 60:
                    self.changeY(-2)

                    timestamp = int(future_message.timestamp) / 1000

                    formatted_time = ago.human(timestamp)

                    render_lines(
                        self.window, 
                        [[formatted_time, [[0, len(formatted_time), curses.color_pair(4)]]]],
                        padding = [self.current_y, 0, 0, 0],
                        align = "^"
                    )

                    self.changeY(-1)

                future_message_max_length = self.add(m, align = align, color = color, show_hash = self.M.show_hash)
            
            self.window.move(0, 0)
            # clear the line  because there is probably stuff overwritten and it creates artifacts
            self.window.clrtoeol()

            if self.current_y <= 0:
                break;


            future_message = m

        # we actually haven't filled up the screen, in that case request more messages
        # or if there were still less than 10 messages to render by the time we broke
        if self.current_y > 1 or i > len(messages_to_render) - 10:
            new_messages = self.client.fetchThreadMessages(
                self.M.getActiveThread().uid,
                before = self.M.getActiveMessages()[-1].timestamp,
                limit = 20
            )

            active_messages = self.M.getActiveMessages()
            active_messages += new_messages[1:]
            #self.render()

        """
        queued_messages = []
        for i, m in enumerate(messages):
            if i != len(messages) - 1:
                queued_messages.append(m)

                if m.replied_to:
                    queued_messages.append(m)
            
                # if there was a change in author the chunk is finished
                # replies are also chunk-finishers because we'd like to render them as their own message chunks for aesthetics
                if messages[i + 1].author != m.author or m.replied_to or messages[i + 1].replied_to:
                    t += 1
                    message_starts = []

                    processed_messages = self.processChunk(queued_messages)

                    # wrap the messages
                    #for m in processed_messages:
                    #    for l in m:
                    #        l
                    for j, msg in enumerate(processed_messages):
                        for l in msg:
                            # wrap the line
                            wrapped = wrapLine(l, int(self.mwidth * 0.4))
                            current_y -= len(wrapped)

                            align = '<'
                            if queued_messages[j].author == self.ME:
                                align = '>'

                            render_lines(self.window, wrapped, padding = [current_y, 2, 0, 0], align = align)
                            message_starts.append(current_y)

                            current_y -= 1

                    queued_messages = []

                    # render author name
                    current_y -= 1

                    author_name = self.user_dict[m.author].name
                    render_lines(
                        self.window,
                        [
                            [author_name, [[0, len(author_name), curses.color_pair(curses.COLOR_BLUE)]]]
                        ],
                        padding = [current_y, 2, 0, 0], 
                        align = ">" if m.author == self.ME else "<"
                    )
                    current_y -= 1

                    # draw boxes
                    for message_start, message in zip(message_starts, queued_messages):
                        pass
        """

        #raw_lines = []
        #for i in range (len(processed_messages)):
        #    if (queued_messages[i].author == self.ME):
        #        for l in processed_messages[i]:
        #            l[1] = ['>'] + l[1]

        #    raw_lines += processed_messages[i]

        
        #print(raw_lines, "raw_lines")
        
        #render_lines(self.window, raw_lines)
    
    def refresh(self):
        self.window.noutrefresh()

        if self.rendered_modal:
            self.peek_modal.noutrefresh()
            self.rendered_modal = False 

class MessengerTextBox(Window):
    def __init__(self, client, messenger_obj, stdscr, width, height, begin_y, begin_x):
        super().__init__(stdscr, width, height, begin_y, begin_x)

        self.stdscr = stdscr

        self.M = messenger_obj
        self.client = client

        self.cursor_position = 0 
        self.text = ''
        self.prev_text = ''

        self.mentions = []
        self.autocomplete_matches = []
        self.autocomplete_modal = curses.newwin(20, 20, 0, 0)
        self.autocomplete_modal_selection = 0
        self.rendered_modal = False

    def textDelta(self):
        """
            both current and previous are arrays of characters. we assume these are single line inputs with no need for wrapping
        """

        # the first thing to do is delete characters at the end if the previous string was longer than the current
        #for i in range (len(self.prev_text) - len(self.text) + 1):
        #    self.window.delch(1, 2 + len(self.text) + i - 1)
        self.window.clear()

        # now you can safely add str
        
        self.addstr(1, 2, self.text)

        # for all mentions just overwrite the original text wth colored text, i'd probably make this a render_line later but i'm too lazy rn
        for mention in self.mentions:
            # mention[1] is offset
            # mention[2] is length
            text = self.text[mention[1] : mention[1] + mention[2]]
            self.addstr(1, 2 + mention[1], text, curses.color_pair(3))
    
    def shiftMentions(self, end, shift, mentions = None):
        if not mentions: mentions = self.mentions

        for mention in self.mentions:
            if mention[1] >= end:
                mention[1] += shift

    def processKey(self, a):
        
        if a == 8:
            # if the char we're deleting interesects a mention delete it
            for i, mention in enumerate(self.mentions):
                if mention[1] <= self.cursor_position <= mention[1] + mention[2]:
                    self.text = self.text[:mention[1]] + self.text[mention[1] + mention[2]:]
                    self.cursor_position = max(0, mention[1])

                    # shift all mentions that come after this
                    self.shiftMentions(mention[1] + mention[2], -mention[2])

                    del self.mentions[i]
                    break;
            else:

                if self.cursor_position > 0:
                    self.text = self.text[:self.cursor_position - 1] + self.text[self.cursor_position:]
                    self.shiftMentions(self.cursor_position, -1)

                self.cursor_position = max(0, self.cursor_position - 1)

        elif a == curses.KEY_LEFT or a == curses.KEY_B1:
            
            self.cursor_position = max(0, self.cursor_position - 1)

        elif a == curses.KEY_RIGHT or a == curses.KEY_B3:
            
            self.cursor_position = min(len(self.text), self.cursor_position + 1)

        elif a == curses.CTL_LEFT or a == curses.ALT_B:
            try:
                self.cursor_position -= self.cursor_position - self.text.rindex(" ", 0, self.cursor_position - 1) - 1
            except ValueError:
                self.cursor_position = 0

        elif a == curses.CTL_RIGHT or a == curses.ALT_F:
            try:
                self.cursor_position += self.text.index(" ", self.cursor_position) - self.cursor_position + 1
            except ValueError:
                self.cursor_position = len(self.text)

        elif a == curses.KEY_SLEFT:
            # move left selection one back
            pass

        elif a == curses.KEY_SRIGHT:
            # move right selection one back
            pass

        elif a == curses.KEY_DC:
            # del key
            self.text = self.text[:self.cursor_position] + self.text[self.cursor_position + 1:]

        elif a == 9 or a == curses.KEY_UP or a == curses.KEY_A2:   # ctrl-I, KEY_A2 is cuz hyper is weird?
            if self.rendered_modal:
                if a == 9:   # this is the tab button, in this case we don't go up/down we just autocomplete
                             # i would've binded this to the enter button but it's so natural for us to tab when autocompleting
                             # also binding to enter would cause accidental message sends

                    # find the closest @ sign
                    at_index = self.text.rindex('@', 0, self.cursor_position)

                    name, uid = self.autocomplete_matches[self.autocomplete_modal_selection % len(self.autocomplete_matches)]
                    self.mentions.append([uid, at_index, len(name) + 1])    # +1 for the @ character
                    self.text = self.text[:self.cursor_position] + name[self.cursor_position - at_index - 1: ] + " " + self.text[self.cursor_position:]

                    self.cursor_position = at_index + len(name) + 1

                else:
                    self.autocomplete_modal_selection -= 1
            else:
                self.M.getActiveThread().start += 5
        
        elif a == 11 or a == curses.KEY_DOWN or a == curses.KEY_C2:    # ctrl-K, KEY_C2 is cuz hyper is weird?
            if self.rendered_modal:
                self.autocomplete_modal_selection += 1
            elif self.M.getActiveThread().start >= 5 :
                self.M.getActiveThread().start -= 5

        elif a == curses.CTL_DOWN:
            self.M.thread_start += 4

        elif a == curses.CTL_UP:
            if self.M.thread_start >= 4:
                self.M.thread_start -= 4

        elif a == 10:
            send_msg = True
        
            # send the text
            # strip leading and trailing whitespace
            self.text = self.text.strip()
            if len(self.text) == 0:
                self.text = ''
                self.prev_text = ''
                cursor_position = 0
                return

            self.window.clear()
            self.window.refresh()

            if self.text == ':q' or self.text == ':Q':
                return True

            msg = Message(text = emoji.emojize(self.text))
            

            if self.text and self.text[0] in ':!':
                if matchBeginning(self.text, [":compact"]):
                    self.M.settings['compact'] = not self.M.settings['compact']
                    send_msg = False
                
                elif matchBeginning(self.text, ['pcls']):
                    self.M.peek_hash = ""
                    send_msg = False

                elif matchBeginning(self.text, [':pin']):
                    name = self.text.split(' ')[1]

                    if name not in self.M.settings['pinnedThreads'].values():
                        self.M.settings['pinnedThreads'][self.M.getActiveThread().uid] = name
                        self.M.updateSettings()

                    send_msg = False
                
                elif matchBeginning(self.text, [':unpin']):
                    uid = self.M.getActiveThread().uid

                    if uid in self.M.settings['pinnedThreads']: 
                        del self.M.settings['pinnedThreads'][uid]
                        self.M.updateSettings()
                    
                    send_msg = False
 
                elif matchBeginning(self.text, [':r']):     # user is defining some quick replies
                    # search for | characters to delimit options 

                    options = self.text.split("|")[1:]

                    quick_replies = []
                    for o in options: 
                        q = QuickReplyText(o)
                        q._type = 'text'
                        quick_replies.append(q)
            
                    # let's hope there aren't any mentions in the options LOL
                    msg.text = msg.text[3:self.text.index("|")]
                    msg.quick_replies = quick_replies
                    self.shiftMentions(3, -3)
                    
                elif matchBeginning(self.text, [':switch', ':s ', ":S", ":Switch"]):
                    thread_code = self.text.split(" ")[1]

                    if (thread_code in ['-u', '-t', '-f']):   
                        # -u = users
                        # -t = threads
                        # -f = fuzzy (everything)
                        
                        name = ' '.join(self.text.split(" ")[2:])

                        try:
                            if thread_code == '-u':
                                thread = self.client.searchForUsers(name, limit = 1)[0]
                            elif thread_code == '-t':
                                thread = self.client.searchForGroups(name, limit = 1)[0]
                            elif thread_code == '-f':
                                thread = self.client.searchForThreads(name, limit = 1)[0]

                        except FBchatException as e:
                            print(e, 'matchBeginning :switch')
                            send_msg = False
                            
                        except IndexError as e:
                            print(e, "matchBegining :switch, index")
                            send_msg = False
                        else:
                            # check if the thread already exists
                            for i, t in enumerate(self.M.threads):
                                if t.uid == thread.uid:
                                    self.M.active_thread = i
                                    break; 
                            else: 
                                # thread does not exist, there is no need to add it to priority queue, cuz we won't actually display it 
                                # # there is not point in displaying a possibly old thread 
                                # plus if you actually say something it will percolate to the top anyway
                                
                                # get thread info
                                thread_info = self.client.fetchThreadInfo(thread.uid)
                                
                                # fetch thread messages
                                thread_messages = self.client.fetchThreadMessages(thread.uid, limit = 20)
                                
                                if thread_messages:
                                    new_users = self.client.fetchAllUsersFromThreads([thread])
                                    for u in new_users:
                                        self.M.user_dict[u.uid] = u

                                    thread_info[thread.uid].start = 0
                                    thread_info[thread.uid].read = False 

                                    self.M.threads.append(thread_info[thread.uid])
                                    self.M.messages.append(thread_messages)

                                    self.M.active_thread = len(self.M.threads) - 1

                            send_msg = False

                    for i, t in enumerate(self.M.threads):
                        if self.M.settings['pinnedThreads'].get(t.uid) == thread_code or produceHashThread(t)[:3] == thread_code:
                            self.M.active_thread = i
                            break;

                    send_msg = False
                
                elif len(self.text) >= 5:
                
                    code = self.text[1:5]
                    for m in self.M.messages[self.M.active_thread]:
                        if produceHash(m)[:4] == code:

                            # we're replying
                            if self.text[0] == '!':
                                msg.reply_to_id = m.uid
                                msg.text = msg.text[6:]

                                # shift mentions back
                                self.shiftMentions(6, -6)


                            # it's a command
                            elif self.text[0] == ':':
                                command = self.text.split(' ')[1]
                                if command == 'click':
                                    idx = int(self.text.split(" ")[2])

                                    if m.clickable:
                                        url = m.clickable[idx - 1]
                                        if url[:4] != 'http':
                                            url = 'https://' + url

                                        webbrowser.open(
                                            url, new = 2
                                        )

                                        send_msg = False
                                
                                elif command == 'peek':
                                    self.M.peek_hash = code
                                    send_msg = False


                                elif command == 'del':
                                    self.client.unsend(m.uid)
                                    send_msg = False
                                
                                elif command in constants.react_mapping_inv:
                                    react = constants.react_mapping_inv[command]
                                    if self.M.ME in m.reactions and m.reactions[self.M.ME] == react:
                                        react = None

                                    self.client.reactToMessage(m.uid, react)

                                    send_msg = False

            if send_msg:
                # assign mentions
                msg.mentions = [
                    Mention(*m) for m in self.mentions
                ]

                self.client.send(
                    msg,
                    thread_id = self.M.threads[self.M.active_thread].uid,
                    thread_type = self.M.threads[self.M.active_thread].type
                )

            self.prev_text = ''
            self.text = ''
            self.cursor_position = 0

        elif a != -1 and a != 9:        # don't check 9 because it is the tab character and needs special checks for autocompletion
            # send a read notification
            if not self.M.threads[self.M.active_thread].read:
                try:
                    self.client.markAsRead(self.M.threads[self.M.active_thread].uid)
                except FBchatFacebookError:
                    pass
                
                self.M.threads[self.M.active_thread].read = True

            char = str(chr(a))[0]
            self.text = self.text[:self.cursor_position] + char + self.text[self.cursor_position:]

            self.shiftMentions(self.cursor_position, 1)
            self.cursor_position += 1

            self.addstr(2, 0, str(a) + " " + curses.keyname(a).decode() + "      ")
        
        # process the text itself
        if self.text:
            if self.text[0] in ':!':
                # display hash
                self.M.show_hash = True
                self.M.force_update = True
 
            else:
                self.M.show_hash = False
                self.M.force_update = True
            
    def render(self):
        self.rendered_modal = False

        self.addstr(1, 0, "> ")

        self.textDelta()
        self.prev_text = self.text
    
        # draw cursor
        if self.cursor_position != len(self.text):
            self.addch(1, 2 + self.cursor_position, self.text[self.cursor_position], curses.A_REVERSE)
        else:
            self.addch(1, 2 + self.cursor_position, ' ', curses.A_REVERSE)

        # draw the mention autocomplete modal
        try:
            at_index = self.text.rindex("@", 0, self.cursor_position)
        except ValueError:
            at_index = 0
        finally:
            # nicknames is occasionally a list. i assume this is when no one has a nickname so i could technicallyj ust check with if active_thread.nicknames: 
            # this is a safer check tho
            active_thread = self.M.getActiveThread()

            if self.text and self.text[at_index] == '@' and active_thread.type == ThreadType.GROUP and type(active_thread.nicknames) == dict:     # start showing autocomplete for usernames
                at_index_end = self.cursor_position
                partial_mention = self.text[at_index + 1:at_index_end]

                # this will not work for dms because there is no participants field
                
                self.autocomplete_matches = []

                autocomplete_lines = []
                matches_found = 0

                for user in active_thread.participants:
                    name = self.M.user_dict[user].name

                    nickname = active_thread.nicknames.get(user, '-')

                    if matchBeginning(name.lower(), [partial_mention.lower()]):
                        autocomplete_lines += [
                            ["%s - %s" % (name, user), [[0, len(name), curses.color_pair(3)]]],
                            [str(nickname), [[0, len(str(nickname)), curses.color_pair(4)]]],
                            ['']
                        ]

                        self.autocomplete_matches.append((name, user))

                        matches_found += 1

                if autocomplete_lines:
                    #highlight the name the user is focusing on
                    highlight = self.autocomplete_modal_selection % matches_found
                    autocomplete_lines[highlight * 3][1][0][2] |= curses.A_REVERSE     
                                    # line  #ins #first_instruction #style

                    max_autocomplete_length = max([len(l[0]) for l in autocomplete_lines])

                    self.autocomplete_modal.resize(len(autocomplete_lines) + 4, max_autocomplete_length + 6)
                    self.autocomplete_modal.clear()

                    move_y = curses.LINES - 3 - len(autocomplete_lines) - 4 
                    
                    move_x = 2 + at_index

                    if move_y >= 1:
                        self.autocomplete_modal.mvwin(move_y, self.begin_x + move_x)
                        render_lines(self.autocomplete_modal, autocomplete_lines, padding = [2, 0, 0, 3])
                        self.autocomplete_modal.box()

                        self.rendered_modal = True


        # move cursor

    def refresh(self):
        self.window.noutrefresh()

        if self.rendered_modal:
            self.autocomplete_modal.noutrefresh()


class LoginTextBox(Window):
    def __init__(self, stdscr, width, height, begin_y, begin_x, hidden = False):
        super().__init__(stdscr, width, height, begin_y, begin_x)

        self.stdscr = stdscr

        self.cursor_position = 0 
        self.text = ''
        self.prev_text = ''

        self.hidden = hidden

    def textDelta(self):
        """
            both current and previous are arrays of characters. we assume these are single line inputs with no need for wrapping
        """

        # the first thing to do is delete characters at the end if the previous string was longer than the current
        #for i in range (len(self.prev_text) - len(self.text) + 1):
        #    self.window.delch(0, len(self.text) + i - 1)
        
        self.window.clear()

        # now you can safely add str
        if self.hidden:
            self.addstr(0, 0, "*" * len(self.text[:self.width - 1]), curses.color_pair(3))
        else:
            self.addstr(0, 0, self.text[:self.width - 1], curses.color_pair(3))

    def processKey(self, a):
        if a == 8:
            self.window.delch(0, self.cursor_position - 1)
            if self.cursor_position > 0:
                self.text = self.text[:self.cursor_position - 1] + self.text[self.cursor_position:]

            self.cursor_position = max(0, self.cursor_position - 1)
        elif a == curses.KEY_LEFT:
            
            self.cursor_position = max(0, self.cursor_position - 1)

        elif a == curses.KEY_RIGHT:
            
            self.cursor_position = min(len(self.text), self.cursor_position + 1)

        elif a == curses.CTL_LEFT:
            try:
                self.cursor_position -= self.cursor_position - self.text.rindex(" ", 0, self.cursor_position - 1) - 1
            except ValueError:
                self.cursor_position = 0

        elif a == curses.CTL_RIGHT:
            try:
                self.cursor_position += self.text.index(" ", self.cursor_position) - self.cursor_position + 1
            except ValueError:
                self.cursor_position = len(self.text)

        elif a == curses.KEY_SLEFT:
            # move left selection one back
            pass

        elif a == curses.KEY_SRIGHT:
            # move right selection one back
            pass

        elif a == curses.KEY_DC:
            # del key
            self.text = self.text[:self.cursor_position] + self.text[self.cursor_position + 1:]

        elif a == 10:
            # send the text

            pass

        elif a != -1 and 32 <= a <= 127: # has to be a valid ascii character, who tf is making their passwords unicode 
            
            char = str(chr(a))[0]
            self.text = self.text[:self.cursor_position] + char + self.text[self.cursor_position:]

            self.cursor_position += 1
        
    def render(self, cursor = True):
        self.window.clear()
        
        self.textDelta()
        self.prev_text = self.text
    
        # draw cursor
        if self.cursor_position < self.width - 1 and cursor:
            if self.cursor_position != len(self.text):
                self.addch(0, self.cursor_position, self.text[self.cursor_position], curses.A_REVERSE)
            else:
                self.addch(0, self.cursor_position, ' ', curses.A_REVERSE)

        # move cursor

    def refresh(self):
        self.window.refresh()