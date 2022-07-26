"""Implementation of functions needed for attendance functions beyond the first one
Responds to messages and stores the messages given """

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import sqlite3
from state_variables import *
import settings
import datetime
from backend_implementations import get_group_members, get_admin_reply, check_admin_privileges


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
                SELECT user_id 
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

        # Next, we check if it is the toxic one (the one with attendance over a long time)
        if 'till' in entry[1]:
            status, final_date = entry[1].split('till').strip()
            # If the final date is invalid, skip the entry
            if len(final_date) != 6:
                update_obj.message.reply_text(f"Regarding user {entry[0]}: Date entered in an invalid format")
                continue
            day, month, year = int(final_date[:2]), int(final_date[2:4]), int('20' + final_date[4:])
            try:
                final_date = datetime.date(year=year, month=month, day=day)
            except ValueError:
                update_obj.message.reply_text(f"Regarding user {entry[0]}: Date must be valid")
                continue
            # If we manage to reach here, that means that we have already passed all the tests.
            today = datetime.date.today()
            # If the date is larger than today, then continue
            if today > final_date:
                update_obj.message.reply_text(f"Regarding user {entry[0]}: Final date is before today's date")
                continue
            # If the final date is more than 2 years in the future, then continue
            elif today + datetime.timedelta(days=730) < final_date:
                update_obj.message.reply_text(f"Regarding user {entry[0]}: Final date must be less than 2 years in "
                                              f"future")
                continue

            # Get the number of days
            num_days = (final_date - today).days + 1  # Need to include today also
            data_table = [(current_group, user_id, j + 1, f"date('now', '+{i} day')", entry[1][i])
                          for i in range(num_days) for j in range(len(entry[1]))]

            # Adding all the attendance changes into the attendance table
            # See if you can merge this with the bottom one, so that you don't duplicate code. Perhaps what changes
            # or not is data_table
            with sqlite3.connect('attendance.db') as con:
                cur = con.cursor()
                cur.executemany(
                    """
                    INSERT INTO attendance
                    (group_id, user_id, TimePeriod, Date, AttendanceStatus)
                    VALUES (?, ?, ?, ?, ?)""",
                    data_table
                )

                # Save changes
                con.commit()

            # Update user about success
            update_obj.message.reply_text(f"User {entry[0]}'s attendance updated.")
            continue

        # Else, if the attendance is listed without '/'
        elif '/' not in entry[1]:
            entry[1] = ' / '.join([entry[1], entry[1]])

        # Update the attendance of the user
        with sqlite3.connect('attendance.db') as con:
            cur = con.cursor()
            entry[1] = entry[1].split('/').strip()

            # You need to update the date to make it correct. It can be either today or tomorrow.
            attendances_to_update = [(current_group, user_id, i + 1, "date('now')", entry[1][i])
                                     for i in range(len(entry[1]))]

            # Inserts all the values into the table
            cur.executemany(
                """
                INSERT INTO attendance
                (group_id, user_id, TimePeriod, Date, AttendanceStatus)
                VALUES (?, ?, ?, ?, ?)""",
                attendances_to_update
            )

            # Save changes
            con.commit()

        # Update user about success
        update_obj.message.reply_text(f"User {entry[0]}'s attendance updated.")


# # Gets the user's attendance, and updates it
# # Should there be any typos, the bot will just not work. Ask user to update again
# def update_users_attendance(update_obj: Update, context: CallbackContext) -> int:
#     # Scenario 2: Half-day LL
#     if '/' in
#         "P/OS/MHC"
#
#     return settings.FIRST


# # Verify which format attendance is in
# def


possible_attendance_formats = """
LL
P / LL 
LL till 260722
"""

# Stuff to be checked about date
# If the date is more than 2 years from today's date, reject
# If the date is before today's date, reject
# If the date has an invalid month or day or year, reject (use try, except ValueError for datetime?)
