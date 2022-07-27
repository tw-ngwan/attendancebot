"""Implementation of functions needed for attendance functions beyond the first one
Responds to messages and stores the messages given """

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import sqlite3
from state_variables import *
import settings
import datetime
from backend_implementations import get_group_members, get_admin_reply, check_admin_privileges, check_valid_datetime, \
    get_day_group_attendance, change_group_attendance_backend
from entry_attendance_functions import _change_attendance_send_messages


# I need to find a way to record what the attendance of a person is over multiple days, that is track the streak of
# LL until when
# Maybe add one more column into SQL (LastDay)


# Gets the name of user to change attendance of, and asks how the attendance is to be changed
# Do I give user a keyboard or what
# Yeah give a keyboard to update attendance
# But keyboard is a little too troublesome, and need to ask again
# Maybe ask user to answer in following formats
# P / LL
# LL
# LL till 260722
# But also need to assert that the date is ok, if not the bot will just crash
# But what if user enter wrongly, and want to change the attendance
# Need to ask them to retype in "P till <date>" to cancel the last attendance change, then redo again

# Attendance is in the following format:
# 1: P / LL
# 3: LL
# 5: MC till 280722
# What I need to do is first split according to \n, and then find valid rows (rows with input)
# The ultimate goal is to get a dict of lists (or list of lists)
# For now, you assume that this is for updating today's attendance. Split this into multiple functions.


# Change today's attendance
def change_today_attendance_follow_up(update_obj: Update, context: CallbackContext) -> int:
    today = datetime.date.today()
    change_group_attendance_backend(update_obj, context, today)
    return ConversationHandler.END


# Changes tomorrow's attendance
def change_tomorrow_attendance_follow_up(update_obj: Update, context: CallbackContext) -> int:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    change_group_attendance_backend(update_obj, context, tomorrow)
    return ConversationHandler.END


# Gets the day that the user wants for changing attendance. For change_any_day_attendance
def change_any_day_attendance_get_day(update_obj: Update, context: CallbackContext) -> int:
    chat_id, day = get_admin_reply(update_obj, context)
    if not check_valid_datetime(day):
        update_obj.message.reply_text("Date entered in an invalid format")
        return ConversationHandler.END

    # Stores the day (as a string) in the settings dictionary
    settings.attendance_date_edit[chat_id] = day

    # Give users instructions to send message detailing attendance
    _change_attendance_send_messages(update_obj, context)
    return settings.SECOND


# Changes the attendance of any day that the user wants
def change_any_day_attendance_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id = update_obj.message.chat_id
    # Gets the day that the user wants from settings, and then deletes it so that there is no duplicate of values
    day = settings.attendance_date_edit.pop(chat_id)
    # Converts it into a datetime object
    day = check_valid_datetime(day)
    change_group_attendance_backend(update_obj, context, day)
    return ConversationHandler.END


# Follow-up function of get_specific_day_group_attendance
def get_specific_day_group_attendance_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, date = get_admin_reply(update_obj, context)
    # Gets the date in the form of a datetime object
    day_to_check = check_valid_datetime(date)
    if not day_to_check:
        update_obj.message.reply_text("Date entered in an invalid format")
        return ConversationHandler.END

    get_day_group_attendance(update_obj, context, day_to_check)
    return ConversationHandler.END
