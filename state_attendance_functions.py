"""Implementation of functions needed for attendance functions beyond the first one
Responds to messages and stores the messages given """
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
import settings
import datetime
from backend_implementations import get_admin_reply, check_valid_datetime, \
    get_day_group_attendance, change_group_attendance_backend, get_intended_users, get_single_user_attendance_backend, \
    convert_rank_to_id, get_group_size, get_child_groups
from entry_attendance_functions import _change_attendance_send_messages


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
    while today.weekday() > 4:
        today += datetime.timedelta(days=1)
    change_group_attendance_backend(update_obj, context, today)
    return ConversationHandler.END


# Changes tomorrow's attendance
def change_tomorrow_attendance_follow_up(update_obj: Update, context: CallbackContext) -> int:
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    while tomorrow.weekday() > 4:
        tomorrow += datetime.timedelta(days=1)
    change_group_attendance_backend(update_obj, context, tomorrow)
    return ConversationHandler.END


# Gets the day that the user wants for changing attendance. For change_any_day_attendance
def change_any_day_attendance_get_day(update_obj: Update, context: CallbackContext) -> int:
    chat_id, day = get_admin_reply(update_obj, context)
    day_datetime = check_valid_datetime(day)

    # Check that date is entered in a valid format
    if not day_datetime:
        update_obj.message.reply_text("Date entered in an invalid format")
        return ConversationHandler.END

    # Check that it is a weekday
    if day_datetime.weekday() > 4:
        update_obj.message.reply_text("Date is a weekend!")
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


# Follow-up function of get_specific_day_group_attendance
def get_specific_day_group_attendance_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, date = get_admin_reply(update_obj, context)
    current_group = settings.current_group_id[chat_id]
    # Gets the date in the form of a datetime object
    day_to_check = check_valid_datetime(date)
    if not day_to_check:
        update_obj.message.reply_text("Date entered in an invalid format")
        return ConversationHandler.END

    # Check that it is a weekday
    if day_to_check.weekday() > 4:
        update_obj.message.reply_text("Date is a weekend!")
        return ConversationHandler.END

    get_day_group_attendance(context, day_to_check, current_group, update_obj=update_obj)
    return ConversationHandler.END


# Gets the attendance of users over the past 31 days
def get_user_attendance_month_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, user_text = get_admin_reply(update_obj, context)

    # Gets the end and start dates
    end_date = datetime.date.today()
    start_date = datetime.date.today() - datetime.timedelta(days=31)

    # Sends all the attendance messages, after verification
    _get_user_attendance_process(update_obj, context, user_text, start_date, end_date)
    return ConversationHandler.END


# Gets the attendance of users over an arbitrary period of time
def get_user_attendance_arbitrary_follow_up(update_obj: Update, context: CallbackContext) -> int:
    chat_id, admin_instructions = get_admin_reply(update_obj, context)
    admin_instructions = [instruction for instruction in admin_instructions.split('\n') if instruction]
    try:
        user_text, start_date, end_date = admin_instructions
    except ValueError:
        update_obj.message.reply_text("Users entered in an incorrect format! Refer to above to see how to "
                                      "enter users and dates!")
        return ConversationHandler.END

    # Gets the dates that the admin wants, and verifies that they are valid first.
    today = datetime.date.today()
    end_date = check_valid_datetime(date_to_check=end_date, date_compared=today, after_date=False)  # Check this condition
    if not end_date:
        update_obj.message.reply_text("End date entered incorrectly! Refer to above to see how to enter dates! "
                                      "The end date must be today or before. ")
        return ConversationHandler.END

    start_date = check_valid_datetime(date_to_check=start_date, date_compared=end_date, after_date=False)
    if not start_date:
        update_obj.message.reply_text("Start date entered incorrectly! Refer to above to see how to enter dates! "
                                      "The start date must be before the end date. ")
        return ConversationHandler.END

    # Sends all the attendance messages, after verification
    _get_user_attendance_process(update_obj, context, user_text, start_date, end_date)
    return ConversationHandler.END


