from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
from keyboards import yes_no_button_markup, group_name_keyboards
import sqlite3


# Creates a group
def create_group(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Great! What would you like to name your group? To cancel, type 'OK'")
    return settings.FIRST


# Enters group
# I think you can use a KeyboardMarkup for this
def enter_group(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    groups_button_markup = group_name_keyboards(chat_id)
    update_obj.message.reply_text("Which group would you like to enter?", reply_markup=groups_button_markup)
    return settings.FIRST


# Leaves the current group to become 'groupless'
def leave_group(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    update_obj.message.reply_text(f"You have left the group")  # Get the group name
    settings.current_group = None
    return ConversationHandler.END


# Gets the current group
def current_group(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    print("Current group called")
    current_group_number = settings.current_group
    if current_group_number is None:
        update_obj.message.reply_text("You are currently not in any group")
        return ConversationHandler.END
    print(settings.current_group)
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute("SELECT Name FROM groups WHERE id = ?", (current_group_number, ))
        group_title = cur.fetchall()[0][0]
        update_obj.message.reply_text(f"You are currently in {group_title}")
        con.commit()
    return ConversationHandler.END


# Deletes group
def delete_group(update_obj: Update, context: CallbackContext) -> int:
    if _check_admin_privileges(update_obj, context):
        update_obj.message.reply_text("Are you sure you want to delete the group?", reply_markup=yes_no_button_markup)
        return settings.FIRST
    update_obj.message.reply_text("Admin Privileges are required to delete the group!")
    # Implementation to be continued in state_group_functions
    return ConversationHandler.END


# Merges groups -> handle problem of merging with oneself (or not)
def merge_groups(update_obj: Update, context: CallbackContext) -> int:
    if _check_admin_privileges(update_obj, context):
        chat_id = update_obj.message.chat_id
        groups_button_markup = group_name_keyboards(chat_id)
        update_obj.message.reply_text("Which group do you want as the parent group?", reply_markup=groups_button_markup)
        return settings.FIRST
    update_obj.message.reply_text("Admin Privileges are required to merge groups!")
    # Implementation to be continued in state_group_functions
    return ConversationHandler.END


# Joins the members of two groups together
def join_group_members(update_obj: Update, context: CallbackContext) -> int:
    if _check_admin_privileges(update_obj, context):
        chat_id = update_obj.message.chat_id
        groups_button_markup = group_name_keyboards(chat_id)
        update_obj.message.reply_text("Select the first group to be joined", reply_markup=groups_button_markup)
        return settings.FIRST
    update_obj.message.reply_text("Admin Privileges are required to join groups!")
    # Implementation to be continued in state_group_functions
    return ConversationHandler.END


# Joins an existing group
def join_existing_group(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text(f"Please key in the Group Code of the group you wish to enter")
    # Implementation to be continued in state_group_functions
    return settings.FIRST


# Quits the group you are currently in
def quit_group(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Are you sure you want to quite the group?", reply_markup=yes_no_button_markup)
    # Implementation to be continued in state_group_functions
    return settings.FIRST


# Changes the group title
def change_group_title(update_obj: Update, context: CallbackContext) -> int:
    # Do we need to check admin privileges?
    update_obj.message.reply_text("What title do you want to give the group?")
    # Implementation to be continued in state_group_functions
    return settings.FIRST


# Checks for admin privileges. Internal function
def _check_admin_privileges(update_obj: Update, context: CallbackContext) -> bool:
    # To be implemented
    return True
