"""This file contains a few of the functions that will be used by main
Old file, change ALL functions here (just storing old NewsBot functions)"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import sqlite3
from state_variables import *
import settings
import datetime
from backend_implementations import get_group_members, get_user_attendance_backend, check_admin_privileges, \
    get_day_group_attendance
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
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    get_day_group_attendance(update_obj, context, tomorrow)
    return ConversationHandler.END


# Gets the attendance of the group on a specific day
def get_specific_day_group_attendance(update_obj: Update, context: CallbackContext) -> int:
    update_obj.message.reply_text("Which day's attendance would you like to get? "
                                  "In your next message, please enter the desired date (and nothing else) in "
                                  "6-digit form (eg: 210722)")
    return settings.FIRST


# Changes attendance in the group you are in, for today
# Ok implement two functions: one to change today's attendance, the other to change tomorrow's
def change_attendance(update_obj: Update, context: CallbackContext) -> int:
    current_group_id = settings.current_group_id

    # Verify that the user is in a group first
    if current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return ConversationHandler.END

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
    return settings.FIRST
