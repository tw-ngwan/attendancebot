"""
#TODO
May want to add encryption.

Bot Description:
This attendance bot tracks attendance of groups, of which each group contains users. Each group can be the subgroup
of other groups, and  the parent of other groups, so this implementation allows for the nesting necessary for there
to be layers of groups on top of each other.
Each group can be managed by users, of which there are three priority tiers: Observers, Members, and Admins, of which
Admins get the full functionality of the bot, and Observers only basic functions. This is to ensure that the
attendance of groups cannot be tampered with unnecessarily.

People using the bot can either create a group, or join the necessary group that has already been created (using a group
code and password). To call a function on a group, they must use /enter to enter the group first.

Technical implementation of the bot:
Data is stored in SQLite in 4 tables: Groups, Users, Attendance, and Admins. Groups stores the groups that are created,
Users stores all the names of all the people in each group, Attendance stores the daily attendance of each user, and
Admins stores the chat_ids and data of all the people who use the bot (regardless of their tier).
Whenever users call a function to change the attendance or get the attendance, the relevant attendance status is stored
in the Attendance Table of SQLite, so that it can be called back when needed. Similarly, whenever groups / users are
added or deleted, the relevant tables are called.
When the attendance of a group is called, it will call recursively for the attendance of all subgroups as well.
However, if you want to change the attendance of a subgroup of a group, you need to enter that group first.

There are functions for editing, merging groups, and transferring users between groups if those are needed.
"""


import os

from telegram.ext import Updater, ConversationHandler, CommandHandler, MessageHandler, Filters

import settings
from entry_attendance_functions import get_today_group_attendance, get_tomorrow_group_attendance, \
    get_any_day_group_attendance, change_attendance, change_any_day_attendance, \
    get_user_attendance_month, get_user_attendance_arbitrary, \
    get_all_users_attendance_month, get_all_users_attendance_arbitrary
from entry_group_functions import create_group, enter_group, leave_group, current_group, delete_group, merge_groups, \
    join_existing_group, quit_group, change_group_title, uprank, get_group_passwords, set_username_precursor, \
    get_group_history
from entry_help_functions import start, user_help, user_help_full
from entry_user_functions import add_users, get_users, remove_users, edit_users, change_group_ordering, \
    change_user_group
from state_attendance_functions import change_today_attendance_follow_up, change_tomorrow_attendance_follow_up, \
    change_any_day_attendance_get_day, change_any_day_attendance_follow_up, \
    get_specific_day_group_attendance_follow_up, get_user_attendance_month_follow_up, \
    get_user_attendance_arbitrary_follow_up, \
    get_all_users_attendance_month_follow_up, get_all_users_attendance_arbitrary_follow_up
from state_group_functions import create_group_follow_up, enter_group_follow_up, delete_group_follow_up, \
    join_group_get_group_code, join_group_follow_up, quit_group_follow_up, change_group_title_follow_up, \
    uprank_follow_up, merge_groups_check_super_group, merge_groups_start_add_users, merge_groups_follow_up, set_username
from state_user_functions import add_user_follow_up, remove_user_verification, remove_user_follow_up, \
    edit_user_follow_up, change_group_ordering_follow_up, change_user_group_get_initial, change_user_group_get_final, \
    change_user_group_follow_up


# Getting the API_KEY
API_KEY = os.getenv("API_KEY_TELEGRAM")

# Letting Telegram know which bot to run code on
updater = Updater(API_KEY)
dispatcher = updater.dispatcher

# Checking that all libraries have been loaded, function can start
print("Bot starting...")

# Initialize all global variables
settings.init()

"Schedule message: https://stackoverflow.com/questions/48288124/how-to-send-message-in-specific-time-telegrambot"
"If you need to remake a table: "
"https://stackoverflow.com/questions/631060/can-i-alter-a-column-in-an-sqlite-table-to-autoincrement-after-creation"


