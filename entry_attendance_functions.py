"""This file contains a few of the functions that will be used by main
Old file, change ALL functions here (just storing old NewsBot functions)"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
import datetime
from backend_implementations import get_group_members, get_group_attendance_backend, check_admin_privileges, \
    reply_non_admin, get_day_group_attendance, verify_group_and_role
from keyboards import group_users_keyboard


"https://stackoverflow.com/questions/48288124/how-to-send-message-in-specific-time-telegrambot"


# Gets the attendance of the group as a message and sends it
# Need to get the actual status of everyone from the table
# Make TimePeriod 1-indexed
def get_today_group_attendance(update_obj: Update, context: CallbackContext) -> int:
    today = datetime.date.today()
    get_day_group_attendance(update_obj, context, today)
    return ConversationHandler.END


# Gets the attendance of the group for the next day
def get_tomorrow_group_attendance(update_obj: Update, context: CallbackContext) -> int:
    # Gets the next weekday
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    while tomorrow.weekday() > 4:
        tomorrow += datetime.timedelta(days=1)
    get_day_group_attendance(update_obj, context, tomorrow)
    return ConversationHandler.END


# Gets the attendance of the group on a specific day
def get_any_day_group_attendance(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Which day's attendance would you like to get? "
                                  "In your next message, please enter the desired date (and nothing else) in "
                                  "6-digit form (eg: 210722)")
    return settings.FIRST


# Gets the attendance of a user over the past month
# Questions you first need to answer: What period of time? How do you define it? Through another question?
def get_user_attendance_month(update_obj: Update, context: CallbackContext) -> int:

    # We first verify that user is in a group, and is at least Member in the group
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    update_obj.message.reply_text("Key in the numbers of the users who you want to get the attendance of, each "
                                  "separated by a space. (Eg: 3 4 6)")
    return settings.FIRST


# Gets the attendance of a user over an arbitrary period of time
def get_user_attendance_arbitrary(update_obj: Update, context: CallbackContext) -> int:

    # We first verify that user is in a group, and is at least Member in the group
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    update_obj.message.reply_text("Key in the numbers of the users who you want to get the attendance of, each "
                                  "separated by a space in the first row. Key in the start date in 6-digit form "
                                  "in the second row, and the end date in the third row (both inclusive). Here's an "
                                  "example of a message that works: ")
    update_obj.message.reply_text("3 4 6 \n"
                                  "260622\n"
                                  "030822")
    return settings.FIRST


# Changes attendance in the group you are in, for today
# Ok implement two functions: one to change today's attendance, the other to change tomorrow's
def change_attendance(update_obj: Update, context: CallbackContext) -> int:

    # We check that the user is in a group, and is at least Member in the group
    if not verify_group_and_role(update_obj, context, settings.MEMBER):
        return ConversationHandler.END

    # Give user instructions on how to submit message
    _change_attendance_send_messages(update_obj, context)
    return settings.FIRST


# Asks question to change attendance of group on any day
def change_any_day_attendance(update_obj: Update, context: CallbackContext) -> int:

    # We check that the user is in a group, and is at least Admin in the group
    if not verify_group_and_role(update_obj, context, settings.ADMIN):
        return ConversationHandler.END

    update_obj.message.reply_text("Enter the date that you want to change attendance of, in the 6-digit format "
                                  "(eg: 280722)")
    return settings.FIRST


# The messages to be sent in the change_attendance function
def _change_attendance_send_messages(update_obj: Update, context: CallbackContext) -> None:

    # Give user instructions on how to submit message
    update_obj.message.reply_text("State the number of the user(s) whose attendance you want to change, followed "
                                  "by a ':', then their attendance for the day. Type 'OK' to cancel. "
                                  "The number of the user refers to the number next to their names. "
                                  "Here are the possible attendance formats: ")
    update_obj.message.reply_text("LL\n"
                                  "P / LL\n"
                                  "LL till 260722")
    update_obj.message.reply_text("Here's an example of a successful attendance update message. Do NOT use ':' or "
                                  "'/' anywhere else other than in marking attendance. ")
    update_obj.message.reply_text("1: LL \n"
                                  "3: P / OFF \n"
                                  "7: MC till 280822 \n"
                                  "4: OS (Jurong) / MA")

