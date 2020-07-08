
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

import constants

from fbchat import Client
from fbchat.models import *

from utils import *
from window import Window

class Modal(Window):
    def __init__(self, stdscr, height, width, begin_y, begin_x):
        super().__init__(self, stdscr, height, width, begin_y, begin_x)

    def render(self):
        # add a rectangular border
        self.window.box()
        
