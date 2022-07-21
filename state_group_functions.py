"""
This file contains a few functions that changes the state of the object. Functions will be used by main

"""

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
import settings
from keyboards import groups_button_markup
from backend_implementations import generate_random_password, get_user_reply
import sqlite3


# Gets new group title
def name_group_title(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    chat_id, title = get_user_reply(update_obj, context)
    if title == "OK":
        update_obj.message.reply_text("Ok, quitting function now")
        return ConversationHandler.END
    # SQLite Execution: To store the group and the new user
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        current_group = settings.current_group
        group_code = generate_random_password(password=False)[0]
        observer_password, member_password, admin_password = generate_random_password(iterations=3)
        # Stores the group in SQLite
        if current_group is None:
            cur.execute(
                """
                INSERT INTO groups (
                Name, DateAdded, GroupCode, 
                ObserverPassword, MemberPassword, AdminPassword
                )
                VALUES (?, datetime('now'), ?, ?, ?, ?)
                """,
                (title, group_code, observer_password, member_password, admin_password)
            )
        else:
            cur.execute(
                """
                INSERT INTO groups (
                parent_id, Name, DateAdded, GroupCode, 
                ObserverPassword, MemberPassword, AdminPassword
                )
                VALUES (?, ?, datetime('now'), ?, ?, ?, ?)
                """,
                (current_group, title, group_code, observer_password, member_password, admin_password)
            )

        # Enter the group
        cur.execute("""SELECT id FROM groups WHERE GroupCode = ?""", (group_code,))
        group_to_enter = cur.fetchall()[0][0]
        print(group_to_enter)
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
    settings.current_group = group_to_enter
    update_obj.message.reply_text(f"You have entered {title}. Feel free to perform whatever functions you need here! "
                                  f"For starters, maybe /addusers?")
    # Have some more conversation take place
    return ConversationHandler.END


# Enters a group
def enter_group_implementation(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    chat_id, title = get_user_reply(update_obj, context)
    # Verify that that group exists first, then enter. Use SQLite to pull groups that user is part of.
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT Name, admins.group_id
              FROM admins 
              JOIN groups 
                ON admins.group_id = groups.id
             WHERE chat_id = ?""",
            (chat_id, )
        )
        user_groups = cur.fetchall()
        group_id = None
        for i in range(len(user_groups)):
            if user_groups[i][0].lower() == title.lower():
                group_id = user_groups[i][1]
                break
        if group_id is not None:
            settings.current_group = group_id

        # Save changes
        con.commit()

    update_obj.message.reply_text(f"Ok, you have entered {title}")
    return ConversationHandler.END
