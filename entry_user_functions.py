from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
import sqlite3
from backend_implementations import verify_group_and_role
from keyboards import yes_no_button_markup


# Adds a user to the bot
def add_users(update_obj: Update, context: CallbackContext) -> int:

    # Verify that user is authorised first
    if verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    update_obj.message.reply_text("Type in the name of the user you want to add. "
                                  "You can keep sending messages to add users. To indicate that you are done "
                                  "adding users, type 'OK'")
    return settings.FIRST


# Removes a user from the bot
def remove_users(update_obj: Update, context: CallbackContext) -> int:

    # Verify that user is authorised first
    if not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END

    # Ask the user whether they want to do this first
    update_obj.message.reply_text("Are you sure you want to remove users? This action CANNOT be erased!",
                                  reply_markup=yes_no_button_markup)
    return settings.FIRST


# Edits a user's name
def edit_users(update_obj: Update, context: CallbackContext) -> int:

    # Verify that user is authorised first
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    # Gives instructions on how to formulate the input
    update_obj.message.reply_text("Type in the number of each user you want ot edit, followed by ':', and their new "
                                  "name. A valid example is presented below. To cancel, type 'OK'. ")
    update_obj.message.reply_text("1: Chan Heng Hong \n"
                                  "3: Chester Mike \n"
                                  "4: Jennifer K. Rastouza ")
    return settings.FIRST


# Gets a list of all users
def get_users(update_obj: Update, context: CallbackContext) -> int:
    if settings.current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return ConversationHandler.END
    update_obj.message.reply_text("Ok, getting all users...")
    with sqlite3.connect('attendance.db') as con:
        current_group_id = settings.current_group_id
        cur = con.cursor()
        cur.execute("""SELECT Name FROM users WHERE group_id = ?""", (current_group_id, ))
        names = [data[0] for data in cur.fetchall()]

    name_message = '\n'.join(["Members: "] + names)
    update_obj.message.reply_text(name_message)
    return ConversationHandler.END
