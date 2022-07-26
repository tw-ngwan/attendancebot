"""This file contains a few of the functions that will be used by main
Old file, change ALL functions here (just storing old NewsBot functions)"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import sqlite3
from state_variables import *
import settings


"https://stackoverflow.com/questions/48288124/how-to-send-message-in-specific-time-telegrambot"


# Gets the attendance of the group as a message and sends it
# Need to get the actual status of everyone from the table
def get_group_attendance(update_obj: Update, context: CallbackContext) -> int:
    attendance_message_beginning = ["Attendance for today:"]
    current_group_id = settings.current_group_id
    # Gets all users
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute("""SELECT Name FROM users WHERE group_id = ?""", (current_group_id,))
        names = [data[0] for data in cur.fetchall()]
    attendance_message_body = [''.join([str(i + 1), ') ', names[i], ' - P']) for i in range(len(names))]

    message = '\n'.join(attendance_message_beginning + attendance_message_body)
    update_obj.message.reply_text(message)
    return ConversationHandler.END
