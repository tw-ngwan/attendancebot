"""
This file contains a few functions that changes the state of the object. Functions will be used by main

"""

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
import settings
from keyboards import yes_no_button_markup, group_name_keyboards
from backend_implementations import generate_random_password, generate_random_group_code, \
    get_admin_reply, rank_determination, get_group_id_from_button, check_admin_privileges
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
        current_group = settings.current_group_id[chat_id]
        group_code = generate_random_group_code()
        observer_password, member_password, admin_password = generate_random_password(iterations=3)
        # Stores the group in SQLite. current_group can be None
        cur.execute(
            """
            INSERT INTO groups (
            parent_id, Name, DateAdded, NumDailyReports, GroupCode, 
            ObserverPassword, MemberPassword, AdminPassword, group_size
            )
            VALUES (?, ?, datetime('now'), 2, ?, ?, ?, ?)
            """,
            (current_group, title, group_code, observer_password, member_password, admin_password)
        )

        # Enter the group
        cur.execute("""SELECT id FROM groups WHERE GroupCode = ?""", (group_code,))
        group_to_enter = cur.fetchall()[0][0]
        print(group_to_enter)
        settings.current_group_id[chat_id] = group_to_enter
        settings.current_group_name[chat_id] = title
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
def enter_group_follow_up(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    chat_id, title = get_admin_reply(update_obj, context)

    # Gets the group id from the title
    # The title is of the following form: '{group_name} ({group_id})'. So the code finds the bracket from the back
    group_id, group_name = get_group_id_from_button(title)

    if not group_id:
        update_obj.message.reply_text("Something went wrong, please try again!")
        return ConversationHandler.END

    settings.current_group_id[chat_id] = group_id
    settings.current_group_name[chat_id] = group_name

    update_obj.message.reply_text(f"Ok, you have entered {group_name}")
    return ConversationHandler.END


# Deletes the group that you are in
def delete_group_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    current_group_id = settings.current_group_id[chat_id]

    # Verify that user really wants to proceed with action
    if message.strip().lower() != "yes":
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
        # Set its child groups to have no parent
        cur.execute("""UPDATE groups SET parent_id = ? WHERE parent_id = ?""", (None, current_group_id))
        # Finally, delete the group
        cur.execute("""DELETE FROM groups WHERE id = ?""", (current_group_id, ))

    # Leave the group
    settings.current_group_id[chat_id] = None
    settings.current_group_name[chat_id] = None

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
        return ConversationHandler.END

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
    settings.current_group_id[chat_id] = group_id
    settings.current_group_name[chat_id] = group_name

    update_obj.message.reply_text(f"Congratulations, you are now a {user_rank} "
                                  f"of {settings.current_group_name[chat_id]}!")
    return ConversationHandler.END


# Quits the group you are currently in. Not to be confused with leavegroup!
def quit_group_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    current_group_id = settings.current_group_id[chat_id]

    # Verify that user really wants to proceed with action
    if message.strip().lower() != "yes":
        update_obj.message.reply_text("Ok, cancelling job now. ")
        return ConversationHandler.END

    # Deletes the user from the admins table
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """DELETE FROM admins WHERE chat_id = ? AND group_id = ?""", (chat_id, current_group_id)
        )

    # Remove you from the current group
    settings.current_group_id[chat_id] = None
    settings.current_group_name[chat_id] = None

    update_obj.message.reply_text("Ok, you have quit the group. Enter a group now with /entergroup or "
                                  "join a new group with /joingroup")
    return ConversationHandler.END


# Implements the changing of the group title
def change_group_title_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    group_name = message.strip()
    group_id = settings.current_group_id[chat_id]

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
    settings.current_group_name[chat_id] = group_name

    update_obj.message.reply_text("Group name updated")
    return ConversationHandler.END


# Ranks up the user
def uprank_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    password = message.strip()
    group_id = settings.current_group_id[chat_id]

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


