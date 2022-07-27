"""Asks for user preferences; thereby implementing the backend for some state functions and entry functions"""

# from keyboards import *
from telegram import Update
from telegram.ext import CallbackContext
from string import ascii_uppercase, ascii_lowercase, digits
import random
import sqlite3
import shelve
import datetime
import settings


# Generates a random password
def generate_random_password(length=12, iterations=1) -> list[str]:
    """Generates a random password"""
    return [''.join([random.choice(''.join([ascii_uppercase, ascii_lowercase, digits])) for _ in range(length)])
            for _ in range(iterations)]


# Generates a random, unique group code
def generate_random_group_code() -> str:
    """Generates a random, unique group code"""
    # How this works:
    # I have a database of 100,000 group codes stored in a database (shelve), along with the current_group_number
    # Whenever a new group is created, the next group code in line will be used, to ensure that it remains unique.
    # Thus, this allows for O(1) lookup and generation of the group code
    with shelve.open('groups.db') as s:
        group_code = s['group_codes'][s['current_group']]
        s['current_group'] += 1
    return group_code


# Gets the user's reply
def get_admin_reply(update_obj: Update, context: CallbackContext):
    """Gets the reply of the user"""
    chat_id = update_obj.message.chat_id
    message = update_obj.message.text.strip()
    return chat_id, message


# Gets the groups that an admin is in
def get_admin_groups(chat_id):
    """Gets the groups that an admin is in.
    Returns a list of tuples: (group_name, group_id, role)"""
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT groups.Name, admins.group_id, admins.role
              FROM admins
              JOIN groups 
                ON admins.group_id = groups.id 
             WHERE admins.chat_id = ?
            """,
            (chat_id, )
        )
        user_groups = cur.fetchall()

        # Save changes
        con.commit()

    # user_groups is a list of tuples, where each tuple is of the form (Group Name, Group ID, Role)
    return user_groups


# Gets all the group members of a group
def get_group_members(group_id):
    """Returns a list of tuples: (group_id, group_name)"""
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT id, Name FROM users
             WHERE group_id = ?
            """,
            (group_id, )
        )
        all_ids = cur.fetchall()
    return all_ids


