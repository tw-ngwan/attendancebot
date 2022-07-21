from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
import sqlite3


# Adds a user to the bot
def add_users(update_obj: Update, context: CallbackContext) -> int:
    if settings.current_group is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return ConversationHandler.END
    update_obj.message.reply_text("Type in the name of the user you want to add. "
                                  "You can keep sending messages to add users. To indicate that you are done "
                                  "adding users, type 'OK'")
    return settings.FIRST


# Removes a user from the bot
def remove_users(update_obj: Update, context: CallbackContext) -> int:
    pass


# Edits a user's name
def edit_users(update_obj: Update, context: CallbackContext) -> int:
    pass


# Gets a list of all users
def get_users(update_obj: Update, context: CallbackContext) -> int:
    if settings.current_group is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return ConversationHandler.END
    update_obj.message.reply_text("Ok, getting all users...")
    with sqlite3.connect('attendance.db') as con:
        current_group = settings.current_group
        cur = con.cursor()
        cur.execute("""SELECT Name FROM users WHERE group_id = ?""", (current_group, ))
        names = [data[0] for data in cur.fetchall()]

    name_message = '\n'.join(["Members: "] + names)
    update_obj.message.reply_text(name_message)
    return ConversationHandler.END
