import curses
from curses import wrapper
from curses.textpad import Textbox
import random
import locale 

from PIL import Image

import base64
import hashlib


def displayImage(window, array, begin_y, begin_x, init_pairs = False, img_idx = 0):
    # target resolution is 4 x 4 characters so 8 x8 resolution
    # the pfps are 60 x 60 in resolution
    # each 

    for y in range (0, 8, 2):
        for x in range (8):
            idx = y * 8 + x
            beneath = (y + 1) * 8 + x

            pixel = array[idx]
            pixel_beneath = array[beneath]

            # rescale the colors
            #curses.COLORS = 10000
            #curses.COLOR_PAIRS = 10000
            #curses.init_color(100 + idx + img_idx * 64, int(pixel[0] * 1000/256), int(pixel[1] * 1000/256), int(pixel[2] * 1000/256))
            #curses.init_color(100 + beneath + img_idx * 64, int(pixel_beneath[0] * 1000/256), int(pixel_beneath[1] * 1000/256), int(pixel_beneath[2] * 1000/256))
            
            #curses.init_pair(100 + idx + img_idx * 64, 100 + idx + img_idx * 64, 100 + beneath + img_idx * 64)

            #window.addch((y + 1)//2 + begin_y, x + begin_x, "▀", curses.color_pair(100 + idx + img_idx * 64))


