<img src="https://github.com/nathan-yan/courier/raw/master/images/logo.png" alt="courier logo" width="300"/>

**courier** is a command line interface for Facebook's Messenger. **courier** is meant to be a _typing only_ alternative to messenger that is also easily accessible (from terminal!) and runs with very few resources. The application is based on the curses library, and uses CarpEDM20's FBChat API to query and send messages.

## How to run
To start **courier** simply do `pip install -r requirements.txt` and then `python messenger.py`. You will be asked to login if it is your first time. Cookies will be stored in a file named `cookies.json`. If your cookies file ever becomes corrupted or lost, you will just be asked to login with username and password again.
