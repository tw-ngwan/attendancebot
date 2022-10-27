"""Hidden developer functions. Mainly for debugging. Functions here are NOT shown to the general public"""
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, Updater
import settings
import os
from data import DATABASE_URL
from backend_implementations import verify_group_and_role, get_admin_reply
import psycopg2


DEVELOPER_GROUP_ID = 101


# Note: All telegram functions here will start with verify_developer, and will call verify_developer_follow_up
# Hence verify_developer returns an integer state, verify_developer_follow_up returns a bool

# I want to add one more function for testing and debugging, like it will print the exception on your phone,
# but I'm not sure how to add it


# Verification function to ensure that all functions here can be used
def verify_developer(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    current_group = settings.current_group_id[chat_id]
    # First layer of security: Check that you are in the correct group, and that you are an admin
    if not current_group == DEVELOPER_GROUP_ID or not verify_group_and_role(update_obj, context, settings.ADMIN):
        update_obj.message.reply_text("A developer function can only be used by an admin in the developer group!")
        return ConversationHandler.END

    # Second layer of security: User password
    update_obj.message.reply_text("Type in the developer password (caps sensitive)")
    return settings.FIRST


# Verification function follow-up
def verify_developer_follow_up_password(update_obj: Update, context: CallbackContext) -> bool:
    chat_id, message = get_admin_reply(update_obj, context)
    message = message.strip()
    password = os.getenv("DEVELOPER_PASSWORD")
    # If the password provided is not correct
    if message != password:
        username = update_obj.message.from_user.username
        update_obj.message.reply_text("Incorrect password, please try again. The developers have been notified")
        broadcast_to_developers_backend(update_obj, context,
                                        f"We foiled a log in attempt by {username} (chat id: {chat_id})")
        return False

    update_obj.message.reply_text("User verified. Welcome")
    return True


# For broadcasting message out to everyone
def broadcast(update_obj: Update, context: CallbackContext):
    # First, we do one more verification to ensure that this is correct
    if not verify_developer_follow_up_password(update_obj, context):
        return ConversationHandler.END

    update_obj.message.reply_text("Type out the message you want to broadcast to everyone")
    return settings.SECOND


# Follow-up function for broadcasting message out to everyone
def broadcast_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    broadcast_backend(update_obj, context, message)
    update_obj.message.reply_text("Message has been broadcasted")
    return ConversationHandler.END


# Backend function for broadcasting message to everyone
def broadcast_backend(update_obj: Update, context: CallbackContext, message: str):
    chat_ids = get_all_admin_chat_ids()
    dev_chat_id = update_obj.message.chat_id
    for chat_id in chat_ids:
        try:
            context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            context.bot.send_message(chat_id=dev_chat_id, text=f"Unable to send message to {chat_id}. Exception:\n{e}")


# For broadcasting message out to developers
def broadcast_to_developers_backend(update_obj: Update, context: CallbackContext, message: str):
    developer_ids = get_all_developer_chat_ids()
    for developer_id in developer_ids:
        context.bot.send_message(chat_id=developer_id, text=message)


# For getting SQL console for developer use
def developer_sql_console(update_obj: Update, context: CallbackContext):
    if not verify_developer_follow_up_password(update_obj, context):
        return ConversationHandler.END

    update_obj.message.reply_text("Type out your SQL commands to be executed exactly (without the ;). Type OK to exit")
    return settings.SECOND


# For getting SQL console for developer use
def developer_sql_console_follow_up(update_obj: Update, context: CallbackContext):
    chat_id, message = get_admin_reply(update_obj, context)
    # This would allow me to keep sending prompts without having to reverify
    if message.strip().lower() == 'ok':
        update_obj.message.reply_text("SQL executed. Exiting...")
        return ConversationHandler.END

    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            try:
                cur.execute(message)
                reply_details = cur.fetchall()
                reply_details_string = str(reply_details)
                update_obj.message.reply_text(reply_details_string)
            except Exception as e:
                update_obj.message.reply_text("An exception has occured")
                update_obj.message.reply_text(str(e))

    return settings.SECOND


# Gets all unique chat_ids inside the group
def get_all_admin_chat_ids():
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            cur.execute(
                """SELECT DISTINCT chat_id FROM admins"""
            )
            chat_ids = cur.fetchall()
            chat_ids = [chat_id[0] for chat_id in chat_ids]
    return chat_ids


# Get all developer chat_ids
def get_all_developer_chat_ids():
    with psycopg2.connect(DATABASE_URL, sslmode='require') as con:
        with con.cursor() as cur:
            cur.execute(
                """SELECT chat_id FROM admins WHERE role = 'Admin' AND group_id = %s""", (DEVELOPER_GROUP_ID, )
            )
            chat_ids = cur.fetchall()
            chat_ids = [chat_id[0] for chat_id in chat_ids]
    return chat_ids
