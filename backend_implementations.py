"""Asks for user preferences; thereby implementing the backend for some state functions and entry functions"""

# from keyboards import *
from telegram import Update
from telegram.ext import CallbackContext
from string import ascii_uppercase, ascii_lowercase, digits
from collections import defaultdict
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
            (chat_id,)
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
            (group_id,)
        )
        all_ids = cur.fetchall()
    return all_ids


# Verifies that a user is in a group and has the privileges he needs to execute function
def verify_group_and_role(update_obj: Update, context: CallbackContext, role: str) -> bool:

    current_group_id = settings.current_group_id
    chat_id = update_obj.message.chat_id
    role_index_dict = {settings.ADMIN: 0, settings.MEMBER: 1, settings.OBSERVER: 2, "Other": 3}
    # Verify that the user is in a group first
    if current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return False

    # Check that the user has the right privileges
    if check_admin_privileges(chat_id, current_group_id) > role_index_dict[role]:
        reply_non_admin(update_obj, context, role)
        return False

    return True


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
        roles_dict = {settings.ADMIN: 0, settings.MEMBER: 1, settings.OBSERVER: 2}
        return roles_dict[roles[0][0]]


# Replies to user that they are not admin
def reply_non_admin(update_obj: Update, context: CallbackContext, role: str = settings.ADMIN) -> None:
    update_obj.message.reply_text("You are not qualified to perform this action!")
    update_obj.message.reply_text(f"You need to be a {role} to perform this action!")
    return None


# Checks if a date given is valid. When checking after or before, inclusive of the current day
def check_valid_datetime(date_to_check: str, date_compared: datetime.date = None, after_date: bool = True):
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

    # If there is a date to be compared to, check how the dates are related
    if date_compared is not None:

        # We compare if the final date is after or before the date that you want to compare
        if (final_date > date_compared) != after_date and final_date != date_compared:
            # print(final_date, date_compared, after_date, final_date > date_compared)
            # print("Condition not satisfied")
            return False

        # Next, we compare if the date is within 730 days (2 years)
        two_years = datetime.timedelta(days=730)

        # We already know that date_compared's relation (bigger or smaller) to final_date is correct
        # So we just need to check that it is within this range
        # Let's say final_date > date_compared. Want to ensure that it is within 2 years of date_compared
        # So date_compared + two_years > final_date
        # Let's say final_date < date_compared. Want to ensure that it is within 2 years.
        # So date_compared - two_years < final_date
        # So the final condition should be: date_compared - two_years <= final_date <= date_compared + two_years
        if not (date_compared - two_years) <= final_date <= (date_compared + two_years):
            # print(f"Date compared: {date_compared}, final_date: {final_date}")
            return False

    # If all conditions that have been checked are ok, then return the final_date to be used
    return final_date


# Gets group's attendance on a certain day
def get_day_group_attendance(update_obj: Update, context: CallbackContext, day: datetime.date) -> None:
    # Verifies that the user is qualified to call this first
    chat_id = update_obj.message.chat_id
    current_group_id = settings.current_group_id

    if not verify_group_and_role(update_obj, context, "Observer"):
        return None

    # Once user is verified, start getting attendance
    date_string = f"{day.day:02d}{day.month:02d}{day.year:04d}"  # day.year[2:]:04d
    attendance_message_beginning = [f"Attendance for {date_string}:"]
    if current_group_id is None:
        update_obj.message.reply_text("Enter a group first with /entergroup!")
        return None
    attendance_message_body, attendance_message_summary = get_group_attendance_backend(current_group_id, day)
    message = '\n'.join(attendance_message_beginning + ['\n'] + attendance_message_summary +
                        ['\n'] + attendance_message_body)
    update_obj.message.reply_text(message)


