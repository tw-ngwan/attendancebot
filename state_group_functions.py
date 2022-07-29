"""
This file contains a few functions that changes the state of the object. Functions will be used by main

"""

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
import settings
from keyboards import group_name_keyboards
from backend_implementations import generate_random_password, generate_random_group_code, \
    get_admin_reply, get_admin_groups
import sqlite3


# # Gets the number of daily updates for attendance wanted
# def get_num_daily_updates(update_obj: Update, context: CallbackContext) -> int:
#     chat_id, title = get_admin_reply(update_obj, context)
#     if title == "OK":
#         update_obj.message.reply_text("Ok, quitting function now")


# Gets new group title
# TO BE ADDED: Get an option for user to toggle number of daily reports they want, from 1-4
def name_group_title(update_obj: Update, context: CallbackContext) -> int:
    chat_id, title = get_admin_reply(update_obj, context)
    if title == "OK":
        update_obj.message.reply_text("Ok, quitting function now")
        return ConversationHandler.END
    # SQLite Execution: To store the group and the new user
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        current_group = settings.current_group_id
        group_code = generate_random_group_code()
        observer_password, member_password, admin_password = generate_random_password(iterations=3)
        # Stores the group in SQLite
        if current_group is None:
            cur.execute(
                """
                INSERT INTO groups (
                Name, DateAdded, NumDailyReports, GroupCode, 
                ObserverPassword, MemberPassword, AdminPassword, group_size
                )
                VALUES (?, datetime('now'), 2, ?, ?, ?, ?, 0)
                """,
                (title, group_code, observer_password, member_password, admin_password)
            )
        else:
            cur.execute(
                """
                INSERT INTO groups (
                parent_id, Name, DateAdded, NumDailyReports, GroupCode, 
                ObserverPassword, MemberPassword, AdminPassword, group_size
                )
                VALUES (?, ?, datetime('now'), 2, ?, ?, ?, ?, 0)
                """,
                (current_group, title, group_code, observer_password, member_password, admin_password)
            )

        # Enter the group
        cur.execute("""SELECT id FROM groups WHERE GroupCode = ?""", (group_code,))
        group_to_enter = cur.fetchall()[0][0]
        print(group_to_enter)
        settings.current_group_id = group_to_enter
        settings.current_group_name = title
        con.commit()

        # Adds the user as an Admin
        cur.execute(
            """
            INSERT INTO admins (
            group_id, DateAdded, chat_id, role
            )
            VALUES (?, datetime('now'), ?, ?)
            """,
            (group_to_enter, chat_id, settings.ADMIN)
        )

        # Save all changes
        con.commit()

    update_obj.message.reply_text(f"Ok, your group will be named {title}")
    update_obj.message.reply_text(f"This is your group code: {group_code}. The following 3 messages are the "
                                  f"observer password, member password, and admin password respectively. "
                                  f"Keep the passwords safe, as they will allow any user to join and gain access to "
                                  f"sensitive info in your group!\n"
                                  f"To add a new member to your group, get them to use /joinexistinggroup and type "
                                  f"the group code.")
    update_obj.message.reply_text(observer_password)
    update_obj.message.reply_text(member_password)
    update_obj.message.reply_text(admin_password)
    update_obj.message.reply_text(f"You have entered {title}. Feel free to perform whatever functions you need here! "
                                  f"For starters, maybe /addusers?")
    # Have some more conversation take place
    return ConversationHandler.END


# Enters a group
def enter_group_implementation(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    chat_id, title = get_admin_reply(update_obj, context)

    # Gets the group id from the title
    # The title is of the following form: '{group_name} ({group_id})'. So the code finds the bracket from the back
    group_name = ''
    group_id = -1
    for i in range(len(title) - 2, -1, -1):
        if title[i] == '(':
            group_name = title[:i - 1]
            group_id = int(title[i + 1:len(title) - 1])
            break

    if group_id == -1:
        update_obj.message.reply_text("Something went wrong, please try again!")
        return ConversationHandler.END

    settings.current_group_id = group_id
    settings.current_group_name = group_name

    update_obj.message.reply_text(f"Ok, you have entered {group_name}")
    return ConversationHandler.END


#
