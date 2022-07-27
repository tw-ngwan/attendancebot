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
        update_obj.message.reply_text("Date entered is of an invalid format! ")
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


def get_submitted_users_attendance(update_obj: Update, context: CallbackContext) -> int:
    chat_id, attendance = get_admin_reply(update_obj, context)
    # First, we split according to \n to get a list
    attendance_parse = attendance.split('\n')
    # Next, we split according to ':' and get rid of blank values, and potential error values
    attendance_parse_two = [attendance.split(':') for attendance in attendance_parse if attendance.strip()
                            and len(attendance.split(':')) == 2]

    # Get the current group
    current_group = settings.current_group_id

    # Now, we check the second entry to see how the attendance is keyed in
    # For all the continues, consider whether we want to send a text to inform the user
    for entry in attendance_parse_two:

        # First, we check if the user exists
        with sqlite3.connect('attendance.db') as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT id 
                  FROM users 
                 WHERE group_id = ? 
                   AND rank = ?""",
                (current_group, int(entry[0]))
            )
            user_id = cur.fetchall()
            if not user_id:
                update_obj.message.reply_text(f"Regarding user {entry[0]}: User does not exist. ")
                continue
            user_id = user_id[0][0]

            con.commit()

        # We set the number of days first (for the non-long attendance)
        num_days = 1

        # Next, we check if it is the long attendance
        # May want to add a few print statements for debug
        if 'till' in entry[1]:
            status, final_date = entry[1].split('till')
            status = status.strip()
            final_date = final_date.strip()

            # We get today's date to compare with
            today = datetime.date.today()
            final_date = check_valid_datetime(date_to_check=final_date, date_compared=today, after_date=True)
            if not final_date:
                update_obj.message.reply_text(f"Regarding user {entry[0]}: Date entered in an invalid format. "
                                              f"Date must also be after today's date, and less than 2 years in future.")
                continue

            # Get the number of days
            num_days = (final_date - today).days + 1  # Need to include today also

            # This is so that it can be split later (for eg: LL --> LL / LL)
            status = ' / '.join([status, status])

        # Else, if the attendance is listed without '/'
        elif '/' not in entry[1]:
            status = ' / '.join([entry[1], entry[1]])
        else:
            status = entry[1]

        # This updates the user's attendance for all
        # Update the attendance of the user
        with sqlite3.connect('attendance.db') as con:
            cur = con.cursor()
            # Gets the values of all
            status = [value.strip() for value in status.split('/')]

            # You need to update the date to make it correct. It can be either today or tomorrow.
            # For now, implementation is today. What this does is create one entry for each day, for each
            # time period. All of them then get updated at once using executemany.
            attendances_to_update = [(current_group, user_id, j + 1, f'+{i} day', status[j])
                                     for i in range(num_days) for j in range(len(status))]
            print(attendances_to_update)

            # Inserts all the values into the table
            cur.executemany(
                """
                INSERT INTO attendance
                (group_id, user_id, TimePeriod, Date, AttendanceStatus)
                VALUES (?, ?, ?, date('now', ?), ?)""",
                attendances_to_update
            )

            # Save changes
            con.commit()

        # Update user about success
        update_obj.message.reply_text(f"User {entry[0]}'s attendance updated.")

    update_obj.message.reply_text("All users' attendance updated.")
    return ConversationHandler.END

# Stuff to be checked about date
# If the date is more than 2 years from today's date, reject
# If the date is before today's date, reject
# If the date has an invalid month or day or year, reject (use try, except ValueError for datetime?)


# Follow up function of get_specific_day_group_attendance
def get_specific_day_group_attendance_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, date = get_admin_reply(update_obj, context)
    # Gets the date in the form of a datetime object
    day_to_check = check_valid_datetime(date)
    if not day_to_check:
        update_obj.message.reply_text("Date entered in an invalid format")
        return ConversationHandler.END

    get_day_group_attendance(update_obj, context, day_to_check)
    return ConversationHandler.END
