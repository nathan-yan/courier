<img src="https://github.com/nathan-yan/courier/raw/master/images/logo.png" alt="courier logo" width="300"/>

*The unofficial Messenger API library this project uses, FBChat, no longer works/requires tweaking to work properly, so this project likely will break for you (typically at the login stage). If you'd like to try to get Courier to work again with FBChat or some alternative API, I would love to see it!*

*This currently only works for WINDOWS machines! I am working on getting this to display properly on Linux/MacOS*

Courier is a command line interface for Facebook's Messenger. Courier is meant to be a _typing only_ alternative to messenger that is also easily accessible (from terminal!) and runs with very few resources. The application is based on the curses library and uses the unofficial FBChat API (https://github.com/carpedm20/fbchat/) to query and send messages.

<img src="https://github.com/nathan-yan/courier/raw/master/images/preview.jpg" alt="courier preview"/>

## How to run
To start Courier run `pip install -r requirements.txt` and then `python messenger.py`. You will be asked to login if it is your first time. Cookies will be stored in a file named `cookies.json`. If your cookies file ever becomes corrupted or lost, you will just be asked to login with username and password again.

I highly recommend using the Fira Code font (https://github.com/tonsky/FiraCode) with Courier, because there is some text in Courier that can take advantage of font ligatures. For the best experience I'd also recommend using a terminal emulator that supports unicode character display and 256 colors. <br><br>

## How to use
Courier tries its best to reconcile the look and feel of messenger with the terminal environment. Low resolution identicons of threads are displayed to aid with thread identification, which mimic profile pictures; messages are boxed to mimic message bubbles. However many things are different by necessity, and take some getting used to. If you're fast at typing using Courier can be a much more fluid and quick experience than using the point and click of regular messenger. <br><br>


### Addressing messages
Courier addresses its messages using a 4 digit code based on the hash of its timestamp. This is how you pick messages to reply, react, delete etc. 

* To reply to a message type `![message_code] [reply_text]`. You'll notice that once you type the ! symbol yellow codes will pop up to the sides of the messages.

* To react to a message type `:[message_code] [love/haha/grr/sad/yes/no]`. Changing a react is just typing the same command with a different react--using the same react will remove it. Reacts will be shown next to the message. 

* If you want to see when a message was sent, or who reacted/read a message, you can use the peek command by typing `:[message_code] peek`. A small box will appear next to the message containing all the message information. <br><br>


### Threads
Threads in Courier have a small 4x4 identicon, as well as a 3 digit code generated from a hash of the thread_id. They're just there to help you quickly identify which thread is which. The thread you're currently in will have reverse video text on its name. Unread threads will have green colored text in the message preview. 

* To switch to a different thread type `:s [thread_code]`.

* The 3 digit codes can be tricky to memorize, so if you have threads you chat often in you can pin them to more easily memorizable names with `:pin [new_code]` inside your active thread. THese pins are written into the settings.json so are persistent across app restarts. You can unpin a thread with `:unpin` inside the active thread.

* You can also search for threads with `:s [-u/-t] [name]`, where `-u` is to search for users and `-t` is to search for groups/threads. As a warning, searching is currently somewhat buggy and may cause errors. <br><br>


### Scrolling
To scroll up or down in a chat use either ctrl-i/ctrl-k for up and down, or use the up and down arrows. To scroll up or down in the thread window, use ctrl-up or ctrl-down. 

**WARNING: Scrolling in threads is very slow (on the order of 5-10 seconds) because you have to load new threads and make a separate request to fetch messages for each thread. Because of this, it's recommended you use the search switch function described in the "Threads" section.**<br><br>


### "Clicking"
Since the terminal cannot display images, attachements/images/videos are displayed as text with a number beside them. You can "click" and view them in a real browser like Chrome with `:[message_code] click [attachement_number]`<br><br>


### Mentioning
To mention someone type the @ symbol and begin typing a name. Autocomplete results will show up in a box above, use the up and down keys to select the name you'd like to mention. Once you've reached the correct selection press `tab` to autocomplete and create the mention. Mentions will be highlighted in magenta.