def displayIdenticon(stdscr, name, begin_y, begin_x):
    colors = [
        -1,
        curses.COLOR_BLUE,
        curses.COLOR_MAGENTA,
        curses.COLOR_GREEN
    ]

    # there are 5 * 5 = 25 color pairs possible
    # we can just do a shitty hash of the color pairs and reconstruct them when we color in

    # the hash is just the foreground color times 7 + background color

    # we need to create each color pair combination
    
    curses.use_default_colors()

    h = hashlib.sha256()
    h.update(name.encode())
    digest = h.digest()

    # identicon is a 4 x 4 image
    hasDrawn = False
    digitOffset = 0
    
    while not hasDrawn:
        for y in range (0, 4, 2):
            for x in range (0, 2):
                digit = y * 4 + x

                # whether it's colored depends on parity
                colored = digest[digit + digitOffset] % 2
                colored_beneath = digest[digit + 4 + digitOffset] % 2 

                # what it's color is depends on its byte divided by 2 mod 4
                color = curses.COLOR_BLACK
                if colored:
                    color = colors[(digest[digit] // 2) % (len(colors) - 1) + 1]

                color_beneath = curses.COLOR_BLACK
                if colored_beneath:
                    color_beneath = colors[(digest[digit] // 2) % (len(colors) - 1)+ 1]

                h = 100 + color * 7 + color_beneath

                if not color and not colored_beneath:
                    continue
                    
                if not color:
                    # top color is default
                    # switch to bottom square
                    curses.init_pair(h, color_beneath, -1)

                    row = digit // 4
                    col = digit % 4
                    stdscr.addstr(y//2 + begin_y, x + begin_x, "▄", curses.color_pair(h))
                    stdscr.addstr(y//2 + begin_y, (4 - x) + begin_x - 1, "▄", curses.color_pair(h))

                    hasDrawn = True
                    continue;

                elif not colored_beneath:
                    colored_beneath = -1
                    
                curses.init_pair(h, color, color_beneath)

                row = digit // 4
                col = digit % 4
                stdscr.addstr(y//2 + begin_y, x + begin_x, "▀", curses.color_pair(h))
                stdscr.addstr(y//2 + begin_y, (4 - x) + begin_x - 1, "▀", curses.color_pair(h))

                hasDrawn = True

        digitOffset += 16

def matchBeginning(string, l):
    for s in l:
        if string[:len(s)] == s:
            return True


def produceHash(msg):
    h = hashlib.new('md5')
    h.update(str(msg.timestamp).encode())
    code = base64.b32encode(h.digest()).decode().lower()

    return code

def ellipses(window, text, padding = 0):
    mwidth = window.getmaxyx()[1] - padding

    if len(text) > mwidth - 3:
        text = text[:mwidth - 3] + '...'

    return text

# padding is top right left bottom
def render_lines(window, lines, padding = [0, 0, 0, 0], default_color = None, align = "<"):
    # lines are given as a series of instructions
    # instructions are in the format: 
    # start, end, attributes

    # the start and end denote indices of the string, and should be non-intersecting and sorted from least start to greatest start index

    # all lines should already be wrapped, and therefore should not exceed the width of the window with padding
    # the only reason why there is right padding is for alignment, NOT to handle wrapping for you

    current_line = padding[0]

    mheight, mwidth = window.getmaxyx()

    begin_y = padding[0]

    if begin_y < 0:
        return

    for line in lines[:mheight - 2]:
        current_x = padding[3]
        current_text_pointer = 0

        if line:
            if len(line) == 1:      # it's just text, then you can just addstr
                line.append([])


            instruction = [0, 0, 0]     # this is a default instruction in case therei s an alignment instruction

            if line[1] and type(line[1][0]) == str:
                alignment = '>'
            else:
                alignment = align

            if align:
                alignment = align 

            if alignment == ">":
                # set the current_x to mwidth - padding[1] (right) - len(line[0])
                current_x = mwidth - 2 - padding[1] - len(line[0])


            for instruction in line[1]:
                if type(instruction) == str:
                    continue;

                # add normal text that comes before the instruction
                
                # when inserting default_color, the begin_

                if default_color:
                    window.addstr(current_line, current_x, line[0][current_text_pointer:instruction[0]], default_color)
                else:                    
                    window.addstr(current_line, current_x, line[0][current_text_pointer:instruction[0]])

                current_x += instruction[0] - current_text_pointer   
                current_text_pointer = instruction[0] 

                # insert the altered text
                window.addstr(current_line, current_x, line[0][instruction[0] : instruction[1]], instruction[2])
                
                current_x += instruction[1] - instruction[0]
                current_text_pointer = instruction[1]

            # add text at the end
            if default_color:
                window.addstr(current_line, current_x, line[0][instruction[1]:], default_color)
            else:
                window.addstr(current_line, current_x, line[0][instruction[1]:])

            current_line += 1

        else:
            current_line += 1            

def wrapLine(line, max_length):

    # wrap each line according to the max_length
    # this is done by inserting newline characters (\n) into the plaintext string
    wrapped_lines = []

    if len(line[0]) > max_length:
        length = len(line[0])
        for i in range (length // max_length):
            line[0] = line[0][:(i + 1) * max_length + i] + '\n' + line[0][(i + 1) * max_length + i:]
    else:
        wrapped_lines.append(line)

    # once the newlines are added, split by newline
    split = line[0].split("\n")
    
    wrapped_lines_ret = []
    current_x = 0 
    current_instruction = 0
    done = False

    instruction = line[1]

    for s in split:
        end = len(s) + current_x
        start = current_x

        wrapped_lines_ret.append([s, []])

        if not done:
            if current_instruction == len(instruction):
                done = True
                continue

            while start >= instruction[current_instruction][1]:
                current_instruction += 1
                if (current_instruction == len(instruction)):
                    current_instruction -= 1
                    done = True
                    break;

            if done: continue

            # chunk entirely engulfs this instruction
            # we can probably make this more concise with max and min

            while end >= instruction[current_instruction][1] - 1 and start <= instruction[current_instruction][0]:
                wrapped_lines_ret[-1][1].append([instruction[current_instruction][0] - start, instruction[current_instruction][1] - start, instruction[current_instruction][2]])
                current_instruction += 1

                if (current_instruction == len(instruction)):
                    current_instruction -= 1
                    done = True
                    break;
            
            if done: continue

            if end >= instruction[current_instruction][1] - 1 and start >= instruction[current_instruction][0] and start <= instruction[current_instruction][1] - 1:
                wrapped_lines_ret[-1][1].append([0, instruction[current_instruction][1] - start, instruction[current_instruction][2]])
                current_instruction += 1 

            elif end < instruction[current_instruction][1] and end > instruction[current_instruction][0] and start <= instruction[current_instruction][0]:

                wrapped_lines_ret[-1][1].append([instruction[current_instruction][0] - start, end - start, instruction[current_instruction][2]])

            elif end < instruction[current_instruction][1] and start >= instruction[current_instruction][0]:

                wrapped_lines_ret[-1][1].append([0, end - start, instruction[current_instruction][2]])
            
            if current_instruction == len(instruction):
                done = True
    
        current_x += len(s)
        
    return wrapped_lines_ret

if __name__ == "__main__":
    print(wrapLine(
        ["hello world i am trying to wrap this line this is a very long, line, yes, current_instruction", [(0, 20, 1), (21, 25, 2), (30, 34, 3)]]
    , 21))