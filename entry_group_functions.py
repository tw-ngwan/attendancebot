from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
from keyboards import yes_no_button_markup, group_name_keyboards
from backend_implementations import verify_group_and_role, check_admin_privileges, get_admin_id
import psycopg2
from data import DATABASE_URL


# Creates a group
def create_group(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    # Get the whole group's id
    current_group_id = settings.current_group_id[chat_id]
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


# enters the current group to become 'groupless'
def leave_group(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    chat_id = update_obj.message.chat_id
    update_obj.message.reply_text(f"You have left the group")  # Get the group name
    settings.current_group_id[chat_id] = None
    settings.current_group_name[chat_id] = None
    return ConversationHandler.END


# Gets the current group
def current_group(update_obj: Update, context: CallbackContext) -> ConversationHandler.END:
    chat_id = update_obj.message.chat_id
    print("Current group called")
    current_group_number = settings.current_group_id[chat_id]
    current_group_name = settings.current_group_name[chat_id]
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


# The precursor function to setting username
def set_username_precursor(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Key your username into the chat")
    return settings.FIRST


# Gets the group passwords of the levels you need
def get_group_passwords(update_obj: Update, context: CallbackContext) -> int:

    chat_id = update_obj.message.chat_id
    current_group_id = settings.current_group_id[chat_id]
    if current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /enter!")
        return ConversationHandler.END

    admin_status = check_admin_privileges(chat_id, current_group_id)

    # In place of an if-else loop, we use a list and lambda functions to save space
    # The functions are for admin, member, and observer respectively (and the last for None)
    message_functions = [lambda x, y: x.message.reply_text("Here is the group code, observer password, member password,"
                                                           " and admin password respectively"),
                         lambda x, y: x.message.reply_text("Here is the group code, observer and member password "
                                                           "respectively"),
                         lambda x, y: x.message.reply_text("Here is the group code and observer password respectively"),
                         lambda x, y: x.message.reply_text("Invalid credentials! Something went wrong, you are not "
                                                           "authorised to perform any actions")]

    # Gets the passwords
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            cur.execute(
                """
                SELECT GroupCode, ObserverPassword, MemberPassword, AdminPassword
                  FROM groups
                 WHERE id = %s
                """,
                (current_group_id, )
            )
            passwords = cur.fetchall()

    # The three passwords that are needed
    group_code, observer, member, admin = passwords[0]
    send_password_functions = [lambda x, y: x.message.reply_text(admin), lambda x, y: x.message.reply_text(member),
                               lambda x, y: x.message.reply_text(observer)]

    # Informs the user
    message_functions[admin_status](update_obj, context)
    update_obj.message.reply_text(group_code)
    for i in range(len(send_password_functions) - 1, -1, -1):
        if i >= admin_status:
            send_password_functions[i](update_obj, context)

    return ConversationHandler.END


# Allows a user (observer or member) to become admin of a group
def uprank(update_obj: Update, context: CallbackContext) -> int:

    chat_id = update_obj.message.chat_id
    group_id = settings.current_group_id[chat_id]

    # Check that group_id is not None
    if group_id is None:
        update_obj.message.reply_text("Enter a group first with /enter!")
        return ConversationHandler.END

    # Unlike in the past where we verify that user is qualified, here we check if overqualified (hence no not)
    if check_admin_privileges(chat_id, group_id) == 0:
        update_obj.message.reply_text("You are already an admin!")
        return ConversationHandler.END

    update_obj.message.reply_text("Enter the group password (case-sensitive)")
    return settings.FIRST


# Allow an admin to get the last-done functions
def get_group_history(update_obj: Update, context: CallbackContext):

    # First, verify that you are an admin
    if not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END

    chat_id = update_obj.message.chat_id
    group_id = settings.current_group_id[chat_id]
    admin_id = get_admin_id(chat_id, group_id)
    # Accesses the table to print out history
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            # Makes the timezone correct first
            cur.execute(
                """
                SET timezone TO 'Asia/Singapore'
                """
            )
            cur.execute(
                """
                SELECT admins.username, admin_movements.DateTime, admin_movements.function, admin_movements.admin_text
                  FROM admin_movements
                  JOIN admins
                    ON admins.id = admin_movements.admin_id 
                 WHERE admin_movements.group_id = %s
                 ORDER BY admin_movements.DateTime DESC
                 LIMIT 100
                """,
                (group_id, )
            )
            values = cur.fetchall()
            if not values:
                update_obj.message.reply_text("Nothing yet...")
                return ConversationHandler.END

    messages = []
    message_content = []
    for value in values:
        new_message = f"Username: {value[0]}\nDate and Time: {value[1]}\nFunction: {value[2]}\nFollow-up Message: {value[3]}\n"
        message_content.append(new_message)
        if len(message_content) >= 10:
            messages.append('\n'.join(message_content))
            message_content = []

    messages.append('\n'.join(message_content))
    for message in messages:
        update_obj.message.reply_text(message)
    return ConversationHandler.END
