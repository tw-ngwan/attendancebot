"""This file contains a few of the functions that will be used by main
Old file, change ALL functions here (just storing old NewsBot functions)"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import sqlite3
from state_variables import *
import settings
import datetime
from backend_implementations import get_group_members, get_user_attendance_backend
from keyboards import group_users_keyboard


"https://stackoverflow.com/questions/48288124/how-to-send-message-in-specific-time-telegrambot"


# Gets the attendance of the group as a message and sends it
# Need to get the actual status of everyone from the table
# Make TimePeriod 1-indexed
def get_today_group_attendance(update_obj: Update, context: CallbackContext) -> int:
    today = datetime.date.today()
    today_string = f"{today.day:02d}{today.month:02d}{today.year:04d}"
    attendance_message_beginning = [f"Attendance for {today_string}:"]
    current_group_id = settings.current_group_id
    if current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return ConversationHandler.END
    attendance_message_body = get_user_attendance_backend(group_id=current_group_id, date=today)
    message = '\n'.join(attendance_message_beginning + attendance_message_body)
    update_obj.message.reply_text(message)
    return ConversationHandler.END


# Changes attendance in the group you are in, for today
# Ok implement two functions: one to change today's attendance, the other to change tomorrow's
def change_attendance(update_obj: Update, context: CallbackContext) -> int:
    current_group_id = settings.current_group_id
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