# Checks that a user is an admin
# If admin, returns 0. If member, returns 1. If observer, returns 2. If none, returns 3
def check_admin_privileges(chat_id, group_id):
    """Checks if a user is an admin, member, observer, or None.
    If admin, returns 0. If member, returns 1. If observer, returns 2. If none, returns 3"""
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT role 
              FROM admins 
             WHERE chat_id = ? 
               AND group_id = ?
            """,
            (chat_id, group_id)
        )
        roles = cur.fetchall()
        if not roles:
            return 3
        roles_dict = {'Admin': 0, 'Member': 1, 'Observer': 2}
        return roles_dict[roles[0][0]]


# Replies to user that they are not admin
def reply_non_admin(update_obj: Update, context: CallbackContext, role: str="Admin") -> None:
    update_obj.message.reply_text("You are not qualified to perform this action!")
    update_obj.message.reply_text(f"You need to be a {role} to perform this action!")
    return None


# Checks if a date given is valid
def check_valid_datetime(date_to_check: str, date_compared: datetime.date=None, after_date: bool=True):
    """Checks if a date given is valid, and if compared with another date, whether it is also after or before the date
    (User specified)"""

    # First, check that it is in the form 'DDMMYY'
    date_to_check = date_to_check.strip()
    if len(date_to_check) != 6:
        return False

    # Split the date up into day, month, and year
    # If this is not possible, this means that there is some issue with the date provided
    try:
        day, month, year = int(date_to_check[:2]), int(date_to_check[2:4]), int('20' + date_to_check[4:])
    except ValueError or IndexError:
        return False

    # We use a try-except statement to try and get a Date object from the day, month, and year.
    # If it works, then there is no issue. Else, return False; it is not a date
    try:
        final_date = datetime.date(year=year, month=month, day=day)
    except ValueError:
        return False

    # If there is a date to be compared to,
    if date_compared is not None:

        # We compare if the final date is after or before the date that you want to compare
        if final_date > date_compared != after_date and final_date != date_compared:
            return False

        # Next, we compare if the date is within 730 days (2 years)
        two_years = datetime.timedelta(days=730)

        # We already know that date_compared's relation (bigger or smaller) to final_date is correct
        # So we just need to check that it is within this range
        if not final_date - two_years <= date_compared <= final_date + two_years:
            return False

    # If all conditions that have been checked are ok, then return the final_date to be used
    return final_date


# Gets group's attendance on a certain day
def get_day_group_attendance(update_obj: Update, context: CallbackContext, day: datetime.date) -> None:

    # Verifies that the user is qualified to call this first
    chat_id = update_obj.message.chat_id
    current_group_id = settings.current_group_id
    if check_admin_privileges(chat_id, current_group_id) >= 3:
        reply_non_admin(update_obj, context, "Observer")
        return None

    # Once user is verified, start getting attendance
    date_string = f"{day.day:02d}{day.month:02d}{day.year:04d}"
    attendance_message_beginning = [f"Attendance for {date_string}:"]
    if current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return None
    attendance_message_body = get_group_attendance_backend(group_id=current_group_id, date=day)
    message = '\n'.join(attendance_message_beginning + attendance_message_body)
    update_obj.message.reply_text(message)


# Backend implementation to get user attendance
# Function used in get_day_group_attendance
def get_group_attendance_backend(group_id: int, date: datetime.date=None):
    """Backend implementation to get the attendance of the user. Key in date as datetime.date object
    (The datetime.date object can be obtained using check_valid_datetime)"""

    if date is None:
        date = datetime.date.today()

    # Get the number of days to add; this is so that we can get the correct date for SQLite
    today = datetime.date.today()
    num_days_to_add = (date - today).days

    # This is the date_message that will be passed to sqlite when checking which date will be used
    date_message = f"{num_days_to_add} day"

    # Get the attendance of the non-present people for the day
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()

        # Gets the attendance of the non-present people for the day
        cur.execute(
            """
            SELECT users.id, users.Name, TimePeriod, AttendanceStatus 
              FROM attendance
              JOIN users 
               ON users.id = attendance.user_id 
             WHERE Date = date('now', ?)
               AND attendance.user_id 
                IN (
                    SELECT id FROM users WHERE group_id = ?
            )
            """,
            (date_message, group_id)
        )

        # group_attendance is a list of tuples; each tuple comprises (user_id, user_name, time_period, status)
        group_attendance = cur.fetchall()
        # print(group_attendance)
        # Gets the number of time periods to be updated per day
        cur.execute("""SELECT NumDailyReports FROM groups WHERE id = ?""", (group_id,))
        num_daily_reports = cur.fetchall()[0][0]

        # How this works:
        # I create a dict, that stores values like this: {id: [Name, [Attendance[0], Attendance[1], ...]]}
        group_attendance_dict = {}
        for member in group_attendance:
            if member[0] not in group_attendance_dict:
                group_attendance_dict[member[0]] = [member[1], ['P'] * num_daily_reports]
            group_attendance_dict[member[0]][1][member[2] - 1] = member[3]

        # Gets the attendance of the remaining people
        all_members = get_group_members(group_id)
        print(all_members)
        id_name_dict = {member[0]: member[1] for member in all_members}

        # Create a list to see the ids of people whose attendance are not added yet
        non_added_attendance_ids = []

        # Generates the message for the attendance of the remaining people
        attendance_message_body = []
        for i, user_id in enumerate(id_name_dict.keys()):
            if user_id in group_attendance_dict:
                # Check if both are the same, if same, then no need the slash, but say till when.
                attendance_message_body.append(''.join([str(i + 1), ') ', group_attendance_dict[user_id][0], ' - ',
                                                        ' / '.join(group_attendance_dict[user_id][1])]))
                "https://stackoverflow.com/questions/44056555/find-longest-streak-in-sqlite"  # Identifying till when
            else:
                non_added_attendance_ids.append(user_id)
                attendance_message_body.append(''.join([str(i + 1), ') ', id_name_dict[user_id], ' - P']))
                # Also another problem: The first one, if only half a day got issue, then the other half a day won't
                # be updated.
                # Ok screw it, when you update attendance, update for all time periods of the day
                # Remember to add to the SQL table

        # Adding the attendances of all the present users
        users_to_add = [(group_id, user, i + 1, date_message) for user in non_added_attendance_ids
                        for i in range(num_daily_reports)]
        cur.executemany(
            """
            INSERT INTO attendance
            (group_id, user_id, TimePeriod, Date, AttendanceStatus)
            VALUES 
            (?, ?, ?, date('now', ?), P)""",
            users_to_add
        )

        # Save changes
        con.commit()

    # Returns the body of the attendance message for people who need it
    return attendance_message_body


# Changes the attendance of users on a specific day
def change_group_attendance_backend(update_obj: Update, context: CallbackContext, day: datetime.date) -> None:

    # Gets the message that user sends, and cancels if necessary
    chat_id, message = get_admin_reply(update_obj, context)
    if message == "OK":
        update_obj.message.reply_text("Ok, cancelling job now")
        return None

    # Get the current group
    current_group = settings.current_group_id

    # We compare how far away the day is from today first
    today = datetime.date.today()
    num_days_difference = (day - today).days

    # Get the user's instructions in form of list of lists
    parsed_attendance_message = parse_user_change_instructions(message)

    # Now, we check how the attendance is keyed in, and whether the user to change attendance of exists
    for entry in parsed_attendance_message:

        # First, we check if the user exists
        user_id = check_user_rank_exists(group_id=current_group, user_rank=int(entry[0]))
        if not user_id:
            update_obj.message.reply_text(f"Regarding user {entry[0]}: User does not exist. ")
            continue

        # We set the number of days first. This will be edited in long attendance (and ignored for others so
        # value remains)
        num_days = 1

        # Next, we check what format the attendance is entered in.
        # First, we check if this is the long attendance.
        if 'till' in entry[1]:
            status, final_date = entry[1].split('till')
            status = status.strip()
            final_date = final_date.strip()

            final_date = check_valid_datetime(date_to_check=final_date, date_compared=day, after_date=True)
            if not final_date:
                update_obj.message.reply_text(f"Regarding user {entry[0]}: Date entered in an invalid format. "
                                              f"Date must also be after the day's date, "
                                              f"and less than 2 years in future.")
                continue

            # Get the number of days
            num_days = (final_date - day).days + 1  # Need to include the actual day also

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
            attendances_to_update = [(status[j], current_group, user_id, j + 1, f'{i + num_days_difference} day')
                                     for i in range(num_days) for j in range(len(status))]
            # print(attendances_to_update)

            # Inserts all the values into the table
            # This needs to be edited, it should be updating values, not inserting values
            cur.executemany(
                """
                UPDATE attendance
                SET AttendanceStatus = ? 
                WHERE group_id = ? AND user_id = ? AND TimePeriod = ? AND Date = date('now', ?)""",
                attendances_to_update
            )

            # Save changes
            con.commit()

        # Update user about success
        update_obj.message.reply_text(f"User {entry[0]}'s attendance updated.")

    update_obj.message.reply_text("All users' attendance updated.")


# Splits the user's change group attendance message
# Function used in change_group_attendance_backend
def parse_user_change_instructions(message: str):
    # First, we split according to '\n' to get the lines of the message
    message_lines = message.split('\n')
    # Next, we split according to ':' and get rid of blank, or error values
    parsed_attendance_message = [attendance.split(':') for attendance in message_lines if attendance.strip()
                                 and len(attendance.split(':')) == 2]
    return parsed_attendance_message


# Checks whether a user of a certain rank (integer) in a group exists
# Function used in change_group_attendance_backend
def check_user_rank_exists(group_id: int, user_rank: int):
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT id 
              FROM users 
             WHERE group_id = ? 
               AND rank = ?""",
            (group_id, user_rank)
        )
        user_id = cur.fetchall()
        if not user_id:
            return False
        user_id = user_id[0][0]

    return user_id
