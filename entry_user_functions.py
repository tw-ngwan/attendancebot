from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
import sqlite3
from backend_implementations import verify_group_and_role
from keyboards import yes_no_button_markup


# Adds a user to the bot
def add_users(update_obj: Update, context: CallbackContext) -> int:

    # Verify that user is authorised first
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    print("After verification")
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
    chat_id = update_obj.message.chat_id
    if settings.current_group_id[chat_id] is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return ConversationHandler.END
    update_obj.message.reply_text("Ok, getting all users...")
    with sqlite3.connect('attendance.db') as con:
        current_group_id = settings.current_group_id[chat_id]
        cur = con.cursor()
        cur.execute("""SELECT Name FROM users WHERE group_id = ? ORDER BY rank""", (current_group_id, ))
        names = [data[0] for data in cur.fetchall()]

    name_message = '\n'.join(["Members: "] + names)
    update_obj.message.reply_text(name_message)
    return ConversationHandler.END


# Changes the ordering of a group
def change_group_ordering(update_obj: Update, context: CallbackContext) -> int:

    # First, verify that the user is qualified to do this
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    # Explanation for how to use the swap function, which is honestly quite complicated
    update_obj.message.reply_text("The group ordering would be done with swapping pairs of users. To do so, "
                                  "in your next message, key in the numbers of pairs of users you would like to "
                                  "swap, with each pair on the same line, and separate pairs on new lines. "
                                  "Key in ONLY two numbers per line, and pairs of numbers in separate lines. "
                                  "A sample attendance, swap message, resultant attendance status "
                                  "and explanation is provided in the next messages. ")
    update_obj.message.reply_text("Sample attendance \n"
                                  "1) Harry \n"
                                  "2) Ethan \n"
                                  "3) Sophia \n"
                                  "4) Michael ")
    update_obj.message.reply_text("1 2 \n"
                                  "2 3 \n"
                                  "1 4 ")
    update_obj.message.reply_text("Resultant attendance \n"
                                  "1) Michael \n"
                                  "2) Sophia \n"
                                  "3) Harry \n"
                                  "4) Ethan ")
    update_obj.message.reply_text("Explanation: \nThe swaps are processed in order. For the first swap, "
                                  "1 and 2 are swapped, so Harry (pos 1) goes to 2) and Ethan (pos 2) to 1). For the "
                                  "second swap, 2 and 3 are swapped, so Harry (pos 2) goes to 3) and Sophia (pos 3) "
                                  "goes to 2). For the third swap, 1 and 4 are swapped, so Ethan (pos 1) goes to 4) "
                                  "and Michael (pos 4) goes to 1).")
    update_obj.message.reply_text("The number refers to the number next to the user. To just swap a user to the "
                                  "top, key in his number along with 0 on the same line. To swap to the bottom, "
                                  "key in his number along with -1 on the same line ")

    return settings.FIRST