# Backend implementation to get user attendance
# Function used in get_day_group_attendance
def get_group_attendance_backend(group_id: int, date: datetime.date = None):
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

        # Gets a summary of the attendance statuses of the entire group
        attendance_status_dict = defaultdict(int)

        # Generates the message for the attendance of the remaining people
        attendance_message_body = []
        for i, user_id in enumerate(id_name_dict.keys()):
            if user_id in group_attendance_dict:

                # Check if both are the same, if same, then no need the slash, but say till when.
                if len(set(group_attendance_dict[user_id][1])) == 1:
                    # If present, then just use the regular P message
                    if group_attendance_dict[user_id][1][0] == 'P':
                        attendance_message_body.append(''.join([str(i + 1), ') ', id_name_dict[user_id], ' - P']))
                        attendance_status_dict['P'] += 1

                    # If not present, find the final date of the attendance
                    else:

                        # How this query works
                        # The query in brackets finds the number of attendance statuses that are different from
                        # statuses of the days before, for the user and group in question.
                        # Afterwards, to get the latest date, we select those with zero different statuses compared
                        # with the previous days (starting from day 0), and select the latest date.
                        cur.execute(
                            """
                            SELECT Date, AttendanceStatus, (
                                SELECT COUNT(*) FROM attendance A
                                WHERE A.AttendanceStatus <> AT.AttendanceStatus 
                                AND A.Date <= AT.Date
                                AND A.Date >= date('now', ?)
                                AND A.user_id = AT.user_id 
                                AND A.group_id = AT.group_id 
                            ) 
                            AS RunGroup 
                            FROM attendance AT
                            WHERE user_id = ? 
                            AND group_id = ?
                            AND Date >= date('now', ?) 
                            AND RunGroup = 0
                            ORDER BY Date DESC 
                            LIMIT 1
                            """,
                            (date_message, user_id, group_id, date_message)
                        )
                        date_parameters = cur.fetchall()
                        print(date_parameters)
                        final_date, attendance_status, rungroup = date_parameters[0]
                        # print(final_date, attendance_status)
                        final_date_representation = represent_date(final_date)
                        assert attendance_status == group_attendance_dict[user_id][1][0]
                        attendance_message_body.append(''.join([str(i + 1), ') ', id_name_dict[user_id], ' - ',
                                                                attendance_status, ' till ', final_date_representation]))
                        attendance_status_dict[attendance_status] += 1

                # If both statuses are different, then need the slash
                else:
                    attendance_message_body.append(''.join([str(i + 1), ') ', group_attendance_dict[user_id][0], ' - ',
                                                            ' / '.join(group_attendance_dict[user_id][1])]))
                    attendance_status_dict[group_attendance_dict[user_id][1][0]] += 1

                #
                #
                #
                # I think the final message that I need to give would be something along these lines:
                # First, I track between two entries, whether they are the same, in
                # an ORDERED TABLE by date, where date later than day compared.
                # If they are not the same, then break immediately. Else, continue
                # Must also check the condition that that date is the latest date. So if no, max rungroup?
                # See https://www.sqlteam.com/articles/detecting-runs-or-streaks-in-your-data
                # "https://stackoverflow.com/questions/44056555/find-longest-streak-in-sqlite"  # Identifying till when
            else:
                non_added_attendance_ids.append(user_id)
                attendance_message_body.append(''.join([str(i + 1), ') ', id_name_dict[user_id], ' - P']))
                attendance_status_dict['P'] += 1

        # Adding the attendances of all the present users
        # I think you may need to edit this to exclude weekends. Wait probably not, I should edit somewhere else
        users_to_add = [(group_id, user, i + 1, date_message) for user in non_added_attendance_ids
                        for i in range(num_daily_reports)]
        cur.executemany(
            """
            INSERT INTO attendance
            (group_id, user_id, TimePeriod, Date, AttendanceStatus)
            VALUES 
            (?, ?, ?, date('now', ?), 'P')""",
            users_to_add
        )

        print(attendance_status_dict)
        attendance_message_summary = [f"Strength: {sum(attendance_status_dict.values())}",
                                      f"Present: {attendance_status_dict['P']}\n"] + \
                                     [''.join([key, ": ", f"{attendance_status_dict[key]:02d}"])
                                         for key in attendance_status_dict if key != 'P']
        print(attendance_message_summary)

        # Save changes
        con.commit()

    # Returns the body of the attendance message for people who need it
    return attendance_message_body, attendance_message_summary


