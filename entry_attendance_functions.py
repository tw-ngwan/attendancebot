"""This file contains a few of the functions that will be used by main
Old file, change ALL functions here (just storing old NewsBot functions)"""


from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import sqlite3
from state_variables import *
import settings
import datetime
from backend_implementations import get_group_members
from keyboards import group_users_keyboard


"https://stackoverflow.com/questions/48288124/how-to-send-message-in-specific-time-telegrambot"


# Gets the attendance of the group as a message and sends it
# Need to get the actual status of everyone from the table
# Make TimePeriod 1-indexed
def get_group_attendance(update_obj: Update, context: CallbackContext) -> int:
    today = datetime.date.today()
    today_string = f"{today.day:02d}{today.month:02d}{today.year:04d}"
    attendance_message_beginning = [f"Attendance for {today_string}:"]
    current_group_id = settings.current_group_id
    # Gets all users
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()

        # Gets the attendance of the non-present people
        cur.execute(
            """
            SELECT users.id, users.Name, TimePeriod, AttendanceStatus 
              FROM attendance
              JOIN users 
               ON users.id = attendance.users_id 
             WHERE Date = date('now', '+1 day') 
               AND attendance.users_id 
                IN (
                    SELECT id FROM users WHERE group_id = ?
            )
            """,
            (current_group_id, )
        )
        group_attendance = cur.fetchall()
        # Gets the number of time periods to be updated per day
        cur.execute("""SELECT NumDailyReports FROM groups WHERE id = ?""", (current_group_id, ))
        num_daily_reports = cur.fetchall()[0][0]

        # How this works:
        # I create a dict, that stores values like this: {id: [Name, [Attendance[0], Attendance[1], ...]]}
        group_attendance_dict = {}
        for member in group_attendance:
            if member[0] not in group_attendance_dict:
                group_attendance_dict[member[0]] = [member[1], ['P'] * num_daily_reports]
            group_attendance_dict[member[0]][1][member[2] - 1] = member[3]
        # group_attendance_dict = {member[0]: member[1:] for member in group_attendance}

        # Gets the attendance of the remaining people
        all_members = get_group_members(current_group_id)
        id_name_dict = {member[0]: member[1] for member in all_members}

        # Generates the message for the attendance of the remaining people
        attendance_message_body = []
        for i, user_id in enumerate(id_name_dict.keys()):
            if user_id in group_attendance_dict:
                attendance_message_body.append(''.join([str(i + 1), ') ', group_attendance_dict[user_id][0], ' - ',
                                                        ' / '.join(group_attendance_dict[user_id][1])]))
            else:
                attendance_message_body.append(''.join([str(i + 1), ') ', id_name_dict[user_id], ' - P']))
                # Also another problem: The first one, if only half a day got issue, then the other half a day won't
                # be updated.
                # Ok screw it, when you update attendance, update for all time periods of the day
                # Remember to add to the SQL table

        # cur.execute("""SELECT Name FROM users WHERE group_id = ?""", (current_group_id,))
        names = [data[0] for data in cur.fetchall()]
    attendance_message_body = [''.join([str(i + 1), ') ', names[i], ' - P']) for i in range(len(names))]

    message = '\n'.join(attendance_message_beginning + attendance_message_body)
    update_obj.message.reply_text(message)
    return ConversationHandler.END


# Changes attendance in the group you are in
def change_attendance(update_obj: Update, context: CallbackContext) -> int:
    current_group_id = settings.current_group_id
    update_obj.message.reply_text("Which users do you want to change the attendance of? To cancel select OK",
                                  reply_markup=get_group_members(current_group_id))
    return settings.FIRST
