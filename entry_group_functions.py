from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
from keyboards import yes_no_button_markup, group_name_keyboards
from backend_implementations import verify_group_and_role, check_admin_privileges
import sqlite3


# Creates a group
def create_group(update_obj: Update, context: CallbackContext) -> int:

    # Get the whole group's id
    current_group_id = settings.current_group_id
    if current_group_id is not None and not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END

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
    settings.current_group_id = None
    settings.current_group_name = None
    return ConversationHandler.END


# Gets the current group
def current_group(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    print("Current group called")
    current_group_number = settings.current_group_id
    current_group_name = settings.current_group_name
    if current_group_number is None:
        update_obj.message.reply_text("You are currently not in any group")
        return ConversationHandler.END

    update_obj.message.reply_text(f"You are currently in {current_group_name}")
    return ConversationHandler.END


# Deletes group
def delete_group(update_obj: Update, context: CallbackContext) -> int:

    # Verify that you can do this role
    if not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END

    update_obj.message.reply_text("Are you sure you want to delete the group? Note that this is "
                                  "an IRREVERSIBLE action and that ALL DATA WILL BE LOST!",
                                  reply_markup=yes_no_button_markup)
    return settings.FIRST


# Merges groups -> handle problem of merging with oneself (or not)
def merge_groups(update_obj: Update, context: CallbackContext) -> int:

    chat_id = update_obj.message.chat_id
    groups_button_markup = group_name_keyboards(chat_id, extra_options=['OK'])
    update_obj.message.reply_text("Which group do you want as the parent group? If you want to merge all groups "
                                  "under a new parent group, call /creategroup to create a new group first. "
                                  "Type 'OK' to cancel ",
                                  reply_markup=groups_button_markup)
    return settings.FIRST


# Joins the members of two groups together
def join_group_members(update_obj: Update, context: CallbackContext) -> int:

    if not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END
    chat_id = update_obj.message.chat_id
    groups_button_markup = group_name_keyboards(chat_id)
    update_obj.message.reply_text("Select the first group to be joined", reply_markup=groups_button_markup)
    return settings.FIRST


# Joins an existing group
def join_existing_group(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text(f"Please key in the Group Code of the group you wish to enter")
    # Implementation to be continued in state_group_functions
    return settings.FIRST


# Quits the group you are currently in
def quit_group(update_obj: Update, context: CallbackContext) -> int:

    # Check that you are in a group first
    if not verify_group_and_role(update_obj, context, settings.OBSERVER):
        return ConversationHandler.END

    update_obj.message.reply_text("Are you sure you want to quit the group?", reply_markup=yes_no_button_markup)
    # Implementation to be continued in state_group_functions
    return settings.FIRST


# Changes the group title
def change_group_title(update_obj: Update, context: CallbackContext) -> int:

    # Verify that you are an admin
    if not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END

    update_obj.message.reply_text("What title do you want to give the group?")
    # Implementation to be continued in state_group_functions
    return settings.FIRST


# Gets the group passwords of the levels you need
def get_group_passwords(update_obj: Update, context: CallbackContext) -> int:

    current_group_id = settings.current_group_id
    chat_id = update_obj.message.chat_id

    admin_status = check_admin_privileges(chat_id, current_group_id)

    # In place of an if-else loop, we use a list and lambda functions to save space
    # The functions are for admin, member, and observer respectively (and the last for None)
    message_functions = [lambda x, y: x.message.reply_text("Here is the observer password, member password, and "
                                                           "admin password respectively"),
                         lambda x, y: x.message.reply_text("Here is the observer and member password respectively"),
                         lambda x, y: x.message.reply_text("Here is the observer password"),
                         lambda x, y: x.message.reply_text("Invalid credentials! Something went wrong, you are not "
                                                           "authorised to perform any actions")]

    # Gets the passwords
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT ObserverPassword, MemberPassword, AdminPassword
              FROM groups
             WHERE id = ?
            """,
            (current_group_id, )
        )
        passwords = cur.fetchall()

    # The three passwords that are needed
    observer, member, admin = passwords[0]
    send_password_functions = [lambda x, y: x.message.reply_text(admin), lambda x, y: x.message.reply_text(member),
                               lambda x, y: x.message.reply_text(observer)]

    # Informs the user
    message_functions[admin_status](update_obj, context)
    for i in range(len(send_password_functions) - 1, -1, -1):
        if i >= admin_status:
            send_password_functions[i](update_obj, context)

    return ConversationHandler.END


# Allows a user (observer or member) to become admin of a group
def uprank(update_obj: Update, context: CallbackContext) -> int:

    # Unlike in the past where we verify that user is qualified, here we check if overqualified (hence no not)
    if verify_group_and_role(update_obj, context, settings.ADMIN):
        update_obj.message.reply_text("You are already an admin!")
        return ConversationHandler.END

    update_obj.message.reply_text("Enter the group password (case-sensitive)")
    return settings.FIRST
