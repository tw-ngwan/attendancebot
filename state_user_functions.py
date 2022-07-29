from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from backend_implementations import get_admin_reply, get_intended_users, convert_rank_to_id
import settings
import sqlite3


# Stores added user from add_users
# Because it returns FIRST, it recursively calls itself (hopefully)
def store_added_user(update_obj: Update, context: CallbackContext) -> int:
    chat_id, name = get_admin_reply(update_obj, context)
    current_group = settings.current_group_id
    if name == "OK":
        # If the dictionary exists, that means the group size has increased. We need to edit it.
        if current_group in settings.temp_groups:
            with sqlite3.connect('attendance.db') as con:
                cur = con.cursor()
                # Commit changes to groups table
                cur.execute(
                    """
                    UPDATE groups
                       SET group_size = ?
                     WHERE id = ?
                    """,
                    (settings.temp_groups[current_group], current_group)
                )

                # Remove the key from settings so that this is just a temp data storage
                settings.temp_groups.pop(current_group)

        update_obj.message.reply_text("Ok, quitting now...")
        return ConversationHandler.END

    # Adds the new name to users database
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()

        # We use settings.temp_groups in order to find the number of users in the group
        # This stores the value temporarily in a dict, so that the number of users does not need to keep getting called
        if current_group in settings.temp_groups:
            # Since num_users is already present, just gets it from the dict
            num_users = settings.temp_groups[current_group]
        else:
            # Finds the current number of users
            cur.execute(
                """ 
                SELECT COUNT(*) 
                  FROM users 
                 WHERE users.id = ?
                """,
                (current_group, )
            )
            num_users = cur.fetchall()[0][0]
            settings.temp_groups[current_group] = num_users

        # Adds user
        cur.execute(
            """
            INSERT INTO users (
            group_id, Name, DateAdded, rank
            ) 
            VALUES (?, ?, datetime('now'), ?)
            """,
            (current_group, name, num_users + 1)
        )

        # Updates the dictionary so that we have an accurate store of value to be called in the next iteration
        settings.temp_groups[current_group] += 1

        # Saves changes
        con.commit()

    update_obj.message.reply_text(f"User {name} added. ")
    return settings.FIRST


# Verifies that admin really wants to remove users
def remove_user_verification(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)

    # Verify that user really wants to proceed with action
    if message != "Yes":
        update_obj.message.reply_text("Ok, cancelling job now. ")
        return ConversationHandler.END

    update_obj.message.reply_text("Type in the numbers of the users you want to remove, separated by spaces. "
                                  "Note that this action cannot be erased! To cancel, type 'OK'. "
                                  "Eg: (1 3 2)")

    return settings.SECOND


# Removes the users
# First, check that the indices are ok. Then use sqlite to remove the users from the list
def remove_user_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, user_text = get_admin_reply(update_obj, context)
    current_group = settings.current_group_id

    if user_text == 'OK':
        update_obj.message.reply_text("Ok, cancelling job")
        return ConversationHandler.END

    # Get the users first
    users = get_intended_users(user_text, current_group)
    if not users:
        update_obj.message.reply_text("Users not entered correctly!")
        return ConversationHandler.END

    user_ids = [(convert_rank_to_id(current_group, rank), ) for rank in users]

    # Now, we remove the users from all tables concerned (attendance, users)
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.executemany(
            """
            DELETE FROM attendance
            WHERE user_id = ?""",
            user_ids
        )
        cur.executemany(
            """
            DELETE FROM users
            WHERE id = ?""",
            user_ids
        )

        # Save changes
        con.commit()

    update_obj.message.reply_text("All users removed")
    return ConversationHandler.END


# Gets the details of the user you want to edit, verifies them
def edit_user_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, message = get_admin_reply(update_obj, context)

    # Check if need to cancel
    if message == 'OK':
        update_obj.message.reply_text("Ok, cancelling job")
        return ConversationHandler.END

    current_group = settings.current_group_id
    user_parameters = [[val.strip() for val in param.split(':')] for param in message.split('\n')]

    # Check that for each new line, there are two entries separated by a :
    if not min([len(param) == 2 for param in user_parameters]):
        update_obj.message.reply_text("Message entered incorrectly!")
        return ConversationHandler.END

    users, names = zip(*user_parameters)

    # Get the users first
    users = get_intended_users(' '.join(users), current_group)
    if not users:
        update_obj.message.reply_text("Users not entered correctly!")
        return ConversationHandler.END

    # Already have the names. So we combine them into a list of tuples where we can executemany
    ids_to_edit = [(names[i], convert_rank_to_id(current_group, users[i])) for i in range(len(users))]

    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        # Update the table now
        cur.executemany(
            """
            UPDATE users
            SET name = ? 
            WHERE id = ?""",
            ids_to_edit
        )

        con.commit()

    update_obj.message.reply_text("All edits done")
    return ConversationHandler.END






