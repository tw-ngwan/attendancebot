"""
This code is copied from NewsBot

Here's the functionality that you want the bot to have first
First, SQLite for storage

Here's how the bot will work:

To start tracking attendance, you first need to create a group.
You can continue creating subgroups for each group (or each subgroup). Groups' relations are stored as trees (dj sets),
with each group's parent group stored (if no parent, stored as 0).
For each subgroup/group, you can add participants to the group.
To add a participant, send a message with his name and ORD date (?)
If you typoed and want to resend something, work on this.
If you send a message that says end, then it stores everything.

Need to generate the attendance, and store the attendance status of people.

SQL admin:
Need to create 3 tables
Table 1: groups
id, parent_id, Name, Date Added, Group Code, Password
Table 2: users
id, group_id, Name, ORD Date (?), Date Added, chat_id (if relevant)
Table 3: attendance
id, time period (morning, afternoon), datetime, user_id, status

Do I need one more table to track users? Or no?
Maybe a chat_id table that links chat_id to user_ids?
Or maybe some table that just contains user's names and id

Question: How do you join a group that already exists?
Using group_id

Delete state_variables

"""


import os
import sqlite3
import settings
# from entry_functions import start, update_preferences, update_news, update_timing, user_help, exit_function, quit_bot
# from state_variables import *
# from state_functions import get_news_sources, get_num_articles, get_frequency, get_news_sources_specific
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters


API_KEY = os.getenv("ATTENDANCE_TELEGRAM_API")

# Letting Telegram know which bot to run code on
updater = Updater(API_KEY)
dispatcher = updater.dispatcher

# Checking that all libraries have been loaded, function can start
print("Bot starting...")

# Initialize all global variables
settings.init()

commands = ['start', 'help', 'tutorial',
            'creategroup', 'entergroup', 'leavegroup', 'currentgroup', 'deletegroup', 'mergegroups',
            'joingroupmembers', 'joinexistinggroup', 'quitexistinggroup'
            'addusers', 'removeusers', 'editusers', 'becomeadmin', 'getadmins', 'dismissadmins'
            'editsettings', 'changeattendance', 'changemyattendance', 'getgroupattendance', 'getuserattendance',
            'getallattendance', 'backdatechangeattendance'
            'stop']

help_message = """
Here is a walkthrough of what each of the functions will do: 
/start: Once you activate the bot, it will send you the attendance statuses of each group you're in every day. 
/help: Gives you the list of commands available and explains the concept of "groups" and "subgroups"

/creategroup: Creates a group within your current group 
/entergroup: Enters group to do stuff in the group
/leavegroup: Leaves group you are currently in, goes one level up. 
/currentgroup: Returns the current group you are in, and None if not 
/deletegroup: Deletes the group. Needs Admin privileges, and prompt to do so
/mergegroups: Merges two groups together, with one becoming the parent group, and the other its child
/joingroupmembers: Joins the members of two groups together, under a new name
/joinexistinggroup: Joins a group that already exists, using its group id. 
/quitexistinggroup: Quits a group you are currently in. 

/addusers: Adds users to the group you are currently in (/entergroup). Recursive, till enter OK
/removeusers: Removes users from the group you are currently in. Recursive, till enter OK 
/editusers: Changes the names and details of the user 
/becomeadmin: Enter a password to become group admin 
/getadmins: Returns a list of all admin users. 
/dismissadmins: Dismisses an admin user. Can only be done with Head Admin Privileges. 

/editsettings: Edits settings. To be elaborated
/changeattendance: Changes the attendance status of any group members of group you are currently in (Admin?)
/changemyattendance: Changes your attendance 
/getgroupattendance: Returns the attendance status of all group members on that day 
/getuserattendance: Returns the attendance status of a user over a period of time (user-defined)
/getallattendance: Returns the attendance status of all group members over a period of time
/backdatechangeattendance: Changes the attendance of a user, backdated. Admin Privileges required. 

/stop: Stops the bot from running. 
"""

"Schedule message: https://stackoverflow.com/questions/48288124/how-to-send-message-in-specific-time-telegrambot"


# Main function
def main():

    # # Introducing the necessary conversation handlers
    # # Start handler handles update, timings_update as well
    # start_handler = ConversationHandler(
    #     entry_points=[CommandHandler('start', start), CommandHandler('update', update_preferences),
    #                   CommandHandler('updatetiming', update_timing)],
    #     states={
    #         FIRST: [MessageHandler(Filters.text, get_news_sources)],
    #         SECOND: [MessageHandler(Filters.text, get_num_articles)],
    #         THIRD: [MessageHandler(Filters.text, get_frequency)],
    #
    #     },
    #     fallbacks=[]
    # )
    # news_update_handler = ConversationHandler(
    #     entry_points=[CommandHandler('updatenews', update_news)],
    #     states={
    #         FIRST: [MessageHandler(Filters.text, get_news_sources_specific)]
    #     },
    #     fallbacks=[])
    # help_handler = ConversationHandler(entry_points=[CommandHandler('help', user_help)], states={}, fallbacks=[])
    # exit_handler = ConversationHandler(entry_points=[CommandHandler('exit', exit_function)], states={}, fallbacks=[])
    # quit_handler = ConversationHandler(entry_points=[CommandHandler('quit', quit_bot)], states={}, fallbacks=[])
    #
    # # Adds the conversation handlers to the dispatchers
    # global dispatcher
    # dispatcher.add_handler(start_handler)
    # dispatcher.add_handler(news_update_handler)
    # dispatcher.add_handler(help_handler)
    # dispatcher.add_handler(exit_handler)
    # dispatcher.add_handler(quit_handler)
    #
    # updater.start_polling()
    #
    # updater.idle()
    pass


if __name__ == "__main__":
    main()
