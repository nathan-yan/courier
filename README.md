<img src="https://github.com/nathan-yan/courier/raw/master/images/logo.png" alt="courier logo" width="300"/>

Courier is a command line interface for Facebook's Messenger. Courier is meant to be a _typing only_ alternative to messenger that is also easily accessible (from terminal!) and runs with very few resources. The application is based on the curses library and uses the unofficial FBChat API (https://github.com/carpedm20/fbchat/) to query and send messages.

<img src="https://github.com/nathan-yan/courier/raw/master/images/preview.jpg" alt="courier preview"/>

## How to run
To start Courier run `pip install -r requirements.txt` and then `python messenger.py`. You will be asked to login if it is your first time. Cookies will be stored in a file named `cookies.json`. If your cookies file ever becomes corrupted or lost, you will just be asked to login with username and password again.

I highly recommend using the Fira Code font (https://github.com/tonsky/FiraCode) with Courier, because there is some text in Courier that can take advantage of font ligatures.

## How to use
Courier tries its best to reconcile the look and feel of messenger with the terminal environment. Low resolution identicons of threads are displayed to aid with thread identification, which mimic profile pictures; messages are boxed to mimic message bubbles. However many things are different by necessity, and take some getting used to. If you're fast at typing using Courier can be a much more fluid and quick experience than using the point and click of regular messenger.

### Addressing messages
Courier addresses its messages using a 4 digit code based on the hash of its timestamp. This is how you pick messages to reply, react, delete etc. To reply to a message type 
```@[messagecode] [your reply text]```
You'll notice that once you type the @ symbol yellow codes will pop up to the sides of the messages.

To react to a message type `:[messagecode] [love/haha/grr/sad/yes/no]`. Changing a react is just typing the same command with a different react--using the same react will remove it. Reacts will be shown next to the message. 

If you want to see when a message was sent, or who reacted/read a message, you can use the peek command by typing `:[messagecode] peek`. A small box will appear next to the message containing all the message information.

### Threads
Threads in Courier have a small 4x4 identicon generated from a hash of the thread_id. They're just there to help you quickly identify which thread is which. The thread you're currently in will have reverse video text on its name. Unread threads will have green colored text in the message preview. 

To switch to a different thread type `:s [threadnumber]`
