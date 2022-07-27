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
    if current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return ConversationHandler.END
    # Gets all users
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()

        # Gets the attendance of the non-present people for today
        cur.execute(
            """
            SELECT users.id, users.Name, TimePeriod, AttendanceStatus 
              FROM attendance
              JOIN users 
               ON users.id = attendance.user_id 
             WHERE Date = date('now')
               AND attendance.user_id 
                IN (
                    SELECT id FROM users WHERE group_id = ?
            )
            """,
            (current_group_id, )
        )
        group_attendance = cur.fetchall()
        print(group_attendance)
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
        print(all_members)
        id_name_dict = {member[0]: member[1] for member in all_members}

        # Generates the message for the attendance of the remaining people
        attendance_message_body = []
        for i, user_id in enumerate(id_name_dict.keys()):
            if user_id in group_attendance_dict:
                # Check if both are the same, if same, then no need the slash, but say till when.
                attendance_message_body.append(''.join([str(i + 1), ') ', group_attendance_dict[user_id][0], ' - ',
                                                        ' / '.join(group_attendance_dict[user_id][1])]))
                "https://stackoverflow.com/questions/44056555/find-longest-streak-in-sqlite"  # Identifying till when
            else:
                attendance_message_body.append(''.join([str(i + 1), ') ', id_name_dict[user_id], ' - P']))
                # Also another problem: The first one, if only half a day got issue, then the other half a day won't
                # be updated.
                # Ok screw it, when you update attendance, update for all time periods of the day
                # Remember to add to the SQL table

        # cur.execute("""SELECT Name FROM users WHERE group_id = ?""", (current_group_id,))
    #     names = [data[0] for data in cur.fetchall()]
    # attendance_message_body = [''.join([str(i + 1), ') ', names[i], ' - P']) for i in range(len(names))]

    message = '\n'.join(attendance_message_beginning + attendance_message_body)
    update_obj.message.reply_text(message)
    return ConversationHandler.END


# # Changes attendance in the group you are in
# def change_attendance(update_obj: Update, context: CallbackContext) -> int:
#     current_group_id = settings.current_group_id
#     update_obj.message.reply_text("Which users do you want to change the attendance of? To cancel select OK",
#                                   reply_markup=get_group_members(current_group_id))
#     return settings.FIRST


# Changes attendance in the group you are in
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
