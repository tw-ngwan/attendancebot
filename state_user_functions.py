from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from backend_implementations import get_admin_reply
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
