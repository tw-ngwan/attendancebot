"""
This file contains a few functions that changes the state of the object. Functions will be used by main

"""

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
import settings
from keyboards import group_name_keyboards
from backend_implementations import generate_random_password, generate_random_group_code, \
    get_admin_reply, get_admin_groups, rank_determination
import sqlite3


# Gets new group title
# TO BE ADDED: Get an option for user to toggle number of daily reports they want, from 1-4
def create_group_follow_up(update_obj: Update, context: CallbackContext) -> int:
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


# Deletes the group that you are in
def delete_group_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    current_group_id = settings.current_group_id

    # Verify that user really wants to proceed with action
    if message != "Yes":
        update_obj.message.reply_text("Ok, cancelling job now. ")
        return ConversationHandler.END

    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()

        # Delete from attendance first
        cur.execute("""DELETE FROM attendance WHERE group_id = ?""", (current_group_id, ))
        # Delete from users
        cur.execute("""DELETE FROM users WHERE group_id = ?""", (current_group_id, ))
        # Delete from admins
        cur.execute("""DELETE FROM admins WHERE group_id = ?""", (current_group_id, ))
        # Finally, delete the group
        cur.execute("""DELETE FROM groups WHERE id = ?""", (current_group_id, ))

    # Leave the group
    settings.current_group_id = None
    settings.current_group_name = None

    return ConversationHandler.END


# Gets the group code of the group that the user wants to enter. Verifies that it exists, and prompts for password
def join_group_get_group_code(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)

    # Check if the group code exists
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute("""SELECT id, Name FROM groups WHERE GroupCode = ?""", (message.strip().upper(), ))
        group_details = cur.fetchall()

    if not group_details:
        update_obj.message.reply_text("Group code entered does not correspond with any group!")

    group_id, group_name = group_details[0][0], group_details[0][1]
    settings.group_to_join[chat_id] = (group_id, group_name)

    update_obj.message.reply_text("Enter the group password (case-sensitive)")
    return settings.SECOND


# Enters a group based on the password provided
def join_group_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    password = message.strip()
    group_id, group_name = settings.group_to_join.pop(chat_id)

    # Gets the rank of the user based on their password
    user_rank = rank_determination(password, group_id)
    if not user_rank:
        update_obj.message.reply_text("Incorrect password provided!")
        return ConversationHandler.END

    # Adds the admin into the group
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO admins
            (group_id, DateAdded, chat_id, role)
            VALUES (?, date('now'), ?, ?)
            """,
            (group_id, chat_id, user_rank)
        )

        # Saves changes
        con.commit()

    # Saves the changes to group
    settings.current_group_id = group_id
    settings.current_group_name = group_name

    update_obj.message.reply_text(f"Congratulations, you are now a {user_rank} "
                                  f"of {settings.current_group_name}!")
    return ConversationHandler.END


# Quits the group you are currently in. Not to be confused with leavegroup!
def quit_group_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    current_group_id = settings.current_group_id

    # Verify that user really wants to proceed with action
    if message != "Yes":
        update_obj.message.reply_text("Ok, cancelling job now. ")
        return ConversationHandler.END

    # Deletes the user from the admins table
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """DELETE FROM admins WHERE chat_id = ? AND group_id = ?""", (chat_id, current_group_id)
        )

    # Remove you from the current group
    settings.current_group_id = None
    settings.current_group_name = None

    update_obj.message.reply_text("Ok, you have quit the group. Enter a group now with /entergroup or "
                                  "join a new group with /joingroup")
    return ConversationHandler.END


# Implements the changing of the group title
def change_group_title_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    group_name = message.strip()
    group_id = settings.current_group_id

    # Updates the group title for the group
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            UPDATE groups 
               SET Name = ? 
             WHERE id = ?
            """, (group_name, group_id)
        )

        # Saves changes
        con.commit()

    # Updates the group name
    settings.current_group_name = group_name

    update_obj.message.reply_text("Group name updated")
    return ConversationHandler.END


# Ranks up the user
def uprank_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    password = message.strip()
    group_id = settings.current_group_id

    user_rank = rank_determination(password, group_id)
    if not user_rank:
        update_obj.message.reply_text("Incorrect password provided!")
        return ConversationHandler.END

    # Updates the rank of the admin
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            UPDATE admins
               SET role = ? 
             WHERE chat_id = ?""",
            (user_rank, chat_id)
        )

        # Save changes
        con.commit()

    update_obj.message.reply_text(f"Congratulations, you are now a {user_rank}!")
    return ConversationHandler.END