# Gets the attendance of all users over the past 31 days
def get_all_users_attendance_month_follow_up(update_obj: Update, context: CallbackContext) -> int:

    # Get the group_id
    chat_id, get_subgroups = get_admin_reply(update_obj, context)
    group_id = settings.current_group_id[chat_id]

    get_subgroups = get_subgroups.strip().lower()

    # Get the start and end dates
    end_date = datetime.date.today()
    start_date = datetime.date.today() - datetime.timedelta(days=31)

    # Gets the attendance for the groups you need, depending on get_subgroups recursive or not
    _get_all_users_attendance_process(update_obj, context, group_id, start_date, end_date, get_subgroups)
    return ConversationHandler.END


# Gets the attendance of all users over an arbitrary period of time
def get_all_users_attendance_arbitrary_follow_up(update_obj: Update, context: CallbackContext) -> int:

    # First, we get user's reply
    chat_id, admin_instructions = get_admin_reply(update_obj, context)
    admin_instructions = [instruction for instruction in admin_instructions.split('\n') if instruction]
    try:
        get_subgroups, start_date, end_date = admin_instructions
    except ValueError:
        update_obj.message.reply_text("Users entered in an incorrect format! Refer to above to see how to "
                                      "enter users and dates!")
        return ConversationHandler.END

    get_subgroups = get_subgroups.strip().lower()

    # Get current_group_id
    group_id = settings.current_group_id[chat_id]

    # Gets the dates that the admin wants, and verifies that they are valid first.
    today = datetime.date.today()
    end_date = check_valid_datetime(date_to_check=end_date, date_compared=today, after_date=False)
    if not end_date:
        update_obj.message.reply_text("End date entered incorrectly! Refer to above to see how to enter dates! "
                                      "The end date must be today or before. ")
        return ConversationHandler.END

    start_date = check_valid_datetime(date_to_check=start_date, date_compared=end_date, after_date=False)
    if not start_date:
        update_obj.message.reply_text("Start date entered incorrectly! Refer to above to see how to enter dates! "
                                      "The start date must be before the end date. ")
        return ConversationHandler.END

    # Gets the attendance for the groups you need
    _get_all_users_attendance_process(update_obj, context, group_id, start_date, end_date, get_subgroups)
    return ConversationHandler.END


# The backend for getting all users' attendance, recursively
def _get_all_users_attendance_process(update_obj: Update, context: CallbackContext, group_id: int,
                                      start_date: datetime.date, end_date: datetime.date, get_subgroups: str) -> None:
    group_size = get_group_size(group_id)
    # Generates the user text to be used
    user_text = ' '.join([str(i) for i in range(1, group_size + 1)])

    # Sends all the attendance messages, after verification
    _get_user_attendance_process(update_obj, context, user_text, start_date, end_date, current_group=group_id)

    # If recursive, do recursively
    if get_subgroups == 'y':
        child_group_ids = get_child_groups(group_id)
        for child_id in child_group_ids:
            _get_all_users_attendance_process(update_obj, context, child_id, start_date, end_date, get_subgroups)


# The backend process for getting attendance. Implemented by both get_user_attendance functions.
def _get_user_attendance_process(update_obj: Update, context: CallbackContext, user_text: str,
                                 start_date: datetime.date, end_date: datetime.date,
                                 current_group=None) -> bool:
    chat_id = update_obj.message.chat_id
    current_group = settings.current_group_id[chat_id] if current_group is None else current_group
    users = get_intended_users(user_text, current_group)
    if not users:
        update_obj.message.reply_text("Users not entered correctly!")
        return False

    # print(users)

    # Gets an attendance message for each user
    for user in users:
        # Gets the user_id from the rank
        user_id = convert_rank_to_id(current_group, user)
        attendance_message_body = get_single_user_attendance_backend(current_group, user_id, start_date, end_date)
        # print(attendance_message_body)
        update_obj.message.reply_text('\n'.join(attendance_message_body))

    # Update that everything is done
    update_obj.message.reply_text("All users' attendance have been retrieved")
    return True