# Changes the attendance of users on a specific day
def change_group_attendance_backend(update_obj: Update, context: CallbackContext, day: datetime.date) -> None:
    # Gets the message that user sends, and cancels if necessary
    chat_id, message = get_admin_reply(update_obj, context)
    if message == "OK":
        update_obj.message.reply_text("Ok, cancelling job now")
        return None

    # Get the current group
    current_group = settings.current_group_id

    # First, we need to get the group's attendance. This helps to fill our database before we perform updates.
    get_group_attendance_backend(current_group, day)

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

            # This part has issues, need to debug
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
            # This implementation can potentially be improved
            # Add functionality to only insert if the days are not weekends; this has to be done in Python not SQLite
            attendances_to_update = [(current_group, user_id, j + 1, f'{i + num_days_difference} day',
                                      status[j], status[j]) for i in range(num_days) for j in range(len(status))
                                     if (day + datetime.timedelta(days=i)).weekday() <= 4]
            # print(attendances_to_update)

            # Inserts all the values into the table
            # This needs to be edited, it should be updating values, not inserting values
            cur.executemany(
                """
                INSERT INTO attendance
                (group_id, user_id, TimePeriod, Date, AttendanceStatus)
                VALUES (?, ?, ?, date('now', ?), ?)
                ON CONFLICT(group_id, user_id, TimePeriod, Date) 
                DO UPDATE SET AttendanceStatus = ?
                """,
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


# Gets user's attendance over the past month
# If don't have, will assume that get attendance of the past month
def get_single_user_attendance_backend(group_id, user_id, start_date: datetime.date, end_date: datetime.date):

    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """
            SELECT TimePeriod, Date, AttendanceStatus
              FROM attendance
             WHERE group_id = ? 
               AND user_id = ? 
               AND Date >= ? 
               AND Date <= ?
             ORDER BY Date, TimePeriod 
            """,
            (group_id, user_id, start_date, end_date)

        )
        # This will be a list of tuples: (TimePeriod, Date, AttendanceStatus)
        user_statuses = cur.fetchall()

        cur.execute(
            """
            SELECT NumDailyReports
              FROM groups
             WHERE id = ?
             """,
            (group_id, )
        )

        num_daily_reports = cur.fetchall()[0][0]

        # # Number of days of attendance gotten
        # num_days = (end_date - start_date).days

        # Data structure: Dictionary of lists. {Date: [Status1, Status2, ...]}
        user_statuses_revamped = {user_statuses[i][1]: [user_statuses[i + k][2] for k in range(num_daily_reports)]
                                  for i in range(0, len(user_statuses), num_daily_reports)}

        # Dictionary to check summary. Only add if TimePeriod = 1
        user_attendance_summary = defaultdict(int)
        for status in user_statuses:
            if status[0] == 1:
                user_attendance_summary[status[2]] += 1

        # Summary message provided
        attendance_message_body = ["Summary:", f"Present: {user_attendance_summary['P']}", ""]
        attendance_message_body += [f"{att_status}: {user_attendance_summary[att_status]}"
                                    for att_status in user_attendance_summary if att_status != 'P']
        attendance_message_body.append("")

        # Detailed attendance: Adding attendance for each day of the month
        for date in user_statuses_revamped:
            statuses = user_statuses_revamped[date]
            attendance_to_add = [represent_date(date), ": "]
            # If all statuses are the same
            if len(set(statuses)) == 1:
                attendance_to_add.append(user_statuses_revamped[date][0])
            else:
                attendance_to_add.append(' / '.join(user_statuses_revamped[date]))

            attendance_message_body.append(''.join(attendance_to_add))
        #
        # attendance_message_body += [''.join([represent_date(date), ": ", ' / '.join(user_statuses_revamped[date])])
        #                             for date in user_statuses_revamped]

        return attendance_message_body


# Represents date obtained from a SQLite server
def represent_date(date_str: str) -> str:
    year, month, day = date_str.split('-')
    year = year[2:]
    new_date = ''.join([day, month, year])
    return new_date


# Gets the users that the admin wants
def get_intended_users(user_string: str, group_id: int=None):

    # We first split the user_string, but must test if the input is valid
    try:
        users = list(map(int, user_string.split()))
    except ValueError:
        return False

    group_size = float("inf")

    # Next, if there is a group_id provided, we check that all inputs provided are less than the group size
    if group_id is not None:
        # Next, we check that all users are of a valid input, that is their indices exist, and are smaller than group size.
        with sqlite3.connect('attendance.db') as con:
            cur = con.cursor()
            cur.execute(
                """SELECT COUNT(*) FROM users WHERE group_id = ?""", (group_id, )
            )
            group_size = cur.fetchall()[0][0]

    # We check that all the users are valid with this condition: If valid, return users, else, return False.
    return users if min([(1 <= user <= group_size) and type(user) == int for user in users]) else False


# Converts user rank into user_id
def convert_rank_to_id(group_id, user_rank) -> int:
    with sqlite3.connect('attendance.db') as con:
        cur = con.cursor()
        cur.execute(
            """SELECT id FROM users WHERE group_id = ? AND rank = ?""", (group_id, user_rank)
        )
        result = cur.fetchall()[0][0]
        return result if result else 0
