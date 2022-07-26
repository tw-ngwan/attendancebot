"""Implementation of functions needed for attendance functions beyond the first one
Responds to messages and stores the messages given """

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import sqlite3
from state_variables import *
import settings
import datetime
from backend_implementations import get_group_members, get_admin_reply

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
def get_users_attendance(update_obj: Update, context: CallbackContext) -> int:
    chat_id, user = get_admin_reply(update_obj, context)
    update_obj.message.reply_text("Enter the user's desired attendance, you can enter in any of the following formats:")
    update_obj.message.reply_text(possible_attendance_formats)
    return settings.SECOND


# Gets the user's attendance, and updates it
# Should there be any typos, the bot will just not work. Ask user to update again
def update_users_attendance(update_obj: Update, context: CallbackContext) -> int:
    # Scenario 2: Half-day LL
    if '/' in
        "P/OS/MHC"

    return settings.FIRST


possible_attendance_formats = """
LL
P / LL 
LL till 260722
"""

# Stuff to be checked about date
# If the date is more than 2 years from today's date, reject
# If the date is before today's date, reject
# If the date has an invalid month or day or year, reject (use try, except ValueError for datetime?)
