from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from backend_implementations import get_admin_reply
import settings
import sqlite3


# Stores added user from add_users
# Because it returns FIRST, it recursively calls itself (hopefully)
def store_added_user(update_obj: Update, context: CallbackContext) -> int:
    chat_id, name = get_admin_reply(update_obj, context)
    if name == "OK":
        update_obj.message.reply_text("Ok, quitting now...")
        return ConversationHandler.END

    # Adds the new name to users database
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        current_group = settings.current_group_id

        # Adds user
        cur.execute(
            """
            INSERT INTO users (
            group_id, Name, DateAdded
            ) 
            VALUES (?, ?, datetime('now'))
            """,
            (current_group, name)
        )

        # May want to add the attendance status of the user for the next 7 days first, so that attendance is tracked

        # Saves edits
        con.commit()

    update_obj.message.reply_text(f"User {name} added. ")
    return settings.FIRST