# Merge groups follow up: Check if the users want all users to join a new group
def merge_groups_check_super_group(update_obj: Update, context: CallbackContext) -> int:
    chat_id, parent_group = get_admin_reply(update_obj, context)
    if parent_group == 'OK':
        update_obj.message.reply_text("Ok, cancelling job now")
        return ConversationHandler.END
    # Stores the group that the user wants as the parent. First we get the group id
    parent_id, parent_name = get_group_id_from_button(parent_group)
    settings.merge_group_storage[chat_id] = settings.MergeGroupStorage(parent_id)
    update_obj.message.reply_text("Do you want to join all users into a super group? That is, all users become united "
                                  "into one group, rather than remain in their own groups under this new parent group.",
                                  reply_markup=yes_no_button_markup)
    return settings.SECOND


# Merge groups follow up
def merge_groups_start_add_users(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    merge_group_storage = settings.merge_group_storage[chat_id]
    merge_group_storage.join_all_groups = message.strip().lower() == 'yes'
    groups_button_markup = group_name_keyboards(chat_id, extra_options=['OK'])
    update_obj.message.reply_text("Which groups do you want to add? Press 'OK' when you are done. ",
                                  reply_markup=groups_button_markup)
    return settings.THIRD


# Store merged groups. This function works recursively and will keep calling itself until OK is entered.
def merge_groups_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)
    merge_group_storage = settings.merge_group_storage[chat_id]

    # If message is ok, that means we can wrap up
    if message.strip().upper() == 'OK':

        # Get the parent group
        parent_id = merge_group_storage.parent

        # Verify that the parent group is ok
        if parent_id == -1:
            update_obj.message.reply_text("Invalid parent group detected. Operation ending...")
            return ConversationHandler.END

        # Check if all groups want to be joined together
        join_all_groups = merge_group_storage.join_all_groups

        # Get all child groups. Ok one problem: Make sure that the parent group is not in the child_groups
        all_groups = list(merge_group_storage.child_groups)

        # Update the sqlite database to reflect that the groups are merged
        with sqlite3.connect('attendance.db') as con:
            cur = con.cursor()
            # This is a tuple that contains first, the parent id, and then all the group_ids
            argument_tuple = tuple([parent_id] + all_groups)
            if not join_all_groups:
                # Add parent groups
                cur.execute(
                    f"""
                    UPDATE groups
                    SET parent_id = ? 
                    WHERE id IN ({','.join(['?'] * len(all_groups))})
                    """, argument_tuple
                )
            else:
                # If we want to join all users, we need to update the group_id of all users, admins, attendance
                argument_tuple = tuple([parent_id] + [ids[1] for ids in all_groups])
                # For users, transfer over to new group
                cur.execute(
                    f"""
                    UPDATE users
                    SET group_id = ?
                    WHERE group_id IN ({','.join(['?'] * len(all_groups))})
                    """, argument_tuple
                )
                # For admins - Delete the users
                cur.execute(
                    f"""
                    DELETE FROM admins
                    WHERE group_id IN ({','.join(['?'] * len(all_groups))})
                    """, tuple(all_groups)
                )
                # For attendance, transfer over to new group
                cur.execute(
                    f"""
                    UPDATE attendance
                    SET group_id = ?
                    WHERE group_id IN ({','.join(['?'] * len(all_groups))})
                    """, argument_tuple
                )

            # Save changes
            con.commit()

        update_obj.message.reply_text("All groups have been merged")
        return ConversationHandler.END

    group_id, group_name = get_group_id_from_button(message)
    group_button_markup = group_name_keyboards(chat_id, extra_options=['OK'])
    print(chat_id, group_id)
    # Check that you are group admin of the group that you want to add to
    if check_admin_privileges(chat_id, group_id) > 0:
        update_obj.message.reply_text("You need to be an admin of the group you want to merge!",
                                      reply_markup=group_button_markup)
        return settings.THIRD

    # Check that group added is not parent group
    if group_id == merge_group_storage.parent:
        update_obj.message.reply_text("Group added cannot be parent group!", reply_markup=group_button_markup)
        return settings.THIRD

    merge_group_storage.child_groups.add(group_id)
    update_obj.message.reply_text(f"Ok, group {message} added", reply_markup=group_button_markup)
    return settings.THIRD
