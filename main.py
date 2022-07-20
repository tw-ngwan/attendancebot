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
id, parent_id, Name, Date Added, Group Code, Observer Password, Member Password, Admin Password
Table 2: users
id, group_id, Name, Date Added, chat_id (if relevant), role -> (Observer, Member, or Admin)
Table 3: attendance
id, time period (morning, afternoon), datetime, user_id, status

Do I need one more table to track users? Or no?
Maybe a chat_id table that links chat_id to user_ids?
Or maybe some table that just contains user's names and id

Question: How do you join a group that already exists?
Using group_id

Delete state_variables.py

These are the following roles of people in each group:
Head Admin: Typically creator. Can pass role to someone else. (Is this needed?)
Admin: Has admin privileges.
Member: Name is inside the name list. Has some privileges.
Observer: Apart from viewing attendance, has no privileges
*Even more below?

"""


import os
import sqlite3
import settings
from entry_help_functions import start, user_help
from entry_group_functions import create_group, enter_group, leave_group, current_group, delete_group, merge_groups, \
    join_group_members, join_existing_group, quit_group, change_group_title
from state_group_functions import name_group_title, enter_group_implementation
from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters

# from entry_functions import start, update_preferences, update_news, update_timing, user_help, exit_function, quit_bot
# from state_variables import *
# from state_functions import get_news_sources, get_num_articles, get_frequency, get_news_sources_specific


API_KEY = os.getenv("ATTENDANCE_TELEGRAM_API")

# Letting Telegram know which bot to run code on
updater = Updater(API_KEY)
dispatcher = updater.dispatcher

# Checking that all libraries have been loaded, function can start
print("Bot starting...")

# Initialize all global variables
settings.init()

commands = ['start', 'help',
            'creategroup', 'entergroup', 'leavegroup', 'currentgroup', 'deletegroup', 'mergegroups',
            'joingroupmembers', 'joinexistinggroup', 'quitexistinggroup', 'changegrouptitle'
            'addusers', 'removeusers', 'editusers', 'becomeadmin', 'getadmins', 'dismissadmins'
            'editsettings', 'changeattendance', 'changemyattendance', 'getgroupattendance', 'getuserattendance',
            'getallattendance', 'backdatechangeattendance'
            'stop']

implemented_commands = ['entergroup', 'currentgroup']

fully_implemented_commands = ['start', 'help',
                              'creategroup']

help_message = """
Here is a walkthrough of what each of the functions will do: 
/start: Once you activate the bot, it will send you the attendance statuses of each group you're in every day. 
/help: Gives you the list of commands available and explains the concept of "groups" and "subgroups"

/creategroup: Creates a group within your current group 
/entergroup: Enters group to do stuff in the group
/leavegroup: Leaves group you are currently in after you finish doing stuff 
/currentgroup: Returns the current group you are in, and None if not 
/deletegroup: Deletes the group. Needs Admin privileges, and prompt to do so
/mergegroups: Merges two groups together, with one becoming the parent group, and the other its child
/joingroupmembers: Joins the members of two groups together, under a new name
/joinexistinggroup: Joins a group that already exists, using its group id. 
/quitgroup: Quits and exits your group. Do NOT confuse with leavegroup! 
/changegrouptitle: Changes group title. Admin privileges required. 

/addusers: Adds users to the group you are currently in (/entergroup). Recursive, till enter OK
/removeusers: Removes users from the group you are currently in. Recursive, till enter OK 
/editusers: Changes the names and details of the user 
/becomeadmin: Enter a password to become group admin 
/getadmins: Returns a list of all admin users. 
/dismissadmins: Dismisses an admin user. 

/editsettings: Edits settings. To be elaborated
/changeattendance: Changes the attendance status of any group members of group you are currently in (Admin?)
/changemyattendance: Changes your attendance 
/getgroupattendance: Returns the attendance status of all group members on that day 
/getuserattendance: Returns the attendance status of a user over a period of time (user-defined)
/getallattendance: Returns the attendance status of all group members over a period of time
/backdatechangeattendance: Changes the attendance of a user, backdated. Admin Privileges required. 

/stop: Stops the bot from running. 

Functions to finish first: 
/creategroup 
/entergroup
/leavegroup 
/currentgroup 
/deletegroup 

/addusers
/removeusers
/editusers

/changeattendance
/getgroupattendance
/getuserattendance
"""

"Schedule message: https://stackoverflow.com/questions/48288124/how-to-send-message-in-specific-time-telegrambot"
"If you need to remake a table: "
"https://stackoverflow.com/questions/631060/can-i-alter-a-column-in-an-sqlite-table-to-autoincrement-after-creation"


# Main function
def main():

    # Introducing the necessary conversation handlers

    # Start/help functions
    start_handler = ConversationHandler(entry_points=[CommandHandler('start', start)], states={}, fallbacks=[])
    help_handler = ConversationHandler(entry_points=[CommandHandler('help', user_help)], states={}, fallbacks=[])

    # Group functions
    create_group_handler = ConversationHandler(
        entry_points=[CommandHandler('creategroup', create_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, name_group_title)],
        },
        fallbacks=[]
    )
    enter_group_handler = ConversationHandler(
        entry_points=[CommandHandler('entergroup', enter_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, enter_group_implementation)],
        },
        fallbacks=[]
    )
    leave_group_handler = ConversationHandler(entry_points=[CommandHandler('leavegroup', leave_group)],
                                              states={}, fallbacks=[])
    current_group_handler = ConversationHandler(entry_points=[CommandHandler('currentgroup', current_group)],
                                                states={}, fallbacks=[])
    delete_group_handler = ConversationHandler(
        entry_points=[CommandHandler('deletegroup', delete_group)],
        states={

        },
        fallbacks=[]
    )
    merge_groups_handler = ConversationHandler(
        entry_points=[CommandHandler('mergegroups', merge_groups)],
        states={

        },
        fallbacks=[]
    )
    join_members_handler = ConversationHandler(
        entry_points=[CommandHandler('joingroupmembers', join_group_members)],
        states={

        },
        fallbacks=[]
    )
    join_groups_handler = ConversationHandler(
        entry_points=[CommandHandler('joinexistinggroup', join_existing_group)],
        states={

        },
        fallbacks=[]
    )
    quit_group_handler = ConversationHandler(
        entry_points=[CommandHandler('quitgroup', quit_group)],
        states={

        },
        fallbacks=[]
    )
    change_group_title_handler = ConversationHandler(
        entry_points=[CommandHandler('changegrouptitle', change_group_title)],
        states={

        },
        fallbacks=[]
    )

    global dispatcher
    all_handlers = [start_handler, help_handler,
                    create_group_handler, enter_group_handler, leave_group_handler, current_group_handler,
                    delete_group_handler, merge_groups_handler, join_members_handler, join_groups_handler,
                    quit_group_handler, change_group_title_handler]
    for handler in all_handlers:
        dispatcher.add_handler(handler)

    updater.start_polling()

    updater.idle()







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