# Main function
def main():

    # Introducing the necessary conversation handlers

    # Start/help functions
    start_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, pass_job_queue=True)], states={}, fallbacks=[]
    )
    help_handler = ConversationHandler(entry_points=[CommandHandler('help', user_help)], states={}, fallbacks=[])
    help_full_handler = ConversationHandler(entry_points=[CommandHandler('helpfull', user_help_full)],
                                            states={}, fallbacks=[])

    # Group functions
    create_group_handler = ConversationHandler(
        entry_points=[CommandHandler('creategroup', create_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, create_group_follow_up)],
            settings.SECOND: [MessageHandler(Filters.text, set_username)]
        },
        fallbacks=[]
    )
    enter_group_handler = ConversationHandler(
        entry_points=[CommandHandler('enter', enter_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, enter_group_follow_up)],
        },
        fallbacks=[]
    )
    leave_group_handler = ConversationHandler(entry_points=[CommandHandler('leave', leave_group)],
                                              states={}, fallbacks=[])
    current_group_handler = ConversationHandler(entry_points=[CommandHandler('current', current_group)],
                                                states={}, fallbacks=[])
    delete_group_handler = ConversationHandler(
        entry_points=[CommandHandler('deletegroup', delete_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, delete_group_follow_up)]
        },
        fallbacks=[]
    )
    merge_groups_handler = ConversationHandler(
        entry_points=[CommandHandler('mergegroups', merge_groups)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, merge_groups_check_super_group)],
            settings.SECOND: [MessageHandler(Filters.text, merge_groups_start_add_users)],
            settings.THIRD: [MessageHandler(Filters.text, merge_groups_follow_up)]
        },
        fallbacks=[]
    )
    join_groups_handler = ConversationHandler(
        entry_points=[CommandHandler('joingroup', join_existing_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, join_group_get_group_code)],
            settings.SECOND: [MessageHandler(Filters.text, join_group_follow_up)],
            settings.THIRD: [MessageHandler(Filters.text, set_username)]
        },
        fallbacks=[]
    )
    quit_group_handler = ConversationHandler(
        entry_points=[CommandHandler('quitgroup', quit_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, quit_group_follow_up)]
        },
        fallbacks=[]
    )
    change_group_title_handler = ConversationHandler(
        entry_points=[CommandHandler('changetitle', change_group_title)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, change_group_title_follow_up)]
        },
        fallbacks=[]
    )
    get_group_passwords_handler = ConversationHandler(
        entry_points=[CommandHandler('getgroupcodes', get_group_passwords)],
        states={},
        fallbacks=[]
    )
    uprank_handler = ConversationHandler(
        entry_points=[CommandHandler('uprank', uprank)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, uprank_follow_up)]
        },
        fallbacks=[]
    )
    set_username_handler = ConversationHandler(
        entry_points=[CommandHandler('setusername', set_username_precursor)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, set_username)]
        },
        fallbacks=[]
    )
    get_group_history_handler = ConversationHandler(
        entry_points=[CommandHandler('getgrouphistory', get_group_history)],
        states={},
        fallbacks=[]
    )

    # User functions
    add_users_handler = ConversationHandler(
        entry_points=[CommandHandler('addusers', add_users)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, add_user_follow_up)]
        },
        fallbacks=[]
    )
    get_users_handler = ConversationHandler(
        entry_points=[CommandHandler('getusers', get_users)], states={}, fallbacks=[]
    )
    remove_users_handler = ConversationHandler(
        entry_points=[CommandHandler('removeusers', remove_users)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, remove_user_verification)],
            settings.SECOND: [MessageHandler(Filters.text, remove_user_follow_up)]
        },
        fallbacks=[]
    )
    edit_users_handler = ConversationHandler(
        entry_points=[CommandHandler('editusers', edit_users)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, edit_user_follow_up)]
        },
        fallbacks=[]
    )
    change_group_ordering_handler = ConversationHandler(
        entry_points=[CommandHandler('changeordering', change_group_ordering)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, change_group_ordering_follow_up)]
        },
        fallbacks=[]
    )
    change_group_users_handler = ConversationHandler(
        entry_points=[CommandHandler('changeusergroup', change_user_group)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, change_user_group_get_initial)],
            settings.SECOND: [MessageHandler(Filters.text, change_user_group_get_final)],
            settings.THIRD: [MessageHandler(Filters.text, change_user_group_follow_up)]
        },
        fallbacks=[]
    )

    # Attendance functions
    get_today_attendance_handler = ConversationHandler(
        entry_points=[CommandHandler('get', get_today_group_attendance)], states={}, fallbacks=[]
    )
    get_tomorrow_attendance_handler = ConversationHandler(
        entry_points=[CommandHandler('gettmr', get_tomorrow_group_attendance)], states={}, fallbacks=[]
    )
    get_any_day_attendance_handler = ConversationHandler(
        entry_points=[CommandHandler('getany', get_any_day_group_attendance)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, get_specific_day_group_attendance_follow_up)]
        },
        fallbacks=[]
    )
    get_user_attendance_month_handler = ConversationHandler(
        entry_points=[CommandHandler('getusermonth', get_user_attendance_month)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, get_user_attendance_month_follow_up)]
        },
        fallbacks=[]
    )
    get_user_attendance_arbitrary_handler = ConversationHandler(
        entry_points=[CommandHandler('getuserany', get_user_attendance_arbitrary)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, get_user_attendance_arbitrary_follow_up)]
        },
        fallbacks=[]
    )
    get_all_users_attendance_month_handler = ConversationHandler(
        entry_points=[CommandHandler('getallusersmonth', get_all_users_attendance_month)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, get_all_users_attendance_month_follow_up)]
        },
        fallbacks=[]
    )
    get_all_users_attendance_arbitrary_handler = ConversationHandler(
        entry_points=[CommandHandler('getallusersany', get_all_users_attendance_arbitrary)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, get_all_users_attendance_arbitrary_follow_up)]
        },
        fallbacks=[]
    )
    change_today_attendance_handler = ConversationHandler(
        entry_points=[CommandHandler('change', change_attendance)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, change_today_attendance_follow_up)]
        },
        fallbacks=[]
    )
    change_tomorrow_attendance_handler = ConversationHandler(
        entry_points=[CommandHandler('changetmr', change_attendance)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, change_tomorrow_attendance_follow_up)]
        },
        fallbacks=[]
    )
    change_any_day_attendance_handler = ConversationHandler(
        entry_points=[CommandHandler('changeany', change_any_day_attendance)],
        states={
            settings.FIRST: [MessageHandler(Filters.text, change_any_day_attendance_get_day)],
            settings.SECOND: [MessageHandler(Filters.text, change_any_day_attendance_follow_up)]
        },
        fallbacks=[]
    )

    global dispatcher
    all_handlers = [start_handler, help_handler, help_full_handler,
                    create_group_handler, enter_group_handler, leave_group_handler, current_group_handler,
                    delete_group_handler, merge_groups_handler, join_groups_handler, quit_group_handler,
                    change_group_title_handler, get_group_passwords_handler, uprank_handler, set_username_handler,
                    get_group_history_handler,

                    add_users_handler, get_users_handler, remove_users_handler, edit_users_handler,
                    change_group_ordering_handler, change_group_users_handler,

                    get_today_attendance_handler, get_tomorrow_attendance_handler, get_any_day_attendance_handler,
                    get_user_attendance_month_handler, get_user_attendance_arbitrary_handler,
                    get_all_users_attendance_month_handler, get_all_users_attendance_arbitrary_handler,
                    change_today_attendance_handler, change_tomorrow_attendance_handler,
                    change_any_day_attendance_handler
                    ]

    for handler in all_handlers:
        dispatcher.add_handler(handler)

    # Start the bot, let it wait for a user command
    updater.start_polling()
    # This allows it to use a webhook to retrieve data immediately
    # updater.start_webhook(listen="0.0.0.0",
    #                       port=int(PORT),
    #                       url_path=API_KEY)
    # updater.bot.set_webhook(f'https://attendance-6bot.herokuapp.com/{API_KEY}')

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == "__main__":
    main()
